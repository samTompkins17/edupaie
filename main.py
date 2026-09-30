"""
Point d'entrée de l'application EduPaie.

Responsabilités :
- Installer un gestionnaire d'exceptions global (sys.excepthook)
- Initialiser la base de données
- Appliquer l'identité visuelle (thème + logo)
- Lancer la fenêtre principale PySide6
"""

import sys
import logging
import os
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox

from db.init_db import initialiser_base
from ui.main_window import FenetrePrincipale
from ui.theme import appliquer_theme, icone_application
from utils.paths import get_data_dir


# --- Configuration du journal d'erreurs ---
logging.basicConfig(
    filename=os.path.join(get_data_dir(), "edupaie.log"),
    level=logging.ERROR,
    format="%(asctime)s — %(levelname)s — %(message)s",
)


def gestionnaire_exceptions(type_exc, valeur, tb):
    """Gestionnaire global d'exceptions non attrapées.

    Affiche un message d'erreur à l'utilisateur via QMessageBox
    et enregistre les détails dans le fichier edupaie.log.
    Empêche l'application de planter silencieusement.
    """
    # Formater le message d'erreur complet pour le log
    message_complet = "".join(traceback.format_exception(type_exc, valeur, tb))
    logging.error("Exception non gérée :\n%s", message_complet)

    # Afficher un message simplifié à l'utilisateur
    try:
        QMessageBox.critical(
            None,
            "Erreur inattendue",
            f"Une erreur inattendue s'est produite :\n\n{valeur}\n\n"
            "Les détails ont été enregistrés dans le journal de l'application.",
        )
    except Exception:
        # Si même QMessageBox échoue, afficher dans la console
        print(message_complet, file=sys.stderr)


def main():
    """Fonction principale : initialise et lance l'application."""
    # Installer le gestionnaire d'exceptions global
    sys.excepthook = gestionnaire_exceptions

    # Créer l'application Qt
    app = QApplication(sys.argv)
    # Métadonnées applicatives (nom, organisation, version)
    app.setApplicationName("EduPaie")
    app.setApplicationDisplayName("EduPaie — Gestion des paiements scolaires")
    app.setOrganizationName("EduPaie")
    app.setApplicationVersion("1.0.0")

    # Identité visuelle : thème global + logo
    appliquer_theme(app)
    app.setWindowIcon(icone_application())

    # Initialiser la base de données (crée les tables si nécessaire)
    try:
        initialiser_base()
    except Exception as e:
        QMessageBox.critical(
            None,
            "Erreur d'initialisation",
            f"Impossible d'initialiser la base de données :\n\n{e}",
        )
        sys.exit(1)

    # Créer et afficher la fenêtre principale
    fenetre = FenetrePrincipale()
    fenetre.show()

    # Lancer la boucle événementielle Qt
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
