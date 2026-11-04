"""Génère un corpus synthétique d'e-mails clients d'une PME de transport et logistique (fictive) avec la vérité terrain.

Sortie :
  data/emails.jsonl       e-mails entrants (id, pays, langue, semaine, objet, corps, pièces jointes, cas limite)
  data/reference.sqlite   « systèmes sources » : clients, commandes de transport, factures
  data/ground_truth.jsonl champs attendus par e-mail (ce que le dossier devrait contenir)

Le corpus couvre 4 pays (FR, BE, ES, NL), 8 semaines, 5 types de demande, et injecte des cas limites :
fautes de frappe, champs manquants, chaînes de transfert, pièce jointe sans texte, montants ambigus (TVA),
post-scriptum ambigus, e-mails hors périmètre, doublons.

Usage : python data/generate_corpus.py [--n 600] [--seed 42]
"""
from __future__ import annotations

import argparse
import json
import random
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ICI = Path(__file__).resolve().parent

PAYS = {
    "FR": {"langue": "fr", "poids": 0.40},
    "BE": {"langue": "fr", "poids": 0.15},
    "ES": {"langue": "es", "poids": 0.25},
    "NL": {"langue": "nl", "poids": 0.20},
}
TYPES = ["reclamation_livraison", "avarie_marchandise", "demande_devis", "modification_commande", "question_facture"]

PRENOMS = ["Marie", "Lucas", "Carmen", "Anna", "Paul", "Javier", "Sanne", "Lena", "Sophie", "Diego", "Emma", "Bram"]
SOCIETES = ["Delta Négoce", "Iberia Frutas", "Van Dijk Interieur", "Atelier Rousseau", "Lumière Cosmétiques", "Textil Ramos",
            "Brabant Fietsen", "Boulangeries Martin", "Cerámica Soler", "Noord Zonnepanelen", "Maison Lefèvre", "Pinturas Vega"]

SUJETS = {
    "reclamation_livraison": {
        "fr": "Réclamation – commande {cmd} non livrée ({soc})",
        "es": "Reclamación – pedido {cmd} no entregado ({soc})",
        "nl": "Klacht – zending {cmd} niet geleverd ({soc})",
    },
    "avarie_marchandise": {
        "fr": "Avarie à la livraison – commande {cmd}, facture {inv}",
        "es": "Mercancía dañada – pedido {cmd}, factura {inv}",
        "nl": "Beschadigde goederen – zending {cmd}, factuur {inv}",
    },
    "demande_devis": {
        "fr": "Demande de devis – transport palettes vers {soc}",
        "es": "Solicitud de presupuesto – transporte de palés a {soc}",
        "nl": "Offerteaanvraag – pallettransport naar {soc}",
    },
    "modification_commande": {
        "fr": "Modification de la commande {cmd} – adresse de livraison",
        "es": "Modificación del pedido {cmd} – dirección de entrega",
        "nl": "Wijziging zending {cmd} – afleveradres",
    },
    "question_facture": {
        "fr": "Question sur la facture {inv}",
        "es": "Consulta sobre la factura {inv}",
        "nl": "Vraag over factuur {inv}",
    },
}

