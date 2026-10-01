# Architecture EduPaie

## 1. Architecture en couches

L'application suit une architecture en **3 couches strictes** :

| Couche | Dossier | Responsabilité | Interdit |
|---|---|---|---|
| **Accès aux données** | `repositories/` | Requêtes SQL paramétrées (`?`), CRUD pur | Logique métier, import PySide6 |
| **Logique métier** | `services/` | Validations, calcul du solde/statut, génération du n° de reçu, transactions | SQL, import PySide6 |
| **Interface** | `ui/` | Fenêtres, widgets, signaux/slots, affichage | SQL, calculs métier |

Chaque couche **ne connaît que la couche immédiatement en dessous**.

## 2. Structure des fichiers

```
edupaie/
├── main.py                      # Point d'entrée, excepthook global
├── requirements.txt
├── README.md
├── data/
│   └── edupaie.db               # Base de test livrée
├── db/
│   ├── __init__.py
│   ├── schema.sql               # Script DDL (généré depuis le MLD)
│   ├── connection.py            # Connexion SQLite, PRAGMA foreign_keys
│   ├── init_db.py               # Création des tables si absentes
│   └── seed.py                  # Jeu de données de test (≥15 élèves)
├── repositories/
│   ├── __init__.py
│   ├── eleve_repository.py      # CRUD élève
│   └── paiement_repository.py   # CRUD paiement
├── services/
│   ├── __init__.py
│   ├── eleve_service.py         # Validations élève, calcul solde/statut
│   ├── paiement_service.py      # Validation paiement, enregistrement transactionnel
│   └── recu_service.py          # Génération du numéro de reçu
├── ui/
│   ├── __init__.py
│   ├── main_window.py           # Fenêtre principale + navigation latérale
│   ├── eleve_list.py            # Liste élèves (QTableWidget + recherche + filtre)
│   ├── eleve_form.py            # Formulaire ajout/modification élève
│   ├── eleve_fiche.py           # Fiche élève (infos + solde + historique)
│   ├── paiement_dialog.py       # Dialogue enregistrement paiement
│   ├── dashboard.py             # Tableau de bord (indicateurs + liste filtrée)
│   └── utils.py                 # Helpers UI : formatage FCFA, couleurs statut
├── receipts/
│   ├── __init__.py
│   └── pdf_generator.py         # Génération PDF (reportlab)
├── utils/
│   ├── __init__.py
│   └── paths.py                 # resource_path() pour PyInstaller
└── docs/
    ├── mcd.mmd
    ├── mld.mmd
    ├── architecture.md
    ├── documentation.md
    └── manuel_utilisateur.md
```

## 3. Format du numéro de reçu

```
REC-AAAA-NNNN
```

- `REC` : préfixe fixe
- `AAAA` : année calendaire du paiement (ex: `2026`)
- `NNNN` : compteur séquentiel sur 4 chiffres, remis à `0001` chaque année

**Algorithme** (dans une transaction) :
1. `SELECT MAX(numero_recu) FROM paiement WHERE numero_recu LIKE 'REC-AAAA-%'`
2. Si NULL → `REC-AAAA-0001`
3. Sinon → extraire NNNN, incrémenter, formater sur 4 chiffres

## 4. Calcul du solde et du statut

```
solde = total_du − somme(paiements)

Soldé             → solde = 0
Partiellement payé → solde > 0 et au moins un paiement
Non payé          → aucun paiement
```

Calculés par `eleve_service.py`, jamais par l'UI ni par le SQL.

## 5. Transaction d'enregistrement de paiement

1. Valider le montant (> 0 et ≤ solde restant)
2. BEGIN TRANSACTION
3. Générer le numéro de reçu (dans la même transaction)
4. Calculer le solde après paiement
5. INSERT paiement
6. COMMIT (ou ROLLBACK en cas d'erreur)

## 6. Reçu PDF

Contenu : numéro de reçu, infos élève (nom, prénom, classe, année), montant payé, date, mode de paiement, solde restant.

Stockage : `Documents/EduPaie/Recus/REC-AAAA-NNNN.pdf`

Réimpression : réouverture du PDF existant ou régénération identique depuis les données en base.

## 7. Gestion des erreurs

- `sys.excepthook` global dans `main.py` (QMessageBox + log)
- Validations UI : champs vides, format basique
- Validations service : règles métier (montant, solde, suppression)
- Contraintes SQL : dernier filet de sécurité (UNIQUE, CHECK, FK)

## 8. PyInstaller

- `utils/paths.py` gère `sys._MEIPASS` pour les ressources embarquées
- Base de données copiée vers `%APPDATA%/EduPaie/` au premier lancement
- Reçus PDF dans `Documents/EduPaie/Recus/`

## 9. Formatage

| Élément | Format | Exemple |
|---|---|---|
| Montants | Séparateur de milliers + ` FCFA` | `250 000 FCFA` |
| Dates affichage | `JJ/MM/AAAA` | `15/09/2025` |
| Dates base | `YYYY-MM-DD` | `2025-09-15` |
| Statuts | 🟢 Soldé, 🟡 Partiellement payé, 🔴 Non payé | — |
