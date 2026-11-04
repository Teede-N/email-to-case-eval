# Rapport d'évaluation go / no-go – déploiement Pays-Bas (NL)

**Décision proposée : NO-GO, à réévaluer en S10** après livraison de E2C-10 (montants « € 1.234,56 ») et E2C-9 (chaînes de transfert).

Base : 124 e-mails NL validés sur 8 semaines (S1–S8), agent `regles`, seuils définis dans [kpi.md](kpi.md). Chiffres issus de `reports/kpi_hebdo.md` (régénérable avec `python -m e2c.cli run`).

## Résultat par critère

| Critère | Seuil | NL | Statut |
|---|---|---|---|
| Taux de conversion | ≥ 70 % | 67,5 % | **Écart de 2,5 pts** |
| Précision d'extraction | ≥ 95 % | 92,4 % | **Écart de 2,6 pts** |
| Précision de classification | ≥ 95 % | 99,2 % | OK |
| Taux d'échec | ≤ 15 % | 5,8 % | OK |
| Faux dossiers | ≤ 2 % | 0,0 % | OK |

Les deux critères en écart ont la même cause : le champ `montant` n'est juste qu'à **63 %** aux Pays-Bas, contre 97 % en France. Les clients néerlandais écrivent le symbole avant le montant (« € 1.234,56 ») ; l'agent ne le lit pas, puis remplit le montant à partir de la facture dans les systèmes sources, ce qui est faux pour une avarie (montant partiel réclamé ≠ total de la facture).

## Ce qui fonctionne

- Classification à 99,2 % : les mots-clés néerlandais couvrent bien les cinq types de demande.
- Aucun faux dossier : hors périmètre et doublons correctement ignorés.
- Résolution du client via la commande ou la facture : les e-mails sans numéro client sont traités.

## Ce qui bloque

| Bug | Impact NL | Correctif prévu | Story |
|---|---|---|---|
| BUG-002 – montant d'avarie remplacé par le total de la facture | 18 e-mails sur 124 (14,5 %), précision `montant` 63 % | lire « € 1.234,56 » ; ne jamais compléter un montant d'avarie depuis la facturation | E2C-10 |
| BUG-001 – mauvaise commande dans les chaînes de transfert | ~6 % des e-mails, escalade justifiée mais coûteuse | ne lire que le message principal, ignorer les blocs « message d'origine » | E2C-9 |
| BUG-004/007 – information uniquement en pièce jointe | ~2 % des e-mails | OCR hors périmètre ; en attendant, escalade avec la facture pré-identifiée | E2C-8 |

## Conditions de GO

1. Précision `montant` ≥ 95 % et précision d'extraction globale ≥ 95 % sur deux semaines consécutives après E2C-10.
2. Revue humaine de 100 % des escalades pendant les deux premières semaines de production (volume estimé : 6 % des e-mails).
3. Procédure de retour arrière documentée (désactivation de la création automatique, retour à la file manuelle).

## Plan d'actions

- [ ] Livrer E2C-10 (format « € 1.234,56 ») – sprint 12
- [ ] Livrer E2C-9 (chaînes de transfert) – sprint 12
- [ ] Rejouer le banc sur le corpus NL et publier le rapport S10
- [ ] Préparer l'intégration des testeurs NL ([onboarding_testeurs.md](onboarding_testeurs.md))
