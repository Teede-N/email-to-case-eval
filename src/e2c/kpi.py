"""KPI hebdomadaires de l'agent e-mail → dossier, par pays, par champ et dans le temps, et rapport go / no-go.

Définitions (documentées dans docs/kpi.md) :
  taux_conversion       = dossiers créés automatiquement sans correction humaine / e-mails à traiter
  precision_extraction  = champs corrects / champs évalués (par champ et global, hors e-mails ignorés)
  precision_classification = type de demande correct / e-mails
  taux_echec            = e-mails en escalade ou en erreur technique / e-mails à traiter
  faux_dossiers          = dossiers créés alors qu'il ne fallait pas (hors périmètre, doublons)
  dossiers_manques       = e-mails à traiter sans dossier
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .extract import CHAMPS
from .validate import Validation

RACINE = Path(__file__).resolve().parents[2]
REPORTS = RACINE / "reports"

SEUILS_GO = {"taux_conversion": 0.70, "precision_extraction": 0.95, "precision_classification": 0.95,
             "taux_echec": 0.15, "faux_dossiers": 0.02}


def _kpi(vs: list[Validation]) -> dict:
    n = len(vs)
    a_traiter = [v for v in vs if v.a_creer_attendu]
    k = {"emails": n, "a_traiter": len(a_traiter)}
    if not n:
        return k
    k["taux_conversion"] = sum(v.verdict == "auto_ok" for v in a_traiter) / max(1, len(a_traiter))
    k["precision_classification"] = sum(v.champs_ok.get("type_demande") for v in vs) / n
    k["taux_echec"] = sum(v.verdict == "escalade" or v.echec_trace is not None for v in a_traiter) / max(1, len(a_traiter))
    k["faux_dossiers"] = sum(v.verdict == "faux_dossier" for v in vs) / n
    k["dossiers_manques"] = sum(v.verdict == "dossier_manque" for v in a_traiter) / max(1, len(a_traiter))
    evalues = [ok for v in a_traiter for c, ok in v.champs_ok.items() if c != "type_demande" and ok is not None]
    k["precision_extraction"] = sum(evalues) / max(1, len(evalues))
    k["par_champ"] = {}
    for c in CHAMPS:
        vals = [v.champs_ok.get(c) for v in a_traiter if v.champs_ok.get(c) is not None]
        if vals:
            k["par_champ"][c] = round(sum(vals) / len(vals), 3)
    k["latence_ms_mediane"] = sorted(v.duree_ms for v in vs)[n // 2]
    for key in ("taux_conversion", "precision_classification", "taux_echec", "faux_dossiers", "dossiers_manques", "precision_extraction"):
        k[key] = round(k[key], 3)
    return k


def calculer(vs: list[Validation]) -> dict:
    par_pays = defaultdict(list)
    par_semaine = defaultdict(list)
    par_cas = defaultdict(list)
    par_pays_semaine = defaultdict(list)
    for v in vs:
        par_pays[v.pays].append(v)
        par_semaine[v.semaine].append(v)
        par_cas[v.cas_limite or "nominal"].append(v)
        par_pays_semaine[(v.pays, v.semaine)].append(v)
    return {
        "global": _kpi(vs),
        "par_pays": {p: _kpi(l) for p, l in sorted(par_pays.items())},
        "par_semaine": {s: _kpi(l) for s, l in sorted(par_semaine.items())},
        "par_cas_limite": {c: _kpi(l) for c, l in sorted(par_cas.items(), key=lambda x: -len(x[1]))},
        "par_pays_semaine": {f"{p}-S{s}": _kpi(l) for (p, s), l in sorted(par_pays_semaine.items())},
        "verdicts": {vd: sum(v.verdict == vd for v in vs) for vd in ("auto_ok", "corrige", "escalade", "faux_dossier", "dossier_manque", "ignore_ok")},
        "anomalies_source": _compte([a for v in vs for a in v.coherence_source]),
        "ecarts_frequents": _compte([e.split(":")[0] for v in vs for e in v.ecarts]),
    }


def _compte(items) -> dict:
    d = defaultdict(int)
    for i in items:
        d[i] += 1
    return dict(sorted(d.items(), key=lambda x: -x[1]))


def go_no_go(k: dict) -> tuple[str, list[str]]:
    """Décision de déploiement d'un pays : GO si tous les seuils sont respectés."""
    raisons = []
    for nom, seuil in SEUILS_GO.items():
        val = k.get(nom)
        if val is None:
            continue
        if nom in ("taux_echec", "faux_dossiers"):
            if val > seuil:
                raisons.append(f"{nom} {val:.1%} > {seuil:.0%}")
        elif val < seuil:
            raisons.append(f"{nom} {val:.1%} < {seuil:.0%}")
    return ("GO" if not raisons else "NO-GO"), raisons


