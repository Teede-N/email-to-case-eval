# Bugs structurés issus de la validation

Un bug par motif d'écart, avec des exemples reproductibles tirés du corpus. Gravité : Majeure = dossier faux ou manquant, Moyenne = correction humaine nécessaire, Mineure = escalade justifiée mais perfectible.

## BUG-001 · order_no incorrect – cas chaine_transfert

- **Gravité** : Mineure · **Occurrences** : 29 · **Pays** : BE, ES, FR, NL
- **Contexte** : agent `regles`, corpus synthétique, semaines 1–8.
- **Étapes pour reproduire** :
    1. `PYTHONPATH=src python -m e2c.cli run`
    2. Ouvrir `data/validations.jsonl`, filtrer `email_id` ∈ {M00001, M00024, M00060}.
    3. Comparer le dossier produit à `data/ground_truth.jsonl`.

**Exemple M00001** (FR, fr, S8) – objet : _FW: Modification de la commande FR-78387461 – adresse de livraison_

| | Attendu | Réel |
|---|---|---|
| Type | modification_commande | modification_commande |
| Dossier à créer | True | True |
| order_no | 'FR-78387461' | 'FR-26937148' |
| Anomalies systèmes sources | – | commande_inconnue_ou_autre_client |

**Exemple M00024** (NL, nl, S3) – objet : _FW: Vraag over factuur INV-2025-49529_

| | Attendu | Réel |
|---|---|---|
| Type | question_facture | question_facture |
| Dossier à créer | True | True |
| order_no | 'NL-36619372' | 'NL-38748452' |
| Anomalies systèmes sources | – | commande_inconnue_ou_autre_client |

**Exemple M00060** (NL, nl, S8) – objet : _FW: Vraag over factuur INV-2025-84177_

| | Attendu | Réel |
|---|---|---|
| Type | question_facture | question_facture |
| Dossier à créer | True | True |
| order_no | 'NL-63238057' | 'NL-92745294' |
| Anomalies systèmes sources | – | commande_inconnue_ou_autre_client |


## BUG-002 · montant incorrect – cas nominal

- **Gravité** : Moyenne · **Occurrences** : 18 · **Pays** : NL
- **Contexte** : agent `regles`, corpus synthétique, semaines 1–8.
- **Étapes pour reproduire** :
    1. `PYTHONPATH=src python -m e2c.cli run`
    2. Ouvrir `data/validations.jsonl`, filtrer `email_id` ∈ {M00012, M00131, M00148}.
    3. Comparer le dossier produit à `data/ground_truth.jsonl`.

**Exemple M00012** (NL, nl, S1) – objet : _Beschadigde goederen – zending NL-98955314, factuur INV-2025-84000_

| | Attendu | Réel |
|---|---|---|
| Type | avarie_marchandise | avarie_marchandise |
| Dossier à créer | True | True |
| montant | 1038.33 | 3932.14 |

**Exemple M00131** (NL, nl, S6) – objet : _Beschadigde goederen – zending NL-75679047, factuur INV-2026-68287_

| | Attendu | Réel |
|---|---|---|
| Type | avarie_marchandise | avarie_marchandise |
| Dossier à créer | True | True |
| montant | 8609.0 | 17124.83 |

**Exemple M00148** (NL, nl, S2) – objet : _Beschadigde goederen – zending NL-75679047, factuur INV-2026-68287_

| | Attendu | Réel |
|---|---|---|
| Type | avarie_marchandise | avarie_marchandise |
| Dossier à créer | True | True |
| montant | 2450.67 | 17124.83 |


## BUG-003 · devise, invoice_no, montant, type_demande incorrect – cas ps_ambigu

- **Gravité** : Moyenne · **Occurrences** : 12 · **Pays** : BE, ES, FR, NL
- **Contexte** : agent `regles`, corpus synthétique, semaines 2–8.
- **Étapes pour reproduire** :
    1. `PYTHONPATH=src python -m e2c.cli run`
    2. Ouvrir `data/validations.jsonl`, filtrer `email_id` ∈ {M00029, M00061, M00082}.
    3. Comparer le dossier produit à `data/ground_truth.jsonl`.

**Exemple M00029** (ES, es, S8) – objet : _Consulta sobre la factura INV-2026-28726_

| | Attendu | Réel |
|---|---|---|
| Type | question_facture | modification_commande |
| Dossier à créer | True | True |
| type_demande | 'question_facture' | 'modification_commande' |
| invoice_no | 'INV-2026-28726' | None |
| montant | 4988.38 | None |
| devise | 'EUR' | None |

