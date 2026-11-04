"""Transforme les écarts de validation en rapports de bug structurés (contexte, étapes, attendu vs réel),
regroupés par motif, prêts à être collés dans un dossier Jira.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .validate import Validation

RACINE = Path(__file__).resolve().parents[2]

GRAVITE = {"faux_dossier": "Majeure", "dossier_manque": "Majeure", "escalade": "Mineure", "corrige": "Moyenne"}


def motif(v: Validation) -> str:
    if v.verdict == "faux_dossier":
        return f"Faux dossier sur e-mail {v.type_attendu} ({v.cas_limite or 'nominal'})"
    if v.verdict == "dossier_manque":
        return f"Dossier manqué ({v.cas_limite or 'nominal'})"
    champs = sorted({e.split(":")[0] for e in v.ecarts})
    base = ", ".join(champs) if champs else "escalade"
    return f"{base} incorrect – cas {v.cas_limite or 'nominal'}"


def rapports_bugs(validations: list[Validation], emails: dict[str, dict], max_exemples: int = 3) -> str:
    groupes: dict[str, list[Validation]] = defaultdict(list)
    for v in validations:
        if v.verdict in ("corrige", "faux_dossier", "dossier_manque") or (v.verdict == "escalade" and v.ecarts):
            groupes[motif(v)].append(v)
    lignes = ["# Bugs structurés issus de la validation", "",
              "Un bug par motif d'écart, avec des exemples reproductibles tirés du corpus. Gravité : Majeure = dossier faux ou manquant, "
              "Moyenne = correction humaine nécessaire, Mineure = escalade justifiée mais perfectible.", ""]
    for i, (m, vs) in enumerate(sorted(groupes.items(), key=lambda x: -len(x[1])), 1):
        grav = GRAVITE[vs[0].verdict]
        pays = sorted({v.pays for v in vs})
        lignes += [f"## BUG-{i:03d} · {m}", "",
                   f"- **Gravité** : {grav} · **Occurrences** : {len(vs)} · **Pays** : {', '.join(pays)}",
                   f"- **Contexte** : agent `regles`, corpus synthétique, semaines {min(v.semaine for v in vs)}–{max(v.semaine for v in vs)}.",
                   "- **Étapes pour reproduire** :", "    1. `PYTHONPATH=src python -m e2c.cli run`",
                   f"    2. Ouvrir `data/validations.jsonl`, filtrer `email_id` ∈ {{{', '.join(v.email_id for v in vs[:max_exemples])}}}.",
                   "    3. Comparer le dossier produit à `data/ground_truth.jsonl`.", ""]
        for v in vs[:max_exemples]:
            e = emails[v.email_id]
            lignes += [f"**Exemple {v.email_id}** ({v.pays}, {v.langue}, S{v.semaine}) – objet : _{e['objet'][:90]}_", "",
                       "| | Attendu | Réel |", "|---|---|---|",
                       f"| Type | {v.type_attendu} | {v.type_predit} |",
                       f"| Dossier à créer | {v.a_creer_attendu} | {v.a_creer_predit} |"]
            for ec in v.ecarts:
                champ, reste = ec.split(":", 1)
                pred, att = reste.split("≠")
                lignes.append(f"| {champ.strip()} | {att.strip()} | {pred.strip()} |")
            if v.coherence_source:
                lignes.append(f"| Anomalies systèmes sources | – | {', '.join(v.coherence_source)} |")
            lignes.append("")
        lignes.append("")
    return "\n".join(lignes)
