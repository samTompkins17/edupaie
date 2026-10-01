"""Smoke-test de l'interface EduPaie (rendu hors écran).

Instancie la fenêtre principale, parcourt les écrans, ouvre la fiche
d'un élève et quitte sans afficher de fenêtre. Sert de vérification
rapide après chaque refonte visuelle.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)

from PySide6.QtWidgets import QApplication

from db.init_db import initialiser_base
from ui.theme import appliquer_theme, feuille_de_style
from ui.main_window import FenetrePrincipale

print("1. QApplication + theme...", flush=True)
app = QApplication(sys.argv)
appliquer_theme(app)
print("   QSS genere :", len(feuille_de_style()), "caracteres", flush=True)

print("2. Initialisation base...", flush=True)
initialiser_base()

print("3. Fenetre principale...", flush=True)
fenetre = FenetrePrincipale()
fenetre.show()
print("   Ecrans :", list(fenetre.ecrans.keys()), flush=True)

print("4. Navigation dashboard -> eleves...", flush=True)
fenetre.naviguer_vers("eleves")
fenetre.naviguer_vers("dashboard")

print("5. Fiche eleve #1...", flush=True)
fenetre.afficher_fiche_eleve(1)
print("   Titre :", fenetre.fiche_eleve.lbl_nom_complet.text(), flush=True)
print("   Statut :", fenetre.fiche_eleve.lbl_val_statut.text(), flush=True)
print("   Solde :", fenetre.fiche_eleve.lbl_val_solde.text(), flush=True)

print("6. Logo rendu...", flush=True)
pix = fenetre.fiche_eleve.grab()
print("   Grab fiche :", pix.width(), "x", pix.height(), flush=True)

print("SMOKE OK", flush=True)