def pct(x) -> str:
    return "–" if x is None else f"{x:.1%}"


def tableau(lignes: list[dict], cols: list[tuple[str, str]]) -> str:
    out = ["| " + " | ".join(t for _, t in cols) + " |", "|" + "---|" * len(cols)]
    for l in lignes:
        out.append("| " + " | ".join(str(l.get(c, "–")) for c, _ in cols) + " |")
    return "\n".join(out)


def tracer(k: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    REPORTS.mkdir(exist_ok=True)
    semaines = sorted(k["par_semaine"])
    fig, ax = plt.subplots(figsize=(8, 4))
    for nom, lab in [("taux_conversion", "Taux de conversion"), ("precision_extraction", "Précision d'extraction"),
                     ("precision_classification", "Précision de classification"), ("taux_echec", "Taux d'échec")]:
        ax.plot([f"S{s}" for s in semaines], [k["par_semaine"][s][nom] for s in semaines], marker="o", label=lab)
    ax.set_ylim(0, 1.02); ax.set_ylabel("taux"); ax.set_title("KPI de l'agent par semaine (tous pays)")
    ax.grid(alpha=.3); ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout(); fig.savefig(REPORTS / "kpi_par_semaine.png", dpi=150); plt.close(fig)

    pays = sorted(k["par_pays"])
    fig, ax = plt.subplots(figsize=(8, 4))
    champs = [c for c in CHAMPS if c != "type_demande"]
    largeur = 0.8 / len(pays)
    for i, p in enumerate(pays):
        vals = [k["par_pays"][p]["par_champ"].get(c, 0) for c in champs]
        ax.bar([j + i * largeur for j in range(len(champs))], vals, width=largeur, label=p)
    ax.set_xticks([j + 0.4 - largeur / 2 for j in range(len(champs))]); ax.set_xticklabels(champs, rotation=20, fontsize=8)
    ax.set_ylim(0, 1.02); ax.set_title("Précision d'extraction par champ et par pays"); ax.legend(fontsize=8); ax.grid(axis="y", alpha=.3)
    fig.tight_layout(); fig.savefig(REPORTS / "precision_par_champ_pays.png", dpi=150); plt.close(fig)


def rapport(k: dict, agent: str, semaine_courante: int | None = None) -> str:
    g = k["global"]
    semaine_courante = semaine_courante or max(k["par_semaine"])
    lignes = [f"# Rapport KPI hebdomadaire – agent e-mail → dossier (`{agent}`)", "",
              f"Semaine de référence : **S{semaine_courante}** · corpus : {g['emails']} e-mails sur {len(k['par_semaine'])} semaines, "
              f"{len(k['par_pays'])} pays. Définitions des KPI : [docs/kpi.md](../docs/kpi.md).", "",
              "## 1. Vue d'ensemble", "",
              tableau([{"kpi": "Taux de conversion (dossier auto sans correction)", "val": pct(g["taux_conversion"]), "seuil": "≥ 70 %"},
                       {"kpi": "Précision d'extraction (tous champs)", "val": pct(g["precision_extraction"]), "seuil": "≥ 95 %"},
                       {"kpi": "Précision de classification", "val": pct(g["precision_classification"]), "seuil": "≥ 95 %"},
                       {"kpi": "Taux d'échec (escalade ou erreur)", "val": pct(g["taux_echec"]), "seuil": "≤ 15 %"},
                       {"kpi": "Faux dossiers (hors périmètre, doublons)", "val": pct(g["faux_dossiers"]), "seuil": "≤ 2 %"},
                       {"kpi": "Dossiers manqués", "val": pct(g["dossiers_manques"]), "seuil": "–"},
                       {"kpi": "Latence médiane", "val": f"{g['latence_ms_mediane']} ms", "seuil": "–"}],
                      [("kpi", "KPI"), ("val", "Valeur"), ("seuil", "Seuil go/no-go")]), "",
              "Verdicts de validation : " + ", ".join(f"{vd} {n}" for vd, n in k["verdicts"].items()) + ".", "",
              "![KPI par semaine](kpi_par_semaine.png)", "",
              "## 2. Par pays et décision de déploiement", ""]
    rows = []
    for p, kp in k["par_pays"].items():
        dec, raisons = go_no_go(kp)
        rows.append({"pays": p, "n": kp["emails"], "conv": pct(kp["taux_conversion"]), "ext": pct(kp["precision_extraction"]),
                     "cla": pct(kp["precision_classification"]), "ech": pct(kp["taux_echec"]), "faux": pct(kp["faux_dossiers"]),
                     "dec": f"**{dec}**" + (f" ({'; '.join(raisons)})" if raisons else "")})
    lignes += [tableau(rows, [("pays", "Pays"), ("n", "E-mails"), ("conv", "Conversion"), ("ext", "Extraction"), ("cla", "Classification"),
                              ("ech", "Échec"), ("faux", "Faux dossiers"), ("dec", "Décision")]), "",
               "![Précision par champ et pays](precision_par_champ_pays.png)", "",
               "## 3. Précision par champ", "",
               tableau([{"champ": c, "val": pct(g["par_champ"].get(c))} for c in CHAMPS], [("champ", "Champ"), ("val", "Précision")]), "",
               "## 4. Tendance par semaine", "",
               tableau([{"s": f"S{s}", "n": ks["emails"], "conv": pct(ks["taux_conversion"]), "ext": pct(ks["precision_extraction"]),
                         "ech": pct(ks["taux_echec"])} for s, ks in k["par_semaine"].items()],
                       [("s", "Semaine"), ("n", "E-mails"), ("conv", "Conversion"), ("ext", "Extraction"), ("ech", "Échec")]), "",
               "## 5. Où l'agent échoue : cas limites", "",
               tableau([{"cas": c, "n": kc["emails"], "conv": pct(kc["taux_conversion"]), "ext": pct(kc["precision_extraction"]),
                         "ech": pct(kc["taux_echec"]), "faux": pct(kc["faux_dossiers"])} for c, kc in k["par_cas_limite"].items()],
                       [("cas", "Cas"), ("n", "E-mails"), ("conv", "Conversion"), ("ext", "Extraction"), ("ech", "Échec"), ("faux", "Faux dossiers")]), "",
               "Écarts les plus fréquents (champ prédit ≠ attendu) : " + ", ".join(f"{c} ({n})" for c, n in k["ecarts_frequents"].items()) + ".", "",
               "Anomalies détectées via les systèmes sources (sans vérité terrain) : " + ", ".join(f"{a} ({n})" for a, n in k["anomalies_source"].items()) + ".", ""]
    return "\n".join(lignes)


def ecrire(k: dict, agent: str) -> None:
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "kpi_hebdo.md").write_text(rapport(k, agent), encoding="utf-8")
    (REPORTS / "kpi.json").write_text(json.dumps(k, ensure_ascii=False, indent=2), encoding="utf-8")