CORPS = {
    "reclamation_livraison": {
        "fr": "Bonjour,\n\nLa commande {cmd} destinée à {soc} devait être livrée le {ech} et n'est toujours pas arrivée. "
              "Merci de nous indiquer une nouvelle date.\nNuméro client : {cli}.\n\nCordialement,\n{prenom}",
        "es": "Buenos días,\n\nel pedido {cmd} destinado a {soc} debía entregarse el {ech} y todavía no ha llegado. "
              "Les rogamos una nueva fecha.\nNúmero de cliente: {cli}.\n\nSaludos,\n{prenom}",
        "nl": "Goedemiddag,\n\nzending {cmd} voor {soc} had op {ech} geleverd moeten zijn en is nog niet aangekomen. "
              "Graag een nieuwe leverdatum.\nKlantnummer: {cli}.\n\nMet vriendelijke groet,\n{prenom}",
    },
    "avarie_marchandise": {
        "fr": "Bonjour,\n\nÀ la réception de la commande {cmd}, deux palettes étaient endommagées. Nous réclamons {mt} EUR "
              "au titre de la facture {inv} (réserves notées sur le bon de livraison).\nNuméro client : {cli}.\n\nCordialement,\n{prenom}",
        "es": "Buenos días,\n\nal recibir el pedido {cmd}, dos palés llegaron dañados. Reclamamos {mt} EUR "
              "sobre la factura {inv} (reservas anotadas en el albarán).\nNúmero de cliente: {cli}.\n\nSaludos,\n{prenom}",
        "nl": "Goedemiddag,\n\nbij ontvangst van zending {cmd} waren twee pallets beschadigd. Wij claimen € {mt} "
              "op factuur {inv} (voorbehoud genoteerd op de vrachtbrief).\nKlantnummer: {cli}.\n\nMet vriendelijke groet,\n{prenom}",
    },
    "demande_devis": {
        "fr": "Bonjour,\n\nPouvez-vous nous chiffrer un transport de 12 palettes vers {soc}, budget indicatif {mt} EUR ? "
              "Client {cli}.\n\nMerci,\n{prenom}",
        "es": "Hola,\n\n¿podrían presupuestar un transporte de 12 palés a {soc}, presupuesto orientativo {mt} EUR? "
              "Cliente {cli}.\n\nGracias,\n{prenom}",
        "nl": "Hallo,\n\nkunnen jullie een offerte maken voor 12 pallets naar {soc}, richtbudget {mt} EUR? "
              "Klant {cli}.\n\nBedankt,\n{prenom}",
    },
    "modification_commande": {
        "fr": "Bonjour,\n\nMerci de modifier l'adresse de livraison de la commande {cmd} (client {cli}) : {adr}.\n\n{prenom}",
        "es": "Buenos días,\n\nles pedimos cambiar la dirección de entrega del pedido {cmd} (cliente {cli}): {adr}.\n\n{prenom}",
        "nl": "Goedemiddag,\n\ngraag het afleveradres van zending {cmd} (klant {cli}) wijzigen naar: {adr}.\n\n{prenom}",
    },
    "question_facture": {
        "fr": "Bonjour,\n\nNous avons reçu la facture {inv} de {mt} EUR mais le montant ne correspond pas au devis de la commande {cmd}. "
              "Pouvez-vous vérifier ? Client {cli}.\n\n{prenom}",
        "es": "Buenos días,\n\nhemos recibido la factura {inv} de {mt} EUR pero el importe no coincide con el presupuesto del pedido {cmd}. "
              "¿Pueden comprobarlo? Cliente {cli}.\n\n{prenom}",
        "nl": "Goedemiddag,\n\nwij ontvingen factuur {inv} van € {mt}, maar het bedrag komt niet overeen met de offerte voor zending {cmd}. "
              "Kunnen jullie dit nakijken? Klant {cli}.\n\n{prenom}",
    },
}

HORS_PERIMETRE = [
    ("Candidature spontanée – conducteur SPL", "Bonjour, je vous adresse ma candidature pour un poste de conducteur. CV en pièce jointe."),
    ("Newsletter : nos offres du mois", "Profitez de -30 % sur nos formations en ligne. Désabonnement en bas de page."),
    ("Out of office", "I am currently out of the office and will reply on my return."),
    ("Invitation : webinar logistique durable", "Rejoignez notre webinar jeudi à 11 h. Lien de connexion ci-dessous."),
]

PS_AMBIGU = {
    "fr": "\n\nPS : une modification de notre adresse de livraison habituelle vous sera envoyée séparément ; inutile de la modifier ici.",
    "es": "\n\nPD: una modificación de nuestra dirección de entrega habitual se enviará por separado; no hace falta cambiar nada aquí.",
    "nl": "\n\nPS: een wijziging van ons vaste afleveradres volgt apart; hier hoeft u niets te wijzigen.",
}

ADRESSES = ["12 rue des Lilas, 69007 Lyon", "Calle Mayor 18, 28013 Madrid", "Keizersgracht 4, 1015 Amsterdam",
            "Rue Neuve 7, 1000 Bruxelles", "8 avenue Foch, 75116 Paris", "Avinguda Diagonal 3, 08019 Barcelona"]


def fmt_montant(x: float, langue: str) -> str:
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")  # 1.234,56 (fr, es, nl)


def typo(s: str, rng: random.Random) -> str:
    """Introduit une ou deux fautes de frappe dans un texte (hors identifiants)."""
    mots = s.split(" ")
    for _ in range(rng.randint(1, 2)):
        i = rng.randrange(len(mots))
        m = mots[i]
        if len(m) > 4 and m.isalpha():
            j = rng.randrange(1, len(m) - 1)
            mots[i] = m[:j] + m[j + 1] + m[j] + m[j + 2:]
    return " ".join(mots)


