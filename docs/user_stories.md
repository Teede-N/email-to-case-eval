# User stories (méthode INVEST) et critères d'acceptation

Chaque story est **I**ndépendante, **N**égociable, **V**aleur pour l'utilisateur, **E**stimable, **S**mall, **T**estable. Les critères d'acceptation sont écrits en Gherkin et exécutés automatiquement dans `features/email_to_case.feature` (pytest-bdd).

## Epic : transformer les e-mails clients en dossiers de service sans ressaisie

| ID | Story | Valeur | Taille | Critères (feature) | Statut |
|---|---|---|---|---|---|
| E2C-1 | En tant que gestionnaire du service client, je veux qu'un e-mail d'avarie complet crée un dossier sans ressaisie, afin de lancer le traitement le jour même. | Suppression de la saisie manuelle (≈ 4 min / e-mail) | S | Scénario 1 | Fait |
| E2C-2 | En tant que gestionnaire, je veux que les e-mails hors périmètre (absence, newsletters, candidatures) ne créent aucun dossier, afin de ne pas polluer la file. | Zéro faux dossier | S | Scénario 2 | Fait |
| E2C-3 | En tant que gestionnaire, je veux qu'un e-mail renvoyé ne crée pas de second dossier, afin d'éviter les doubles traitements. | Pas de double traitement | S | Scénario 3 | Fait |
| E2C-4 | En tant que responsable qualité, je veux qu'une incohérence avec les systèmes sources (commande d'un autre client, facture inconnue) bloque la création et escalade à un humain, afin qu'aucune action ne soit prise sur un mauvais dossier. | Contrôle humain ciblé | M | Scénario 4 | Fait |
| E2C-5 | En tant que gestionnaire, je veux que l'agent retrouve le client à partir de la commande ou de la facture quand le numéro client manque, afin de ne pas escalader inutilement. | Conversion 79 % sur les e-mails incomplets (contre 0 % sans l'outil) | M | Scénario 5 | Fait |
| E2C-6 | En tant qu'équipe pays, je veux que les montants soient lus correctement dans le format local, afin que les avaries soient indemnisées pour le bon montant. | Exactitude financière | S | Plan de scénario 6 | Partiel : format « € 1.234,56 » (NL) non lu, voir E2C-10 |
| E2C-7 | En tant que product owner, je veux un rapport KPI hebdomadaire par pays et par champ, afin de décider des déploiements (go / no-go). | Décision objectivée | M | `reports/kpi_hebdo.md` | Fait |
| E2C-8 | En tant que gestionnaire, je veux qu'un e-mail dont l'information n'est que dans la pièce jointe soit escaladé avec la facture pré-identifiée, afin de gagner du temps à la revue. | Revue plus rapide | M | à écrire | À faire |
| E2C-9 | En tant que gestionnaire, je veux que l'agent ne retienne que la commande du message principal dans une chaîne de transfert, afin d'éviter les dossiers sur d'anciennes commandes annulées. | Correction du BUG-001 (35 e-mails) | M | à écrire | À faire |
| E2C-10 | En tant qu'équipe NL, je veux que les montants écrits « € 1.234,56 » soient lus, afin que le montant d'une avarie ne soit pas remplacé par le total de la facture. | Correction du BUG-002 (18 e-mails NL), condition du GO NL | S | à écrire | À faire |
| E2C-11 | En tant que gestionnaire, je veux qu'un post-scriptum ne change pas le type de demande, afin que les questions de facture ne soient pas classées en modification de commande. | Correction du BUG-003 (ps_ambigu, conversion 64 %) | M | à écrire | À faire |

## Exemple de story détaillée (E2C-4)

**En tant que** responsable qualité
**Je veux** qu'un dossier dont la commande n'appartient pas au client déclaré soit routé vers un contrôle humain
**Afin que** personne n'agisse sur un mauvais dossier.

**Critères d'acceptation (Gherkin)**

```gherkin
Étant donné un e-mail d'avarie mentionnant le client C100001
Et une commande appartenant à un autre client
Quand l'agent traite l'e-mail
Alors la validation signale l'anomalie "commande_inconnue_ou_autre_client"
Et le verdict de validation est "escalade"
```

**Définition de fini** : scénario vert en CI, cas ajouté au corpus, KPI `taux_echec` inchangé sur les e-mails nominaux, motif d'escalade documenté dans `docs/kpi.md`.

## Dépendances entre stories

- E2C-5 dépend de l'accès en lecture aux systèmes sources (E2C-4 fournit le connecteur).
- E2C-9 dépend d'un découpage des chaînes de transfert (nouvelle brique d'ingestion).
- E2C-10 est un correctif de l'analyseur de montants ; il conditionne le GO des Pays-Bas.
- E2C-8 dépend d'un OCR des pièces jointes (hors périmètre de ce dépôt).
