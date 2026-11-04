# Définition des KPI de l'agent e-mail → dossier

Les KPI sont calculés chaque semaine par `python -m e2c.cli run` à partir des validations (`data/validations.jsonl`) et publiés dans `reports/kpi_hebdo.md`. Ils sont déclinés **par pays**, **par champ** et **par semaine**.

## Vocabulaire

Un e-mail « à traiter » est un e-mail dont la vérité terrain attend un dossier (`a_creer = true`). Les e-mails hors périmètre et les doublons ne sont pas à traiter : le bon comportement est de les ignorer.

Chaque e-mail reçoit un **verdict de validation** :

| Verdict | Sens | Qui agit |
|---|---|---|
| `auto_ok` | dossier créé automatiquement, tous les champs corrects | personne |
| `corrige` | dossier créé, mais un validateur a dû corriger au moins un champ | humain, après coup |
| `escalade` | création bloquée avant action : erreur technique de l'agent ou incohérence avec les systèmes sources | humain, avant action |
| `faux_dossier` | dossier créé alors qu'il ne fallait pas (hors périmètre, doublon) | humain, nettoyage |
| `dossier_manque` | e-mail à traiter sans dossier | humain, rattrapage |
| `ignore_ok` | e-mail à ignorer correctement ignoré | personne |

## Formules

| KPI | Formule | Seuil go / no-go |
|---|---|---|
| Taux de conversion | `auto_ok / à traiter` | ≥ 70 % |
| Précision d'extraction | champs corrects / champs évalués, sur les e-mails à traiter (un champ attendu vide et prédit vide n'est pas évalué) | ≥ 95 % |
| Précision de classification | type de demande correct / tous les e-mails | ≥ 95 % |
| Taux d'échec | `escalade` ou erreur de trace / à traiter | ≤ 15 % |
| Faux dossiers | `faux_dossier` / tous les e-mails | ≤ 2 % |
| Dossiers manqués | `dossier_manque` / à traiter | suivi, pas de seuil |
| Latence médiane | médiane de `trace.duree_ms` | suivi |

La précision par champ est publiée pour : `customer_id`, `order_no`, `invoice_no`, `montant`, `devise`, `urgence`, `type_demande`.

## Pourquoi ces seuils

Le taux de conversion mesure le gain réel pour les équipes (un dossier `corrige` coûte presque autant qu'une saisie). La précision d'extraction protège le client final : un montant ou une commande faux sur une avarie a des conséquences financières et commerciales, d'où un seuil élevé. Le taux d'échec borne la charge de revue humaine. Les faux dossiers sont presque inacceptables parce qu'ils déclenchent des actions sur des dossiers inexistants.

## Signaux disponibles en production (sans vérité terrain)

La validation « humain sur la boucle » s'appuie d'abord sur les **systèmes sources** : client inconnu, commande inconnue ou appartenant à un autre client, commande annulée, facture inconnue, montant différent de la facturation, aucun identifiant. Ces anomalies routent un dossier vers un validateur sans connaître la bonne réponse. La vérité terrain n'est utilisée que pour le banc d'évaluation et le calcul hebdomadaire des KPI sur l'échantillon validé.

## Analyse des traces

Chaque dossier porte une trace : moteur, durée, étapes (classification, extraction, outils appelés, doublon, escalade), tokens, motif d'échec (`timeout`, `json_invalide`, `exception`, `aucun_champ`). Les motifs d'échec sont agrégés dans le rapport ; les étapes servent à reproduire un cas dans la console de validation.
