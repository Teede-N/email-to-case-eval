"""Console de validation « humain sur la boucle » et suivi des KPI.

Lancer : PYTHONPATH=src streamlit run app.py
"""
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE / "src"))
from e2c import kpi  # noqa: E402
from e2c.extract import RuleAgent, dossier_vers_dict  # noqa: E402
from e2c.validate import SourceSystems, charger_corpus  # noqa: E402

st.set_page_config(page_title="e-mail → dossier – validation", page_icon="📨", layout="wide")


@st.cache_data
def charger():
    emails, verites = charger_corpus()
    vals = [json.loads(l) for l in (RACINE / "data" / "validations.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    k = json.loads((RACINE / "reports" / "kpi.json").read_text(encoding="utf-8"))
    return emails, verites, vals, k


emails, verites, vals, k = charger()
df = pd.DataFrame(vals)
par_id = {e["email_id"]: e for e in emails}

st.title("📨 e-mail → dossier – console de validation")
st.caption("Agent sous test : règles · corpus synthétique multilingue · vérité terrain et systèmes sources fictifs")

onglet_kpi, onglet_revue, onglet_un = st.tabs(["KPI hebdomadaires", "File de revue humaine", "Tester un e-mail"])

with onglet_kpi:
    g = k["global"]
    c = st.columns(5)
    c[0].metric("Taux de conversion", f"{g['taux_conversion']:.1%}", "cible ≥ 70 %", delta_color="off")
    c[1].metric("Précision d'extraction", f"{g['precision_extraction']:.1%}", "cible ≥ 95 %", delta_color="off")
    c[2].metric("Précision de classification", f"{g['precision_classification']:.1%}", "cible ≥ 95 %", delta_color="off")
    c[3].metric("Taux d'échec", f"{g['taux_echec']:.1%}", "cible ≤ 15 %", delta_color="off")
    c[4].metric("Faux dossiers", f"{g['faux_dossiers']:.1%}", "cible ≤ 2 %", delta_color="off")
    col1, col2 = st.columns(2)
    col1.image(str(RACINE / "reports" / "kpi_par_semaine.png"))
    col2.image(str(RACINE / "reports" / "precision_par_champ_pays.png"))
    st.subheader("Décision de déploiement par pays")
    lignes = []
    for p, kp in k["par_pays"].items():
        dec, raisons = kpi.go_no_go(kp)
        lignes.append({"Pays": p, "E-mails": kp["emails"], "Conversion": f"{kp['taux_conversion']:.1%}", "Extraction": f"{kp['precision_extraction']:.1%}",
                       "Classification": f"{kp['precision_classification']:.1%}", "Échec": f"{kp['taux_echec']:.1%}", "Décision": dec, "Motifs": "; ".join(raisons)})
    st.dataframe(pd.DataFrame(lignes), hide_index=True, use_container_width=True)
    st.subheader("Où l'agent échoue")
    st.dataframe(pd.DataFrame([{"Cas": c_, "E-mails": v["emails"], "Conversion": f"{v['taux_conversion']:.1%}", "Extraction": f"{v['precision_extraction']:.1%}",
                                "Échec": f"{v['taux_echec']:.1%}"} for c_, v in k["par_cas_limite"].items()]), hide_index=True, use_container_width=True)

with onglet_revue:
    st.markdown("E-mails dont le dossier a été **escaladé** ou **corrigé** : le validateur compare les champs extraits aux systèmes sources et à la référence.")
    f1, f2, f3 = st.columns(3)
    pays = f1.multiselect("Pays", sorted(df.pays.unique()), default=sorted(df.pays.unique()))
    verdicts = f2.multiselect("Verdict", ["escalade", "corrige", "dossier_manque", "faux_dossier", "auto_ok", "ignore_ok"], default=["escalade", "corrige", "dossier_manque"])
    cas = f3.multiselect("Cas limite", sorted(df.cas_limite.fillna("nominal").unique()), default=sorted(df.cas_limite.fillna("nominal").unique()))
    sel = df[df.pays.isin(pays) & df.verdict.isin(verdicts) & df.cas_limite.fillna("nominal").isin(cas)]
    st.write(f"**{len(sel)}** e-mails à revoir")
    st.dataframe(sel[["email_id", "pays", "semaine", "cas_limite", "type_attendu", "type_predit", "verdict", "ecarts", "coherence_source", "confiance"]],
                 hide_index=True, use_container_width=True, height=260)
    choix = st.selectbox("Ouvrir un e-mail", sel.email_id.tolist()) if len(sel) else None
    if choix:
        e, v, vt = par_id[choix], sel[sel.email_id == choix].iloc[0], verites[choix]
        a, b = st.columns([3, 2])
        with a:
            st.markdown(f"**Objet :** {e['objet']}")
            st.text(e["corps"])
            if e["pieces_jointes"]:
                st.caption("Pièces jointes : " + ", ".join(e["pieces_jointes"]))
        with b:
            st.markdown(f"**Verdict :** `{v.verdict}` · confiance {v.confiance}")
            t = RuleAgent(src=SourceSystems()).traiter(e)
            comp = pd.DataFrame({"Attendu (référence)": {c_: vt.get(c_) for c_ in ("type_demande", "customer_id", "order_no", "invoice_no", "montant", "devise", "urgence")},
                                 "Extrait par l'agent": {c_: getattr(t, c_) for c_ in ("type_demande", "customer_id", "order_no", "invoice_no", "montant", "devise", "urgence")}})
            st.dataframe(comp, use_container_width=True)
            if v.coherence_source:
                st.warning("Anomalies systèmes sources : " + ", ".join(v.coherence_source))
            st.markdown("**Trace de l'agent**")
            for et in t.trace.etapes:
                st.write("· " + et)
            d1, d2 = st.columns(2)
            d1.button("✅ Valider le dossier", key="ok")
            d2.button("✏️ Corriger et créer", key="fix")

with onglet_un:
    exemple = emails[0]
    objet = st.text_input("Objet", exemple["objet"])
    corps = st.text_area("Corps", exemple["corps"], height=180)
    langue = st.selectbox("Langue", ["fr", "es", "nl"], index=["fr", "es", "nl"].index(exemple["langue"]))
    if st.button("Traiter"):
        t = RuleAgent(src=SourceSystems()).traiter({"email_id": "UI", "pays": {"fr": "FR", "en": "ES", "it": "IT", "de": "DE"}[langue], "langue": langue,
                                                   "semaine": 1, "expediteur": "ui@test", "objet": objet, "corps": corps, "pieces_jointes": []})
        st.json(dossier_vers_dict(t))
