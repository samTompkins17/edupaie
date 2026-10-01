"""Capture d'écrans de l'interface EduPaie (rendu hors écran).

Produit des captures PNG de la fenêtre principale pour chaque écran :
    preview/dashboard.png, preview/eleves.png, preview/fiche_eleve.png
Utile pour vérifier visuellement une refonte sans lancer l'application.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)

from PySide6.QtWidgets import QApplication

from db.init_db import initialiser_base
from ui.theme import appliquer_theme
from ui.main_window import FenetrePrincipale

DOSSIER = os.path.join(RACINE, "preview")
os.makedirs(DOSSIER, exist_ok=True)

app = QApplication(sys.argv)
appliquer_theme(app)
initialiser_base()

fenetre = FenetrePrincipale()
fenetre.resize(1340, 840)
fenetre.show()

captures = [
    ("dashboard", "dashboard.png"),
    ("eleves", "eleves.png"),
    ("fiche_eleve", "fiche_eleve.png"),
]

for ecran, fichier in captures:
    if ecran == "fiche_eleve":
        fenetre.afficher_fiche_eleve(1)  # DIALLO Aminata : 3 versements
    else:
        fenetre.naviguer_vers(ecran)
    app.processEvents()
    pixmap = fenetre.grab()
    chemin = os.path.join(DOSSIER, fichier)
    ok = pixmap.save(chemin, "PNG")
    print(("OK  " if ok else "ECHEC ") + fichier,
          f"{pixmap.width()}x{pixmap.height()}", flush=True)

print("CAPTURES TERMINEES", flush=True)