**Exemple M00061** (ES, es, S6) – objet : _Consulta sobre la factura INV-2025-21003_

| | Attendu | Réel |
|---|---|---|
| Type | question_facture | modification_commande |
| Dossier à créer | True | True |
| type_demande | 'question_facture' | 'modification_commande' |
| invoice_no | 'INV-2025-21003' | None |
| montant | 11676.67 | None |
| devise | 'EUR' | None |

**Exemple M00082** (FR, fr, S2) – objet : _Question sur la facture INV-2025-60940_

| | Attendu | Réel |
|---|---|---|
| Type | question_facture | modification_commande |
| Dossier à créer | True | True |
| type_demande | 'question_facture' | 'modification_commande' |
| invoice_no | 'INV-2025-60940' | None |
| montant | 8329.49 | None |
| devise | 'EUR' | None |


## BUG-004 · order_no incorrect – cas piece_jointe_seule

- **Gravité** : Moyenne · **Occurrences** : 7 · **Pays** : BE, ES, FR, NL
- **Contexte** : agent `regles`, corpus synthétique, semaines 1–8.
- **Étapes pour reproduire** :
    1. `PYTHONPATH=src python -m e2c.cli run`
    2. Ouvrir `data/validations.jsonl`, filtrer `email_id` ∈ {M00171, M00201, M00368}.
    3. Comparer le dossier produit à `data/ground_truth.jsonl`.

**Exemple M00171** (FR, fr, S1) – objet : _Réclamation – commande FR-50071487 non livrée (Textil Ramos)_

| | Attendu | Réel |
|---|---|---|
| Type | reclamation_livraison | reclamation_livraison |
| Dossier à créer | True | True |
| order_no | None | 'FR-50071487' |

**Exemple M00201** (ES, es, S5) – objet : _Reclamación – pedido ES-73481797 no entregado (Pinturas Vega)_

| | Attendu | Réel |
|---|---|---|
| Type | reclamation_livraison | reclamation_livraison |
| Dossier à créer | True | True |
| order_no | None | 'ES-73481797' |

**Exemple M00368** (FR, fr, S2) – objet : _Modification de la commande FR-16818112 – adresse de livraison_

| | Attendu | Réel |
|---|---|---|
| Type | modification_commande | modification_commande |
| Dossier à créer | True | True |
| order_no | None | 'FR-16818112' |


## BUG-005 · customer_id incorrect – cas champ_manquant

- **Gravité** : Mineure · **Occurrences** : 5 · **Pays** : ES, FR, NL
- **Contexte** : agent `regles`, corpus synthétique, semaines 3–8.
- **Étapes pour reproduire** :
    1. `PYTHONPATH=src python -m e2c.cli run`
    2. Ouvrir `data/validations.jsonl`, filtrer `email_id` ∈ {M00054, M00132, M00273}.
    3. Comparer le dossier produit à `data/ground_truth.jsonl`.

**Exemple M00054** (FR, fr, S6) – objet : _Demande de devis – transport palettes vers Cerámica Soler_

| | Attendu | Réel |
|---|---|---|
| Type | demande_devis | demande_devis |
| Dossier à créer | True | True |
| customer_id | 'C100026' | None |
| Anomalies systèmes sources | – | aucun_identifiant |

**Exemple M00132** (NL, nl, S3) – objet : _Offerteaanvraag – pallettransport naar Lumière Cosmétiques_

| | Attendu | Réel |
|---|---|---|
| Type | demande_devis | demande_devis |
| Dossier à créer | True | True |
| customer_id | 'C100076' | None |
| Anomalies systèmes sources | – | aucun_identifiant |

**Exemple M00273** (ES, es, S8) – objet : _Solicitud de presupuesto – transporte de palés a Brabant Fietsen_

| | Attendu | Réel |
|---|---|---|
| Type | demande_devis | demande_devis |
| Dossier à créer | True | True |
| customer_id | 'C100071' | None |
| Anomalies systèmes sources | – | aucun_identifiant |


## BUG-006 · montant incorrect – cas champ_manquant

- **Gravité** : Moyenne · **Occurrences** : 4 · **Pays** : NL
- **Contexte** : agent `regles`, corpus synthétique, semaines 1–7.
- **Étapes pour reproduire** :
    1. `PYTHONPATH=src python -m e2c.cli run`
    2. Ouvrir `data/validations.jsonl`, filtrer `email_id` ∈ {M00074, M00208, M00295}.
    3. Comparer le dossier produit à `data/ground_truth.jsonl`.

