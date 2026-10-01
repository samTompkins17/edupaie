"""
Gestion des chemins de fichiers pour EduPaie.

Compatible avec l'exécution en développement et avec PyInstaller (--onefile).
- Ressources embarquées (icônes, schema.sql) → resource_path()
- Base de données (lecture/écriture)          → get_data_dir()
- Reçus PDF (écriture)                        → get_receipts_dir()
"""

import sys
import os
import shutil


def resource_path(relative_path: str) -> str:
    """Retourne le chemin absolu vers une ressource embarquée.

    En mode PyInstaller, les ressources sont extraites dans un dossier
    temporaire accessible via sys._MEIPASS. En développement, on
    remonte simplement à la racine du projet.
    """
    if hasattr(sys, '_MEIPASS'):
        # Mode PyInstaller : dossier temporaire d'extraction
        return os.path.join(sys._MEIPASS, relative_path)
    # Mode développement : relatif à la racine du projet
    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(racine, relative_path)


def get_data_dir() -> str:
    """Retourne le dossier contenant la base de données (en écriture).

    En mode PyInstaller :
        - Utilise %APPDATA%/EduPaie/
        - Copie la base initiale embarquée au premier lancement
    En développement :
        - Utilise le dossier data/ à la racine du projet
    """
    if hasattr(sys, '_MEIPASS'):
        # Mode PyInstaller : stocker dans %APPDATA%/EduPaie
        appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        dossier = os.path.join(appdata, 'EduPaie')
        os.makedirs(dossier, exist_ok=True)

        # Copier la base initiale si elle n'existe pas encore
        destination = os.path.join(dossier, 'edupaie.db')
        if not os.path.exists(destination):
            source = os.path.join(sys._MEIPASS, 'data', 'edupaie.db')
            if os.path.exists(source):
                shutil.copy2(source, destination)

        return dossier
    else:
        # Mode développement : dossier data/ du projet
        racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dossier = os.path.join(racine, 'data')
        os.makedirs(dossier, exist_ok=True)
        return dossier


def get_receipts_dir() -> str:
    """Retourne le dossier de stockage des reçus PDF.

    Crée le dossier Documents/EduPaie/Recus/ s'il n'existe pas.
    Ce dossier est toujours accessible en écriture.
    """
    documents = os.path.join(os.path.expanduser('~'), 'Documents')
    dossier = os.path.join(documents, 'EduPaie', 'Recus')
    os.makedirs(dossier, exist_ok=True)
    return dossier
