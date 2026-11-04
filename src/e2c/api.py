"""API du service e-mail → dossier (FastAPI) : la surface testée par les tests d'API et la collection Postman.

  POST /dossiers/from-email   e-mail → dossier + trace
  GET  /dossiers/{email_id}   dossier déjà produit
  GET  /health
  GET  /metrics/summary      KPI calculés sur les dossiers produits depuis le démarrage (si vérité terrain connue)

Lancer : PYTHONPATH=src uvicorn e2c.api:app --reload
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .extract import RuleAgent, choisir_agent, dossier_vers_dict
from .kpi import calculer
from .validate import SourceSystems, charger_corpus, valider

app = FastAPI(title="E-mail → dossier (banc d'évaluation)", version="1.0.0")
_agent: RuleAgent = choisir_agent("regles", src=SourceSystems())
_dossiers: dict[str, dict] = {}
_validations: list = []
_verites: dict[str, dict] = {}
_src: SourceSystems | None = None


class EmailIn(BaseModel):
    email_id: str = Field(..., min_length=1, max_length=20)
    pays: str = Field(..., pattern="^(FR|BE|ES|NL)$")
    langue: str = Field("fr", pattern="^(fr|es|nl)$")
    semaine: int = Field(1, ge=1, le=53)
    expediteur: str
    objet: str = Field(..., max_length=500)
    corps: str = Field(..., max_length=20000)
    pieces_jointes: list[str] = []


def _ref():
    global _src, _verites
    if _src is None:
        _src = SourceSystems()
        try:
            _, _verites = charger_corpus()
        except FileNotFoundError:
            _verites = {}
    return _src


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "agent": _agent.nom, "dossiers": len(_dossiers)}


@app.post("/dossiers/from-email", status_code=201)
def from_email(email: EmailIn) -> dict[str, Any]:
    t = _agent.traiter(email.model_dump())
    d = dossier_vers_dict(t)
    _dossiers[email.email_id] = d
    src = _ref()
    if email.email_id in _verites:
        _validations.append(valider(t, email.model_dump(), _verites[email.email_id], src))
    from .validate import coherence
    d["anomalies_source"] = coherence(t, src)
    d["decision"] = ("ignorer" if not t.a_creer else "escalade_humaine" if (t.trace.echec or d["anomalies_source"]) else "creer")
    return d


@app.get("/dossiers/{email_id}")
def get_dossier(email_id: str) -> dict[str, Any]:
    if email_id not in _dossiers:
        raise HTTPException(404, "dossier inconnu")
    return _dossiers[email_id]


@app.get("/metrics/summary")
def metrics() -> dict[str, Any]:
    if not _validations:
        return {"emails_valides": 0}
    k = calculer(_validations)
    return {"emails_valides": len(_validations), **{c: k["global"][c] for c in
            ("taux_conversion", "precision_extraction", "precision_classification", "taux_echec", "faux_dossiers")}}


@app.post("/reset", status_code=204)
def reset() -> None:
    global _agent
    _agent = choisir_agent("regles", src=_ref())
    _dossiers.clear(); _validations.clear()