**Exemple M00074** (NL, nl, S1) – objet : _Beschadigde goederen – zending NL-59555330, factuur INV-2025-56898_

| | Attendu | Réel |
|---|---|---|
| Type | avarie_marchandise | avarie_marchandise |
| Dossier à créer | True | True |
| montant | 2063.4 | 4018.35 |

**Exemple M00208** (NL, nl, S4) – objet : _Beschadigde goederen – zending NL-17532195, factuur INV-2026-91226_

| | Attendu | Réel |
|---|---|---|
| Type | avarie_marchandise | avarie_marchandise |
| Dossier à créer | True | True |
| montant | 6672.72 | 12391.48 |

**Exemple M00295** (NL, nl, S7) – objet : _Beschadigde goederen – zending NL-75998319, factuur INV-2026-63523_

| | Attendu | Réel |
|---|---|---|
| Type | avarie_marchandise | avarie_marchandise |
| Dossier à créer | True | True |
| montant | 1272.68 | 6199.56 |


## BUG-007 · devise, montant incorrect – cas piece_jointe_seule

- **Gravité** : Moyenne · **Occurrences** : 3 · **Pays** : ES, NL
- **Contexte** : agent `regles`, corpus synthétique, semaines 1–6.
- **Étapes pour reproduire** :
    1. `PYTHONPATH=src python -m e2c.cli run`
    2. Ouvrir `data/validations.jsonl`, filtrer `email_id` ∈ {M00198, M00422, M00590}.
    3. Comparer le dossier produit à `data/ground_truth.jsonl`.

**Exemple M00198** (NL, nl, S1) – objet : _Offerteaanvraag – pallettransport naar Boulangeries Martin_

| | Attendu | Réel |
|---|---|---|
| Type | demande_devis | demande_devis |
| Dossier à créer | True | True |
| montant | 4560.0 | None |
| devise | 'EUR' | None |

**Exemple M00422** (ES, es, S2) – objet : _Solicitud de presupuesto – transporte de palés a Iberia Frutas_

| | Attendu | Réel |
|---|---|---|
| Type | demande_devis | demande_devis |
| Dossier à créer | True | True |
| montant | 2230.0 | None |
| devise | 'EUR' | None |

**Exemple M00590** (ES, es, S6) – objet : _Solicitud de presupuesto – transporte de palés a Van Dijk Interieur_

| | Attendu | Réel |
|---|---|---|
| Type | demande_devis | demande_devis |
| Dossier à créer | True | True |
| montant | 680.0 | None |
| devise | 'EUR' | None |


## BUG-008 · montant incorrect – cas fautes_de_frappe

- **Gravité** : Moyenne · **Occurrences** : 2 · **Pays** : NL
- **Contexte** : agent `regles`, corpus synthétique, semaines 6–6.
- **Étapes pour reproduire** :
    1. `PYTHONPATH=src python -m e2c.cli run`
    2. Ouvrir `data/validations.jsonl`, filtrer `email_id` ∈ {M00056, M00500}.
    3. Comparer le dossier produit à `data/ground_truth.jsonl`.

**Exemple M00056** (NL, nl, S6) – objet : _Beschadigde goederen – zending NL-77898694, factuur INV-2026-90173_

| | Attendu | Réel |
|---|---|---|
| Type | avarie_marchandise | avarie_marchandise |
| Dossier à créer | True | True |
| montant | 5906.05 | 17714.2 |

**Exemple M00500** (NL, nl, S6) – objet : _Beschadidge goederen – zending NL-75679047, factuur INV-2026-17936_

| | Attendu | Réel |
|---|---|---|
| Type | avarie_marchandise | avarie_marchandise |
| Dossier à créer | True | True |
| montant | 4205.31 | 7347.07 |


## BUG-009 · montant incorrect – cas ps_ambigu

- **Gravité** : Moyenne · **Occurrences** : 2 · **Pays** : NL
- **Contexte** : agent `regles`, corpus synthétique, semaines 3–6.
- **Étapes pour reproduire** :
    1. `PYTHONPATH=src python -m e2c.cli run`
    2. Ouvrir `data/validations.jsonl`, filtrer `email_id` ∈ {M00112, M00519}.
    3. Comparer le dossier produit à `data/ground_truth.jsonl`.

**Exemple M00112** (NL, nl, S3) – objet : _Beschadigde goederen – zending NL-98955314, factuur INV-2025-84000_

| | Attendu | Réel |
|---|---|---|
| Type | avarie_marchandise | avarie_marchandise |
| Dossier à créer | True | True |
| montant | 742.46 | 3932.14 |

