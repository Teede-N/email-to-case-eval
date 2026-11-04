"""Exécution des critères d'acceptation Gherkin (features/email_to_case.feature) avec pytest-bdd."""
import sys
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
from e2c.extract import RuleAgent  # noqa: E402
from e2c.validate import SourceSystems, valider  # noqa: E402

scenarios(str(RACINE / "features" / "email_to_case.feature"))

PAYS = {"fr": "FR", "es": "ES", "nl": "NL"}


@pytest.fixture
def ctx():
    return {"email": {"email_id": "G001", "pays": "FR", "langue": "fr", "semaine": 1, "expediteur": "g@client.example",
                      "objet": "", "corps": "", "pieces_jointes": []}}


@given("l'agent e-mail → dossier est connecté aux systèmes sources", target_fixture="agent")
def agent():
    src = SourceSystems()
    a = RuleAgent(src=src)
    a._src = src
    return a


@given(parsers.parse('un e-mail en "{langue}" dont l\'objet est "{objet}"'))
def email_objet(ctx, langue, objet):
    ctx["email"].update(langue=langue, objet=objet, pays=PAYS[langue])


@given(parsers.parse('dont le corps mentionne la commande "{cmd}", le client "{cli}" et le montant "{mt}"'))
def corps_complet(ctx, cmd, cli, mt):
    ctx["email"]["corps"] = (f"Bonjour,\n\nà la réception de la commande {cmd}, deux palettes étaient endommagées. Nous réclamons {mt} "
                             f"au titre de la facture INV-2026-11111 (réserves). Numéro client : {cli}.")


@given(parsers.parse('dont le corps est "{corps}"'))
def corps_libre(ctx, corps):
    ctx["email"]["corps"] = corps


@given("dont le corps mentionne une commande d'un autre client")
def commande_autre(ctx, agent):
    autre = agent._src.con.execute("SELECT order_no FROM commandes WHERE customer_id<>'C100001' LIMIT 1").fetchone()[0]
    ctx["email"]["corps"] = (f"Bonjour, à la réception de la commande {autre}, deux palettes étaient endommagées. "
                             "Nous réclamons 1.000,00 EUR au titre de la facture INV-2026-11111. Numéro client : C100001.")
    ctx["attendu_commande"] = "FR-00000000"


@given("dont le corps mentionne seulement une commande en cours connue")
def commande_seule(ctx, agent):
    cmd, cid = agent._src.con.execute("SELECT order_no, customer_id FROM commandes WHERE statut='en_cours' LIMIT 1").fetchone()
    ctx["email"]["corps"] = f"Goedemiddag, zending {cmd} is nog niet aangekomen. Graag een nieuwe leverdatum."
    ctx["proprietaire"] = cid


@given("l'agent a déjà traité cet e-mail")
def deja_traite(ctx, agent):
    agent.traiter(dict(ctx["email"]))


@when("l'agent traite l'e-mail")
def traite(ctx, agent):
    ctx["dossier"] = agent.traiter(ctx["email"])


@when(parsers.parse('l\'agent traite le même e-mail renvoyé avec l\'objet préfixé "{prefixe}"'))
def traite_renvoi(ctx, agent, prefixe):
    e = dict(ctx["email"], email_id="G001D", objet=f"{prefixe} {ctx['email']['objet']}")
    ctx["dossier"] = agent.traiter(e)


@then(parsers.parse('le type de demande est "{typ}"'))
def type_est(ctx, typ):
    assert ctx["dossier"].type_demande == typ


@then(parsers.parse('le dossier est créé automatiquement avec l\'urgence "{urg}"'))
def cree_urgence(ctx, urg):
    d = ctx["dossier"]
    assert d.a_creer and d.trace.echec is None and d.urgence == urg


@then(parsers.parse('le montant extrait vaut {montant:g} "{devise}"'))
def montant_vaut(ctx, montant, devise):
    assert ctx["dossier"].montant == pytest.approx(montant) and ctx["dossier"].devise == devise


@then("aucun dossier n'est créé")
def aucun_dossier(ctx):
    assert ctx["dossier"].a_creer is False


@then(parsers.parse('la trace mentionne "{mot}"'))
def trace_mentionne(ctx, mot):
    assert any(mot in e for e in ctx["dossier"].trace.etapes)


@then(parsers.parse('la validation signale l\'anomalie "{anomalie}"'))
def anomalie(ctx, agent, anomalie):
    verite = {"type_demande": "avarie_marchandise", "customer_id": "C100001", "order_no": ctx["attendu_commande"], "invoice_no": "INV-2026-11111",
              "montant": 1000.0, "devise": "EUR", "urgence": "haute", "a_creer": True}
    ctx["validation"] = valider(ctx["dossier"], ctx["email"], verite, agent._src)
    assert anomalie in ctx["validation"].coherence_source


@then(parsers.parse('le verdict de validation est "{verdict}"'))
def verdict(ctx, verdict):
    assert ctx["validation"].verdict == verdict


@then("le dossier porte le numéro client propriétaire de cette commande")
def proprietaire(ctx):
    assert ctx["dossier"].customer_id == ctx["proprietaire"]