def retirer_client(corps: str, cid: str) -> str:
    for motif in (f"Numéro client : {cid}.", f"Número de cliente: {cid}.", f"Klantnummer: {cid}.",
                  f"Client {cid}.", f"Cliente {cid}.", f"Klant {cid}.", f"client {cid}", f"cliente {cid}", f"klant {cid}"):
        corps = corps.replace(motif, "")
    return corps


def main(n: int, seed: int) -> None:
    rng = random.Random(seed)
    debut = datetime(2026, 9, 7)  # lundi, semaine 1

    # --- systèmes sources ---------------------------------------------------
    db = ICI / "reference.sqlite"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE clients (customer_id TEXT PRIMARY KEY, nom TEXT, pays TEXT);
        CREATE TABLE commandes (order_no TEXT PRIMARY KEY, customer_id TEXT, pays TEXT, statut TEXT);
        CREATE TABLE factures (invoice_no TEXT PRIMARY KEY, customer_id TEXT, montant REAL, devise TEXT, echeance TEXT);
    """)
    clients, commandes, factures = [], [], []
    for k in range(80):
        pays = rng.choices(list(PAYS), weights=[p["poids"] for p in PAYS.values()])[0]
        cid = f"C{100000 + k}"
        clients.append((cid, rng.choice(SOCIETES), pays))
        for j in range(rng.randint(1, 2)):
            cmd = f"{pays}-{rng.randint(10_000_000, 99_999_999)}"
            # chaque client garde au moins une commande en cours ; les commandes annulées servent aux chaînes de transfert
            commandes.append((cmd, cid, pays, "en_cours" if j == 0 else rng.choice(["en_cours", "annulee", "annulee"])))
        for _ in range(rng.randint(1, 4)):
            inv = f"INV-{rng.randint(2025, 2026)}-{rng.randint(10000, 99999)}"
            mt = round(rng.uniform(300, 18000), 2)
            factures.append((inv, cid, mt, "EUR", (debut - timedelta(days=rng.randint(10, 120))).date().isoformat()))
    con.executemany("INSERT INTO clients VALUES (?,?,?)", clients)
    con.executemany("INSERT INTO commandes VALUES (?,?,?,?)", commandes)
    con.executemany("INSERT INTO factures VALUES (?,?,?,?,?)", factures)
    con.commit()
    cmd_par_client: dict[str, list[str]] = {}
    en_cours = {cmd for cmd, _, _, st in commandes if st == "en_cours"}
    for cmd, cid, _, _ in commandes:
        cmd_par_client.setdefault(cid, []).append(cmd)
    fac_par_client: dict[str, list] = {}
    for inv, cid, mt, dev, ech in factures:
        fac_par_client.setdefault(cid, []).append((inv, mt, dev, ech))

    # --- e-mails --------------------------------------------------------------
    emails, verites = [], []
    for i in range(n):
        eid = f"M{i + 1:05d}"
        cid, nom, pays = rng.choice(clients)
        langue = PAYS[pays]["langue"]
        semaine = rng.randint(1, 8)
        recu = debut + timedelta(days=(semaine - 1) * 7 + rng.randint(0, 4), hours=rng.randint(7, 18))
        prenom = rng.choice(PRENOMS)
        expediteur = f"{prenom.lower()}@{nom.lower().replace(' ', '-')}.example"

        if rng.random() < 0.06:  # hors périmètre
            sujet, corps = rng.choice(HORS_PERIMETRE)
            emails.append({"email_id": eid, "pays": pays, "langue": langue, "semaine": semaine, "recu_le": recu.isoformat(),
                           "expediteur": expediteur, "objet": sujet, "corps": corps, "pieces_jointes": [], "cas_limite": "hors_perimetre"})
            verites.append({"email_id": eid, "type_demande": "hors_perimetre", "customer_id": None, "order_no": None,
                            "invoice_no": None, "montant": None, "devise": None, "urgence": "basse", "a_creer": False})
            continue

        t = rng.choice(TYPES)
        actives = [c for c in cmd_par_client[cid] if c in en_cours] or cmd_par_client[cid]
        cmd = rng.choice(actives)
        inv, mt, dev, ech = rng.choice(fac_par_client[cid])
        if t == "demande_devis":
            mt = round(rng.choice([800, 1200, 2500, 4000, 6500]) * rng.uniform(0.8, 1.2), -1)
        if t == "avarie_marchandise":
            mt = round(mt * rng.uniform(0.1, 0.6), 2)
        soc = rng.choice(SOCIETES)
        ctx = dict(cmd=cmd, soc=soc, inv=inv, cli=cid, mt=fmt_montant(mt, langue), ech=ech, prenom=prenom, adr=rng.choice(ADRESSES))
        sujet = SUJETS[t][langue].format(**ctx)
        corps = CORPS[t][langue].format(**ctx)
        pj: list[str] = []
        cas = None
        urgence = "haute" if t in ("reclamation_livraison", "avarie_marchandise") else "normale"
        attendu = {"email_id": eid, "type_demande": t, "customer_id": cid,
                   "order_no": cmd if t != "demande_devis" else None,
                   "invoice_no": inv if t in ("avarie_marchandise", "question_facture") else None,
                   "montant": mt if t in ("avarie_marchandise", "question_facture", "demande_devis") else None,
                   "devise": "EUR" if t in ("avarie_marchandise", "question_facture", "demande_devis") else None,
                   "urgence": urgence, "a_creer": True}

        r = rng.random()  # cas limites (environ 40 % des e-mails)
        if r < 0.08:
            cas = "fautes_de_frappe"; corps = typo(corps, rng); sujet = typo(sujet, rng)
        elif r < 0.14:
            cas = "champ_manquant"; corps = retirer_client(corps, cid)   # le client reste identifiable par la commande ou la facture
        elif r < 0.19:
            cas = "chaine_transfert"
            ancienne = f"{pays}-{rng.randint(10_000_000, 99_999_999)}"
            corps = (f"FW: {sujet}\n\n---------- Message transféré ----------\nDe : {expediteur}\nDate : {recu.date()}\n\n" + corps
                     + "\n\n---------- Message d'origine ----------\nObjet : RE: Relance\nMerci de traiter rapidement. Ancienne commande : "
                     f"{ancienne} (annulée).")
            sujet = "FW: " + sujet
        elif r < 0.23:
            cas = "piece_jointe_seule"
            corps = {"fr": "Bonjour, voir pièce jointe.\n" + prenom, "es": "Hola, ver adjunto.\n" + prenom, "nl": "Hallo, zie bijlage.\n" + prenom}[langue]
            pj = [f"{inv}.pdf"]
            attendu["order_no"] = None  # pas dans le texte : à retrouver via la facture ou à escalader
        elif r < 0.27:
            cas = "montant_ambigu"
            corps = corps.replace(f"{ctx['mt']} EUR", f"{ctx['mt']} EUR (dont {fmt_montant(round(mt * 0.2, 2), langue)} EUR de TVA)") \
                        .replace(f"€ {ctx['mt']}", f"€ {ctx['mt']} (waarvan € {fmt_montant(round(mt * 0.2, 2), langue)} btw)")
        elif r < 0.35:
            cas = "ps_ambigu"; corps = corps + PS_AMBIGU[langue]
        elif r < 0.38:
            cas = "doublon"  # même e-mail renvoyé deux heures plus tard : le second ne doit pas créer de dossier
            emails.append({"email_id": eid, "pays": pays, "langue": langue, "semaine": semaine, "recu_le": recu.isoformat(),
                           "expediteur": expediteur, "objet": sujet, "corps": corps, "pieces_jointes": pj, "cas_limite": None})
            verites.append(dict(attendu))
            eid = f"M{i + 1:05d}D"
            attendu = dict(attendu, email_id=eid, a_creer=False, doublon_de=f"M{i + 1:05d}")
            recu = recu + timedelta(hours=2)
            sujet = "RE: " + sujet

        emails.append({"email_id": eid, "pays": pays, "langue": langue, "semaine": semaine, "recu_le": recu.isoformat(),
                       "expediteur": expediteur, "objet": sujet, "corps": corps, "pieces_jointes": pj, "cas_limite": cas})
        verites.append(attendu)

    with open(ICI / "emails.jsonl", "w", encoding="utf-8") as f:
        for e in emails:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    with open(ICI / "ground_truth.jsonl", "w", encoding="utf-8") as f:
        for v in verites:
            f.write(json.dumps(v, ensure_ascii=False) + "\n")
    print(f"{len(emails)} e-mails, {len(clients)} clients, {len(commandes)} commandes, {len(factures)} factures")
    print("cas limites :", dict(Counter(e["cas_limite"] for e in emails)))
    print("pays :", dict(Counter(e["pays"] for e in emails)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=600)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    main(a.n, a.seed)
