# edupaie
# EduPaie — Gestion des paiements scolaires

Application de bureau (Desktop) sous **Python**, **PySide6** et **SQLite3** permettant la gestion complète des frais de scolarité, l'enregistrement des versements échelonnés, le suivi des soldes en temps réel et la génération de reçus numérotés certifiés en PDF.

---

## 📋 Fonctionnalités implémentées

- **F1. Gestion des élèves** : Création, modification, suppression sécurisée (rejet si paiements existants), recherche multi-critères et filtre par classe.
- **F2. Calcul automatique du solde et du statut** : `solde = total_du - somme(paiements)`. Statuts visuels : 🟢 Soldé, 🟡 Partiellement payé, 🔴 Non payé.
- **F3. Enregistrement transactionnel d'un paiement** : Modes acceptés (*Espèces*, *Mobile Money*, *Chèque*, *Virement*). Interdiction absolue de paiement supérieur au solde restant. Transaction ACID unique.
- **F4. Historique des paiements** : Chronologie complète des règlements sur la fiche élève, consultation détaillée et réimpression de reçus.
- **F5. Reçus PDF officiels** : Numérotation séquentielle annuelle `REC-AAAA-NNNN` protégée par contrainte d'unicité, génération avec **ReportLab**, réimpression certifiée à l'identique.
- **F6. Tableau de bord** : Indicateurs financiers clés (élèves inscrits, total encaissé, total restant dû, élèves redevables), taux de recouvrement global et tableau filtrable par statut.

---

## 🛠️ Prérequis

- **Python 3.10 ou supérieur**
- Système d'exploitation : **Windows 10 / 11** (compatible également Linux / macOS)

---

## 🚀 Installation et lancement rapide

### 1. Cloner le dépôt et créer l'environnement virtuel
```bash
git clone <url-du-depot>
cd gestion_ecolage

# Créer l'environnement virtuel
python -m venv .venv

# Activer l'environnement virtuel sous Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# ou sous invite de commande classique (cmd) :
.\.venv\Scripts\activate.bat
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Initialiser la base de données de test
Le script pré-remplit la base avec **18 élèves** dans 4 classes et **25 paiements** variés illustrant les trois statuts :
```bash
python db/seed.py
```

### 4. Lancer l'application
```bash
python main.py
```

---

## 🏛️ Architecture du projet

L'application respecte une séparation stricte en 3 couches indépendantes :

```
edupaie/
├── main.py                      # Point d'entrée de l'application (sys.excepthook)
├── requirements.txt             # Dépendances (PySide6, reportlab, pyinstaller)
├── README.md                    # Guide d'installation et documentation
├── data/
│   └── edupaie.db               # Base de données SQLite de travail
├── db/
│   ├── schema.sql               # Script DDL
│   ├── connection.py            # Connexion SQLite avec PRAGMA foreign_keys = ON
│   ├── init_db.py               # Création automatique des tables
│   └── seed.py                  # Jeu de données de test (18 élèves, 25 paiements)
├── repositories/                # Couche Données (SQL paramétré pur, aucun PySide6)
│   ├── eleve_repository.py      # CRUD élèves, recherche, filtres
│   └── paiement_repository.py   # CRUD paiements, sommes, numéros de reçus
├── services/                    # Couche Métier (Règles de gestion, sans SQL ni PySide6)
│   ├── eleve_service.py         # Calcul du solde/statut, validations élèves, stats
│   ├── paiement_service.py      # Contrôle du solde, transaction d'enregistrement
│   └── recu_service.py          # Numérotation REC-AAAA-NNNN, consolidation reçu
├── ui/                          # Couche Présentation (PySide6 exclusif, sans SQL)
│   ├── main_window.py           # Fenêtre principale et navigation latérale
│   ├── dashboard.py             # Tableau de bord avec 4 indicateurs et filtres
│   ├── eleve_list.py            # Liste des élèves avec recherche et filtres
│   ├── eleve_form.py            # Formulaire d'ajout / modification
│   ├── eleve_fiche.py           # Fiche élève, historique des paiements
│   ├── paiement_dialog.py       # Dialogue d'enregistrement de versement
│   ├── paiement_detail.py       # Consultation détaillée d'un versement
│   └── utils.py                 # Formatage FCFA, dates JJ/MM/AAAA, couleurs
├── receipts/
│   └── pdf_generator.py         # Moteur de génération des reçus PDF ReportLab
├── utils/
│   └── paths.py                 # Résolution des chemins compatible PyInstaller
└── docs/
    ├── mcd.mmd                  # Schéma conceptuel Mermaid (MCD Merise)
    ├── mld.mmd                  # Schéma logique relationnel Mermaid (MLD SQLite)
    ├── architecture.md          # Spécification technique d'architecture
    ├── documentation.md         # Dossier technique complet (4 pages)
    └── manuel_utilisateur.md    # Manuel utilisateur synthétique d'une page
```

---

## 📦 Packaging exécutable Windows (.exe)

Pour produire un binaire autonome sans Python requis sur le poste client :

```bash
pyinstaller --onefile --windowed --name "EduPaie" --add-data "data/edupaie.db;data" --add-data "db/schema.sql;db" main.py
```

L'exécutable généré se trouve dans le dossier `dist/EduPaie.exe`.
Au premier lancement sur une machine cliente, la base de travail est automatiquement déployée dans `%APPDATA%\EduPaie\` pour permettre les modifications permanentes en écriture. Les reçus PDF sont stockés dans `Documents\EduPaie\Recus\`.

---

## 🌳 Workflow Git respecté

Le projet a été développé en respectant rigoureusement le modèle Git Flow :
- `main` : Version stable livrable (tag `v1.0`).
- `develop` : Branche d'intégration continue.
- `feature/*` : Branches dédiées pour chaque fonctionnalité fusionnées avec `--no-ff`.
- Commits conventionnels et granulaires (`feat:`, `chore:`, `docs:`, `build:`).
