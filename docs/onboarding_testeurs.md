# Guide d'intégration des testeurs et des équipes pays

Ce guide permet à un nouveau testeur (équipe pays, support, product) de valider des dossiers et de remonter des bugs exploitables en moins d'une demi-journée.

## 1. Installer et lancer (10 min)

```bash
git clone https://github.com/Teede-N/email-to-case-eval && cd email-to-case-eval
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m e2c.cli run          # valide le corpus, produit les KPI et la liste des bugs
PYTHONPATH=src streamlit run app.py           # console de validation
```

Pour tester l'API : `PYTHONPATH=src uvicorn e2c.api:app --reload`, puis importer `postman/email_to_case.postman_collection.json` dans Postman (variable `base_url` = `http://localhost:8000`).

## 2. Valider un dossier (approche « humain sur la boucle »)

1. Ouvrir l'onglet **File de revue humaine** de la console et filtrer sur votre pays.
2. Pour chaque e-mail : lire l'objet et le corps, puis comparer la colonne « Extrait par l'agent » à « Attendu (référence) » et aux anomalies des systèmes sources.
3. Décider : **Valider** (le dossier est juste), **Corriger et créer** (un champ est faux : noter lequel), ou laisser en escalade si le dossier est douteux.
4. Si l'écart est nouveau, créer un bug (section 3). S'il correspond à un bug existant (`docs/bugs.md`), ajouter l'identifiant de l'e-mail en commentaire du bug.

Règle d'or : **un champ non trouvé vaut mieux qu'un champ inventé**. Un agent qui laisse `order_no` vide et escalade fait son travail ; un agent qui met la commande d'un autre client ne le fait pas.

## 3. Rédiger un bug exploitable

Modèle (copier dans Jira, type *Bug*, composant *E-mail → dossier*) :

```
Titre      : [FR] order_no incorrect sur chaîne de transfert
Contexte   : agent regles, corpus S8, e-mail M00001 (fr, FR), cas chaine_transfert
Étapes     : 1. PYTHONPATH=src python -m e2c.cli one M00001
             2. comparer dossier.order_no et attendu.order_no
Attendu    : order_no = FR-78387461 (commande en cours du message principal)
Réel       : order_no = FR-26937148 (ancienne commande annulée citée dans le message d'origine)
Fréquence  : 35 e-mails sur 619 (5,7 %), tous pays
Gravité    : Moyenne (dossier créé, correction humaine nécessaire) – Majeure si action automatique en aval
Pièces     : extrait de data/validations.jsonl, capture de la console
```

Un bug sans étapes de reproduction ni exemple d'e-mail est renvoyé au testeur.

## 4. Lire le rapport KPI hebdomadaire

`reports/kpi_hebdo.md` donne les cinq KPI suivis, la décision go / no-go par pays et les cas limites où l'agent échoue. Les définitions sont dans [kpi.md](kpi.md). Un testeur pays doit regarder en priorité : le taux d'échec (sa charge de revue), la précision par champ (les risques financiers) et les faux dossiers.

## 5. Rituels agiles où le testeur intervient

| Rituel | Rôle du testeur | Livrable |
|---|---|---|
| Refinement (grooming) | relire les critères d'acceptation Gherkin, signaler les cas pays manquants | commentaires sur la story |
| Sprint planning | estimer l'effort de test par story | cases de test créées dans Jira |
| Daily / Kanban | déplacer ses cartes de test, signaler les blocages | tableau à jour |
| Sprint review | présenter les KPI de la semaine et les bugs majeurs | 3 chiffres, 3 bugs |
| Rétrospective | proposer une amélioration du processus de validation | une action suivie |

## 6. Ajouter un cas de test

Écrire le scénario en Gherkin dans `features/email_to_case.feature` (Étant donné / Quand / Alors), ajouter si besoin la phrase correspondante dans `tests/test_features.py`, puis lancer `pytest -q`. Un scénario rouge sur un comportement attendu est une story de correction, pas un test à supprimer.
