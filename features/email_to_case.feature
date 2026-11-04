# language: fr
Fonctionnalité: Création automatique de dossiers à partir des e-mails clients
  En tant que responsable du service client d'une société de transport
  Je veux que les e-mails clients deviennent des dossiers fiables sans ressaisie
  Afin de réduire l'effort manuel tout en gardant un contrôle humain sur les cas douteux

  Contexte:
    Étant donné que l'agent e-mail → dossier est connecté aux systèmes sources

  Scénario: Un e-mail d'avarie complet crée un dossier sans intervention
    Étant donné un e-mail en "fr" dont l'objet est "Avarie à la livraison – commande FR-12345678, facture INV-2026-11111"
    Et dont le corps mentionne la commande "FR-12345678", le client "C100001" et le montant "1.234,56 EUR"
    Quand l'agent traite l'e-mail
    Alors le type de demande est "avarie_marchandise"
    Et le dossier est créé automatiquement avec l'urgence "haute"
    Et le montant extrait vaut 1234.56 "EUR"

  Scénario: Un e-mail hors périmètre ne crée aucun dossier
    Étant donné un e-mail en "fr" dont l'objet est "Out of office"
    Et dont le corps est "I am currently out of the office."
    Quand l'agent traite l'e-mail
    Alors le type de demande est "hors_perimetre"
    Et aucun dossier n'est créé

  Scénario: Un e-mail renvoyé dans la même semaine est reconnu comme doublon
    Étant donné un e-mail en "fr" dont l'objet est "Demande de devis – transport palettes vers Delta Négoce"
    Et dont le corps est "Bonjour, pouvez-vous nous chiffrer un transport de 12 palettes, budget 2.500,00 EUR ? Client C100001."
    Et que l'agent a déjà traité cet e-mail
    Quand l'agent traite le même e-mail renvoyé avec l'objet préfixé "RE:"
    Alors aucun dossier n'est créé
    Et la trace mentionne "doublon"

  Scénario: Une commande qui n'appartient pas au client déclenche une escalade humaine
    Étant donné un e-mail en "fr" dont l'objet est "Avarie à la livraison – commande FR-12345678, facture INV-2026-11111"
    Et dont le corps mentionne une commande d'un autre client
    Quand l'agent traite l'e-mail
    Alors la validation signale l'anomalie "commande_inconnue_ou_autre_client"
    Et le verdict de validation est "escalade"

  Scénario: Le client absent du texte est retrouvé grâce à la commande
    Étant donné un e-mail en "nl" dont l'objet est "Klacht – zending niet geleverd"
    Et dont le corps mentionne seulement une commande en cours connue
    Quand l'agent traite l'e-mail
    Alors le dossier porte le numéro client propriétaire de cette commande
    Et la trace mentionne "retrouvé via la commande"

  Plan du scénario: Les montants sont lus dans le format de chaque pays
    Étant donné un e-mail en "<langue>" dont l'objet est "Question facture"
    Et dont le corps est "<corps>"
    Quand l'agent traite l'e-mail
    Alors le montant extrait vaut <montant> "<devise>"

    Exemples:
      | langue | corps                                                                       | montant | devise |
      | fr     | Facture INV-2026-30001 de 1.250,50 EUR, client C100001                      | 1250.5  | EUR    |
      | es     | Factura INV-2026-30002 de 2.000,00 EUR, cliente C100002                     | 2000.0  | EUR    |
      | fr     | Facture INV-2026-30003 de 3 100,00 €, client C100003                        | 3100.0  | EUR    |