**Exemple M00519** (NL, nl, S6) – objet : _Beschadigde goederen – zending NL-57683626, factuur INV-2025-99733_

| | Attendu | Réel |
|---|---|---|
| Type | avarie_marchandise | avarie_marchandise |
| Dossier à créer | True | True |
| montant | 2505.19 | 6039.8 |


## BUG-010 · montant incorrect – cas montant_ambigu

- **Gravité** : Moyenne · **Occurrences** : 2 · **Pays** : NL
- **Contexte** : agent `regles`, corpus synthétique, semaines 3–3.
- **Étapes pour reproduire** :
    1. `PYTHONPATH=src python -m e2c.cli run`
    2. Ouvrir `data/validations.jsonl`, filtrer `email_id` ∈ {M00203, M00507}.
    3. Comparer le dossier produit à `data/ground_truth.jsonl`.

**Exemple M00203** (NL, nl, S3) – objet : _Beschadigde goederen – zending NL-65625330, factuur INV-2025-23970_

| | Attendu | Réel |
|---|---|---|
| Type | avarie_marchandise | avarie_marchandise |
| Dossier à créer | True | True |
| montant | 6955.19 | 14078.04 |

**Exemple M00507** (NL, nl, S3) – objet : _Beschadigde goederen – zending NL-65625330, factuur INV-2025-23970_

| | Attendu | Réel |
|---|---|---|
| Type | avarie_marchandise | avarie_marchandise |
| Dossier à créer | True | True |
| montant | 6407.31 | 14078.04 |


## BUG-011 · devise, montant, type_demande incorrect – cas ps_ambigu

- **Gravité** : Moyenne · **Occurrences** : 2 · **Pays** : ES
- **Contexte** : agent `regles`, corpus synthétique, semaines 2–4.
- **Étapes pour reproduire** :
    1. `PYTHONPATH=src python -m e2c.cli run`
    2. Ouvrir `data/validations.jsonl`, filtrer `email_id` ∈ {M00343, M00566}.
    3. Comparer le dossier produit à `data/ground_truth.jsonl`.

**Exemple M00343** (ES, es, S2) – objet : _Solicitud de presupuesto – transporte de palés a Maison Lefèvre_

| | Attendu | Réel |
|---|---|---|
| Type | demande_devis | modification_commande |
| Dossier à créer | True | True |
| type_demande | 'demande_devis' | 'modification_commande' |
| montant | 2440.0 | None |
| devise | 'EUR' | None |

**Exemple M00566** (ES, es, S4) – objet : _Solicitud de presupuesto – transporte de palés a Maison Lefèvre_

| | Attendu | Réel |
|---|---|---|
| Type | demande_devis | modification_commande |
| Dossier à créer | True | True |
| type_demande | 'demande_devis' | 'modification_commande' |
| montant | 3640.0 | None |
| devise | 'EUR' | None |


## BUG-012 · montant, order_no incorrect – cas piece_jointe_seule

- **Gravité** : Moyenne · **Occurrences** : 1 · **Pays** : NL
- **Contexte** : agent `regles`, corpus synthétique, semaines 7–7.
- **Étapes pour reproduire** :
    1. `PYTHONPATH=src python -m e2c.cli run`
    2. Ouvrir `data/validations.jsonl`, filtrer `email_id` ∈ {M00122}.
    3. Comparer le dossier produit à `data/ground_truth.jsonl`.

**Exemple M00122** (NL, nl, S7) – objet : _Beschadigde goederen – zending NL-59555330, factuur INV-2025-56898_

| | Attendu | Réel |
|---|---|---|
| Type | avarie_marchandise | avarie_marchandise |
| Dossier à créer | True | True |
| order_no | None | 'NL-59555330' |
| montant | 1183.07 | 4018.35 |


## BUG-013 · Dossier manqué (nominal)

- **Gravité** : Majeure · **Occurrences** : 1 · **Pays** : FR
- **Contexte** : agent `regles`, corpus synthétique, semaines 5–5.
- **Étapes pour reproduire** :
    1. `PYTHONPATH=src python -m e2c.cli run`
    2. Ouvrir `data/validations.jsonl`, filtrer `email_id` ∈ {M00425}.
    3. Comparer le dossier produit à `data/ground_truth.jsonl`.

**Exemple M00425** (FR, fr, S5) – objet : _Avarie à la livraison – commande FR-78387461, facture INV-2025-99192_

| | Attendu | Réel |
|---|---|---|
| Type | avarie_marchandise | avarie_marchandise |
| Dossier à créer | True | False |

