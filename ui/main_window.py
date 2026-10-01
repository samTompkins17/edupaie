"""
Fenêtre principale de l'application EduPaie.

Contient la barre latérale de navigation (logo, navigation, raccourcis)
et la zone centrale qui affiche les différents écrans (tableau de bord,
liste élèves, fiche élève).
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget,
)

from ui.logo import LogoWidget
from ui.theme import activer_fond_stylise


class FenetrePrincipale(QMainWindow):
    """Fenêtre principale avec navigation latérale et zone de contenu."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduPaie — Gestion des paiements scolaires")
        self.setMinimumSize(1100, 700)
        self.resize(1340, 840)

        # Widget central contenant la mise en page horizontale
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # --- Barre latérale de navigation ---
        self.barre_laterale = self._creer_barre_laterale()
        layout_principal.addWidget(self.barre_laterale)

        # --- Zone de contenu (QStackedWidget pour basculer entre écrans) ---
        self.pile_ecrans = QStackedWidget()
        layout_principal.addWidget(self.pile_ecrans, stretch=1)

        # Dictionnaire pour retrouver l'index de chaque écran par nom
        self.ecrans = {}

        # 1. Écran Tableau de bord (F6)
        from ui.dashboard import TableauDeBord
        self.dashboard = TableauDeBord()
        self.ajouter_ecran("dashboard", self.dashboard)

        # 2. Écran de gestion des élèves (F1)
        from ui.eleve_list import ListeEleves
        from ui.eleve_fiche import FicheEleve

        self.liste_eleves = ListeEleves()
        self.ajouter_ecran("eleves", self.liste_eleves)

        # 3. Écran de la fiche élève (F2, F4)
        self.fiche_eleve = FicheEleve()
        self.ajouter_ecran("fiche_eleve", self.fiche_eleve)

        # Connexions de signaux
        self.dashboard.fiche_demandee.connect(self.afficher_fiche_eleve)
        self.liste_eleves.fiche_demandee.connect(self.afficher_fiche_eleve)
        self.fiche_eleve.retour_demande.connect(lambda: self.naviguer_vers("eleves"))
        self.fiche_eleve.reimprimer_recu_demande.connect(self.imprimer_recu)

        # Raccourcis clavier
        self._creer_raccourcis()

        # Afficher le tableau de bord par défaut au démarrage
        self.naviguer_vers("dashboard")

    # ------------------------------------------------------------------
    # Construction de la barre latérale
    # ------------------------------------------------------------------
    def _creer_barre_laterale(self) -> QWidget:
        """Crée et retourne la barre latérale avec logo et navigation."""
        barre = QWidget()
        barre.setObjectName("sidebar")
        barre.setFixedWidth(252)
        activer_fond_stylise(barre)

        layout = QVBoxLayout(barre)
        layout.setContentsMargins(16, 22, 16, 18)
        layout.setSpacing(0)

        # --- Bloc de marque : logo + nom ---
        marque = QHBoxLayout()
        marque.setSpacing(12)
        marque.setContentsMargins(2, 0, 0, 0)

        self.logo = LogoWidget(42)
        marque.addWidget(self.logo)

        colonne_marque = QVBoxLayout()
        colonne_marque.setSpacing(0)
        colonne_marque.setContentsMargins(0, 0, 0, 0)

        wordmark = QLabel("EduPaie")
        wordmark.setObjectName("sidebarWordmark")
        colonne_marque.addWidget(wordmark)

        tagline = QLabel("Gestion scolaire")
        tagline.setObjectName("sidebarTagline")
        colonne_marque.addWidget(tagline)

        marque.addLayout(colonne_marque)
        marque.addStretch()
        layout.addLayout(marque)

        layout.addSpacing(22)

        # --- Séparateur ---
        separateur = QFrame()
        separateur.setObjectName("sidebarDivider")
        separateur.setFixedHeight(1)
        layout.addWidget(separateur)

        layout.addSpacing(18)

        # --- Libellé de section ---
        section = QLabel("NAVIGATION")
        section.setObjectName("sidebarSection")
        layout.addWidget(section)
        layout.addSpacing(8)

        # --- Boutons de navigation ---
        self.boutons_nav = {}
        noms_ecrans = [
            ("dashboard", "Tableau de bord"),
            ("eleves", "Élèves"),
        ]

        for cle, libelle in noms_ecrans:
            bouton = QPushButton(libelle)
            bouton.setObjectName("navButton")
            bouton.setCheckable(True)
            bouton.setCursor(Qt.CursorShape.PointingHandCursor)
            bouton.clicked.connect(lambda checked, c=cle: self.naviguer_vers(c))
            layout.addWidget(bouton)
            layout.addSpacing(4)
            self.boutons_nav[cle] = bouton

        layout.addStretch()

        # --- Bouton d'action rapide ---
        self.btn_nouvel_eleve = QPushButton("Nouvel élève")
        self.btn_nouvel_eleve.setObjectName("sidebarCta")
        self.btn_nouvel_eleve.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nouvel_eleve.setToolTip("Ajouter un élève (Ctrl+N)")
        self.btn_nouvel_eleve.clicked.connect(self.ouvrir_nouvel_eleve)
        layout.addWidget(self.btn_nouvel_eleve)

        layout.addSpacing(14)

        # --- Encart d'information (base locale) ---
        info = QFrame()
        info.setObjectName("sidebarInfo")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(12, 10, 12, 10)
        info_layout.setSpacing(2)

        titre_info = QLabel("Données locales")
        titre_info.setObjectName("sidebarInfoTitle")
        info_layout.addWidget(titre_info)

        self.lbl_resume_sidebar = QLabel("Base SQLite · hors-ligne")
        self.lbl_resume_sidebar.setObjectName("sidebarInfoText")
        self.lbl_resume_sidebar.setWordWrap(True)
        info_layout.addWidget(self.lbl_resume_sidebar)

        layout.addWidget(info)

        layout.addSpacing(10)

        # --- Pied de barre : version ---
        version = QLabel("Version 1.0.0")
        version.setObjectName("sidebarFooter")
        layout.addWidget(version)

        return barre

    def _creer_raccourcis(self):
        """Installe les raccourcis clavier de navigation rapide."""
        raccourcis = [
            ("Ctrl+1", lambda: self.naviguer_vers("dashboard")),
            ("Ctrl+2", lambda: self.naviguer_vers("eleves")),
            ("Ctrl+N", self.ouvrir_nouvel_eleve),
            ("Ctrl+R", self.actualiser_ecran_courant),
        ]
        for sequence, action in raccourcis:
            QShortcut(QKeySequence(sequence), self, activated=action)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def ajouter_ecran(self, nom: str, widget: QWidget):
        """Ajoute un écran dans la pile et l'enregistre par son nom.

        Args:
            nom: Clé unique pour identifier l'écran (ex: 'eleves', 'dashboard')
            widget: Le widget à afficher pour cet écran
        """
        index = self.pile_ecrans.addWidget(widget)
        self.ecrans[nom] = index

    def naviguer_vers(self, nom_ecran: str):
        """Bascule l'affichage vers l'écran désigné par son nom.

        Met aussi à jour l'état visuel des boutons de navigation.
        """
        if nom_ecran in self.ecrans:
            widget = self.pile_ecrans.widget(self.ecrans[nom_ecran])
            if hasattr(widget, "actualiser"):
                widget.actualiser()
            self.pile_ecrans.setCurrentIndex(self.ecrans[nom_ecran])

            # Mettre à jour l'état checked des boutons
            for cle, bouton in self.boutons_nav.items():
                bouton.setChecked(cle == nom_ecran)

            self._maj_resume_sidebar()

    def _maj_resume_sidebar(self):
        """Rafraîchit le petit résumé affiché dans la barre latérale."""
        try:
            from services import eleve_service

            stats = eleve_service.obtenir_statistiques()
            self.lbl_resume_sidebar.setText(
                f"{stats['nombre_eleves']} élèves suivis\n"
                f"{stats['nombre_non_soldes']} dossier(s) à recouvrer"
            )
        except Exception:
            self.lbl_resume_sidebar.setText("Base SQLite · hors-ligne")

    def actualiser_ecran_courant(self):
        """Recharge l'écran actuellement affiché."""
        widget = self.pile_ecrans.currentWidget()
        if widget is not None and hasattr(widget, "actualiser"):
            widget.actualiser()
        self._maj_resume_sidebar()

    def afficher_fiche_eleve(self, id_eleve: int):
        """Affiche la fiche détaillée de l'élève spécifié."""
        self.fiche_eleve.charger_eleve(id_eleve)
        self.naviguer_vers("fiche_eleve")

    def ouvrir_nouvel_eleve(self):
        """Navigue vers la liste des élèves et ouvre le formulaire d'ajout."""
        self.naviguer_vers("eleves")
        self.liste_eleves.ouvrir_formulaire_ajout()

    def imprimer_recu(self, id_paiement: int):
        """Génère (ou retrouve) le reçu PDF et l'ouvre pour l'utilisateur."""
        try:
            from receipts.pdf_generator import generer_recu_pdf, ouvrir_recu_pdf

            chemin = generer_recu_pdf(id_paiement)
            ouvrir_recu_pdf(chemin)
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(
                self,
                "Erreur d'édition du reçu",
                f"Impossible d'ouvrir le reçu PDF :\n\n{e}",
            )
