# EduPaie

EduPaie est une application de bureau destinée au suivi des frais de scolarité. Elle permet d’enregistrer les élèves et leurs paiements, de consulter les soldes et de produire des reçus PDF. L’application est écrite en Python avec PySide6 et utilise SQLite pour stocker les données localement.

## Fonctions principales

- Gestion des élèves : ajout, modification, recherche et suppression lorsqu’aucun paiement n’est associé.
- Calcul du montant payé, du solde restant et du statut de paiement.
- Enregistrement des paiements par espèces, chèque, virement ou Mobile Money.
- Consultation de l’historique et du détail des paiements.
- Génération et réimpression de reçus PDF numérotés au format `REC-AAAA-NNNN`.
- Tableau de bord avec les principaux totaux et un suivi par statut.

## Prérequis

- **Python 3.10 ou supérieur**
- Windows 10 ou 11 pour utiliser les scripts de build fournis. L’application peut aussi être lancée avec Python sur d’autres systèmes compatibles avec PySide6.

---

## Installation

Clone le dépôt, crée un environnement virtuel et installe les dépendances :

```powershell
git clone https://github.com/samTompkins17/edupaie.git
cd edupaie
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Puis lance l’application :

```powershell
python main.py
```

Au premier lancement, EduPaie crée les tables nécessaires. Le dépôt contient aussi une base de démonstration. Pour la recréer avec 18 élèves et 25 paiements, exécute :

```powershell
python db/seed.py
```

Cette commande efface les données présentes dans la base de travail et les remplace par les données de démonstration.

## Tests

Depuis la racine du projet, lance la suite avec :

```powershell
python -m unittest discover -s tests -v
```

## Organisation du code

Le code est réparti par rôle : `ui/` contient les écrans, `services/` les règles métier et `repositories/` les requêtes SQLite.

```text
├── main.py                 # Démarrage de l’application
├── db/                     # Connexion, schéma et données de démonstration
├── repositories/           # Accès aux données
├── services/               # Logique métier
├── ui/                     # Interface PySide6
├── receipts/               # Création des reçus PDF
├── resources/              # Logos et icônes
├── tests/                  # Tests automatisés
├── tools/                  # Build installateur, capture, smoke-test, assets
├── data/                   # Base SQLite de démonstration
├── EduPaie.spec            # Configuration PyInstaller
├── build.bat               # Tests et build sous Windows
└── requirements.txt        # Dépendances Python
```

## Construire l’exécutable

Sous Windows, le script `build.bat` génère les ressources, lance les tests, puis construit l’exécutable autonome `dist/EduPaie.exe` :

```powershell
.\build.bat
```

Le build peut aussi être lancé directement avec PyInstaller :

```powershell
python -m PyInstaller EduPaie.spec --noconfirm --clean
```

Dans la version empaquetée, la base modifiable est copiée dans `%APPDATA%\EduPaie\`. Les reçus PDF sont enregistrés dans `Documents\EduPaie\Recus\`.

## Installer sur un PC (installateur Windows)

Le script `tools/build_installer.bat` produit un véritable installateur Windows : EduPaie est alors **installé de façon permanente** sur le PC (il ne disparaît pas à la fermeture), accessible depuis le **menu Démarrer**, avec un **désinstalleur** dans « Applications et fonctionnalités ».

Prérequis (une seule fois) : Inno Setup 6 :

```powershell
winget install -e --id JRSoftware.InnoSetup
```

Puis générez l’installateur :

```powershell
tools\build_installer.bat
```

Le fichier obtenu, `output\EduPaie-Setup-1.0.0.exe`, se copie sur n’importe quel PC Windows 10/11 (clé USB, partage réseau…) : double-clic, choix du dossier d’installation, terminé. Aucun droit administrateur n’est requis (installation par utilisateur) et le dossier d’installation est librement choisissable — utile si le disque C: est saturé.

À la désinstallation, les données scolaires (`%APPDATA%\EduPaie\edupaie.db`) sont **conservées** : réinstaller EduPaie les retrouve.
