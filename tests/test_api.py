"""Tests d'API (contrat, validation d'entrée, codes HTTP, cohérence des réponses).
Équivalents de la collection Postman `postman/email_to_case.postman_collection.json`, automatisés.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from e2c.api import app  # noqa: E402

client = TestClient(app)

EMAIL = {"email_id": "API001", "pays": "ES", "langue": "es", "semaine": 3, "expediteur": "carmen@textil-ramos.example",
         "objet": "Mercancía dañada – pedido ES-11112222, factura INV-2026-20001",
         "corps": "Buenos días,\n\nal recibir el pedido ES-11112222, dos palés llegaron dañados. Reclamamos 425,00 EUR "
                  "sobre la factura INV-2026-20001 (reservas anotadas en el albarán).\nNúmero de cliente: C100010.\n\nSaludos,\nCarmen"}


@pytest.fixture(autouse=True)
def reset():
    client.post("/reset")


def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_creation_dossier_contrat_de_reponse():
    r = client.post("/dossiers/from-email", json=EMAIL)
    assert r.status_code == 201
    d = r.json()
    for champ in ("type_demande", "customer_id", "order_no", "invoice_no", "montant", "devise", "urgence", "confiance", "a_creer", "trace", "decision"):
        assert champ in d
    assert d["type_demande"] == "avarie_marchandise" and d["montant"] == 425.0 and d["devise"] == "EUR"
    assert d["trace"]["moteur"] == "regles" and d["trace"]["duree_ms"] >= 0


def test_lecture_dossier_et_404():
    client.post("/dossiers/from-email", json=EMAIL)
    assert client.get("/dossiers/API001").status_code == 200
    assert client.get("/dossiers/INCONNU").status_code == 404


@pytest.mark.parametrize("patch", [{"pays": "IT"}, {"langue": "de"}, {"semaine": 0}, {"email_id": ""}, {"objet": "x" * 501}])
def test_validation_des_entrees(patch):
    r = client.post("/dossiers/from-email", json={**EMAIL, **patch})
    assert r.status_code == 422


def test_hors_perimetre_decision_ignorer():
    r = client.post("/dossiers/from-email", json={**EMAIL, "objet": "Out of office", "corps": "I am out of the office."})
    assert r.json()["decision"] == "ignorer" and r.json()["a_creer"] is False


def test_commande_inconnue_escalade_humaine():
    r = client.post("/dossiers/from-email", json=EMAIL)   # ES-11112222 n'existe pas dans les systèmes sources
    assert "commande_inconnue_ou_autre_client" in r.json()["anomalies_source"]
    assert r.json()["decision"] == "escalade_humaine"


def test_metrics_vides_puis_remplies():
    assert client.get("/metrics/summary").json()["emails_valides"] == 0
    from e2c.validate import charger_corpus
    emails, _ = charger_corpus()
    for e in emails[:20]:
        client.post("/dossiers/from-email", json={k: e[k] for k in ("email_id", "pays", "langue", "semaine", "expediteur", "objet", "corps", "pieces_jointes")})
    m = client.get("/metrics/summary").json()
    assert m["emails_valides"] == 20 and 0 <= m["taux_conversion"] <= 1
