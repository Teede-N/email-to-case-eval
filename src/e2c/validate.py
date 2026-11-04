"""Validation « humain sur la boucle » des dossiers produits par l'agent.

Deux niveaux de contrôle, comme en production :
  1. Cohérence avec les SYSTÈMES SOURCES (data/reference.sqlite) : le client existe-t-il ? la commande appartient-elle
     à ce client ? la facture existe-t-elle et son montant correspond-il ? → signaux disponibles SANS vérité terrain,
     utilisables en production pour router un dossier vers un contrôle humain.
  2. Comparaison avec la VÉRITÉ TERRAIN (data/ground_truth.jsonl) : exactitude par champ, utilisée pour le banc
     d'évaluation et les KPI.

Sortie : une ligne de validation par e-mail (data/validations.jsonl), avec le verdict et les champs en écart.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from .extract import CHAMPS, Dossier

RACINE = Path(__file__).resolve().parents[2]
DATA = RACINE / "data"


@dataclass
class Validation:
    email_id: str
    pays: str
    langue: str
    semaine: int
    cas_limite: str | None
    type_attendu: str
    type_predit: str
    a_creer_attendu: bool
    a_creer_predit: bool
    champs_ok: dict = field(default_factory=dict)      # champ -> bool (None si non attendu et non prédit)
    ecarts: list[str] = field(default_factory=list)    # "champ: prédit≠attendu"
    coherence_source: list[str] = field(default_factory=list)  # anomalies détectées via la base de référence
    verdict: str = ""        # auto_ok | corrige | escalade | faux_dossier | dossier_manque | ignore_ok
    confiance: float = 0.0
    echec_trace: str | None = None
    duree_ms: float = 0.0


class SourceSystems:
    """Accès en lecture aux systèmes de référence (CRM, gestion des commandes de transport, facturation)."""

    def __init__(self, chemin: Path = DATA / "reference.sqlite"):
        self.con = sqlite3.connect(chemin, check_same_thread=False)

    def client_existe(self, cid: str | None) -> bool:
        return bool(cid) and self.con.execute("SELECT 1 FROM clients WHERE customer_id=?", (cid,)).fetchone() is not None

    def commande_du_client(self, cmd: str | None, cid: str | None) -> bool | None:
        if not cmd:
            return None
        row = self.con.execute("SELECT customer_id, statut FROM commandes WHERE order_no=?", (cmd,)).fetchone()
        if row is None:
            return False
        return (cid is None) or row[0] == cid

    def commande_active(self, cmd: str | None) -> bool | None:
        if not cmd:
            return None
        row = self.con.execute("SELECT statut FROM commandes WHERE order_no=?", (cmd,)).fetchone()
        return None if row is None else row[0] == "en_cours"

    def facture(self, inv: str | None) -> dict | None:
        if not inv:
            return None
        row = self.con.execute("SELECT customer_id, montant, devise FROM factures WHERE invoice_no=?", (inv,)).fetchone()
        return None if row is None else {"customer_id": row[0], "montant": row[1], "devise": row[2]}

    def client_par_commande(self, cmd: str | None) -> str | None:
        if not cmd:
            return None
        row = self.con.execute("SELECT customer_id FROM commandes WHERE order_no=?", (cmd,)).fetchone()
        return row[0] if row else None


def coherence(t: Dossier, src: SourceSystems) -> list[str]:
    """Anomalies détectables en production, sans vérité terrain."""
    a = []
    if t.customer_id and not src.client_existe(t.customer_id):
        a.append("client_inconnu")
    if src.commande_du_client(t.order_no, t.customer_id) is False:
        a.append("commande_inconnue_ou_autre_client")
    if src.commande_active(t.order_no) is False:
        a.append("commande_annulee")
    f = src.facture(t.invoice_no)
    if t.invoice_no and f is None:
        a.append("facture_inconnue")
    if f and t.montant is not None and t.type_demande == "question_facture" and abs(f["montant"] - t.montant) > 0.01:
        a.append("montant_different_de_la_facturation")
    if t.a_creer and not any([t.customer_id, t.order_no, t.invoice_no]):
        a.append("aucun_identifiant")
    return a


def egal(a, b) -> bool:
    if a is None and b is None:
        return True
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 0.01
    return a == b


def valider(t: Dossier, email: dict, verite: dict, src: SourceSystems) -> Validation:
    v = Validation(email_id=t.email_id, pays=email["pays"], langue=email["langue"], semaine=email["semaine"],
                   cas_limite=email.get("cas_limite"), type_attendu=verite["type_demande"], type_predit=t.type_demande,
                   a_creer_attendu=verite["a_creer"], a_creer_predit=t.a_creer, confiance=t.confiance,
                   echec_trace=t.trace.echec, duree_ms=t.trace.duree_ms)
    for c in CHAMPS:
        if c == "type_demande":
            continue
        att, pred = verite.get(c), getattr(t, c)
        if att is None and pred is None:
            v.champs_ok[c] = None
        else:
            ok = egal(att, pred)
            v.champs_ok[c] = ok
            if not ok:
                v.ecarts.append(f"{c}: {pred!r} ≠ {att!r}")
    v.champs_ok["type_demande"] = t.type_demande == verite["type_demande"]
    if not v.champs_ok["type_demande"]:
        v.ecarts.insert(0, f"type_demande: {t.type_demande!r} ≠ {verite['type_demande']!r}")
    v.coherence_source = coherence(t, src)

    if not verite["a_creer"]:
        v.verdict = "ignore_ok" if not t.a_creer else "faux_dossier"
    elif not t.a_creer:
        v.verdict = "dossier_manque"
    elif t.trace.echec or v.coherence_source:
        v.verdict = "escalade"           # routé vers un humain avant création
    elif v.ecarts:
        v.verdict = "corrige"            # dossier créé mais un humain a dû corriger
    else:
        v.verdict = "auto_ok"
    return v


def valider_corpus(agent, emails: list[dict], verites: dict[str, dict], src: SourceSystems | None = None) -> list[Validation]:
    src = src or SourceSystems()
    return [valider(agent.traiter(e), e, verites[e["email_id"]], src) for e in emails]


def charger_corpus() -> tuple[list[dict], dict[str, dict]]:
    emails = [json.loads(l) for l in (DATA / "emails.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    verites = {d["email_id"]: d for d in (json.loads(l) for l in (DATA / "ground_truth.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}
    return emails, verites


def sauver(validations: list[Validation], chemin: Path = DATA / "validations.jsonl") -> None:
    with open(chemin, "w", encoding="utf-8") as f:
        for v in validations:
            f.write(json.dumps(v.__dict__, ensure_ascii=False) + "\n")
