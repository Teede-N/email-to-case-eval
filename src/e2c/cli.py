"""Ligne de commande du banc d'évaluation.

  PYTHONPATH=src python -m e2c.cli run [--agent regles|claude|auto]   valide tout le corpus, écrit data/validations.jsonl,
                                                                         reports/kpi_hebdo.md, reports/kpi.json, les graphiques
                                                                         et docs/bugs.md
  PYTHONPATH=src python -m e2c.cli one M00042                         traite un e-mail et affiche le dossier + la trace
  PYTHONPATH=src python -m e2c.cli gonogo NL                          décision de déploiement pour un pays
"""
from __future__ import annotations

import argparse
import json
import sys

from . import bugs, kpi
from .extract import choisir_agent, dossier_vers_dict
from .validate import SourceSystems, charger_corpus, sauver, valider_corpus


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="e2c")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--agent", default="regles")
    o = sub.add_parser("one"); o.add_argument("email_id"); o.add_argument("--agent", default="regles")
    g = sub.add_parser("gonogo"); g.add_argument("pays")
    a = ap.parse_args(argv)

    emails, verites = charger_corpus()
    if a.cmd == "one":
        e = next((x for x in emails if x["email_id"] == a.email_id), None)
        if not e:
            print("e-mail inconnu"); return 1
        t = choisir_agent(a.agent, src=SourceSystems()).traiter(e)
        print(json.dumps({"email": e, "dossier": dossier_vers_dict(t), "attendu": verites[e["email_id"]]}, ensure_ascii=False, indent=2))
        return 0
    if a.cmd == "gonogo":
        k = json.loads((kpi.REPORTS / "kpi.json").read_text(encoding="utf-8"))
        if a.pays not in k["par_pays"]:
            print("pays inconnu"); return 1
        dec, raisons = kpi.go_no_go(k["par_pays"][a.pays])
        print(f"{a.pays} : {dec}" + (f" – {'; '.join(raisons)}" if raisons else ""))
        return 0

    src = SourceSystems()
    agent = choisir_agent(a.agent, src=src)
    vs = valider_corpus(agent, emails, verites, src)
    sauver(vs)
    k = kpi.calculer(vs)
    kpi.tracer(k)
    kpi.ecrire(k, agent.nom)
    (kpi.RACINE / "docs").mkdir(exist_ok=True)
    (kpi.RACINE / "docs" / "bugs.md").write_text(bugs.rapports_bugs(vs, {e["email_id"]: e for e in emails}), encoding="utf-8")
    gl = k["global"]
    print(f"{gl['emails']} e-mails · conversion {gl['taux_conversion']:.1%} · extraction {gl['precision_extraction']:.1%} · "
          f"classification {gl['precision_classification']:.1%} · échec {gl['taux_echec']:.1%} · faux dossiers {gl['faux_dossiers']:.1%}")
    for p, kp in k["par_pays"].items():
        dec, raisons = kpi.go_no_go(kp)
        print(f"  {p}: {dec:6} conv {kp['taux_conversion']:.1%} ext {kp['precision_extraction']:.1%} cla {kp['precision_classification']:.1%}"
              + (f"  ← {'; '.join(raisons)}" if raisons else ""))
    print("Rapport : reports/kpi_hebdo.md · bugs : docs/bugs.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
