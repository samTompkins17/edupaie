"""
Écran de la liste des élèves.

Affiche un tableau avec recherche textuelle et filtre par classe.
Colonnes : Nom, Prénom, Classe, Année, Total dû, Solde, Statut.
Boutons : Ajouter, Modifier, Supprimer, Voir fiche, Enregistrer paiement.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from services import eleve_service
from ui.theme import COULEUR_STATUT, PALETTE
from ui.utils import couleur_statut, formater_montant
from ui.widgets import EnTetePage, separateur_horizontal


class ListeEleves(QWidget):
    """Widget affichant la liste des élèves avec recherche et filtres."""

    # Signal émis quand l'utilisateur veut voir la fiche d'un élève
    fiche_demandee = Signal(int)  # émet l'id_eleve

    def __init__(self):
        super().__init__()
        self._construire_interface()
        self.actualiser()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _construire_interface(self):
        """Construit la mise en page de l'écran."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(16)

        # --- En-tête ---
        entete = EnTetePage(
            "Élèves",
            "Annuaire, situation des soldes et enregistrement des versements",
        )
        self.btn_ajouter = QPushButton("Ajouter un élève")
        self.btn_ajouter.setObjectName("btnPrimary")
        self.btn_ajouter.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ajouter.setToolTip("Nouvel élève (Ctrl+N)")
        self.btn_ajouter.clicked.connect(self._ajouter_eleve)
        entete.ajouter_action(self.btn_ajouter)
        layout.addWidget(entete)

        # --- Barre de recherche et filtres ---
        barre = QHBoxLayout()
        barre.setSpacing(10)

        self.champ_recherche = QLineEdit()
        self.champ_recherche.setObjectName("searchField")
        self.champ_recherche.setPlaceholderText(
            "Rechercher par nom ou prénom..."
        )
        self.champ_recherche.textChanged.connect(self.actualiser)
        barre.addWidget(self.champ_recherche, stretch=1)

        self.filtre_classe = QComboBox()
        self.filtre_classe.setMinimumWidth(180)
        self.filtre_classe.currentTextChanged.connect(self.actualiser)
        barre.addWidget(self.filtre_classe)

        layout.addLayout(barre)

        # --- Tableau des élèves ---
        self.tableau = QTableWidget()
        self._configurer_tableau()
        layout.addWidget(self.tableau, stretch=1)

        layout.addWidget(separateur_horizontal())

        # --- Boutons d'action ---
        boutons = QHBoxLayout()
        boutons.setSpacing(10)

        self.btn_supprimer = QPushButton("Supprimer")
        self.btn_supprimer.setObjectName("btnDanger")
        self.btn_supprimer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_supprimer.clicked.connect(self._supprimer_eleve)
        boutons.addWidget(self.btn_supprimer)

        self.btn_modifier = QPushButton("Modifier")
        self.btn_modifier.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_modifier.clicked.connect(self._modifier_eleve)
        boutons.addWidget(self.btn_modifier)

        self.btn_paiement = QPushButton("Enregistrer un paiement")
        self.btn_paiement.setObjectName("btnSuccess")
        self.btn_paiement.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_paiement.clicked.connect(self._enregistrer_paiement_selectionne)
        boutons.addWidget(self.btn_paiement)

        boutons.addStretch()

        self.lbl_resume = QLabel("0 élève(s)")
        self.lbl_resume.setObjectName("muted")
        boutons.addWidget(self.lbl_resume)

        self.btn_fiche = QPushButton("Voir la fiche")
        self.btn_fiche.setObjectName("btnGhost")
        self.btn_fiche.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fiche.clicked.connect(self._ouvrir_fiche)
        boutons.addWidget(self.btn_fiche)

        layout.addLayout(boutons)

    def _configurer_tableau(self):
        """Configure les colonnes et le comportement du tableau."""
        self.tableau.setColumnCount(7)
        self.tableau.setHorizontalHeaderLabels([
            "Nom", "Prénom", "Classe", "Année", "Total dû", "Solde", "Statut",
        ])
        self.tableau.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tableau.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.tableau.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.tableau.setAlternatingRowColors(True)
        self.tableau.setShowGrid(False)
        self.tableau.verticalHeader().setVisible(False)
        self.tableau.verticalHeader().setDefaultSectionSize(40)

        entete = self.tableau.horizontalHeader()
        entete.setHighlightSections(False)
        entete.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        entete.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for colonne in range(2, 7):
            entete.setSectionResizeMode(
                colonne, QHeaderView.ResizeMode.ResizeToContents
            )

        # Double-clic pour ouvrir la fiche
        self.tableau.doubleClicked.connect(self._ouvrir_fiche)

    # ------------------------------------------------------------------
    # Données
    # ------------------------------------------------------------------
    def actualiser(self):
        """Recharge les données du tableau avec les filtres actuels."""
        terme = self.champ_recherche.text().strip()

        # Récupérer le filtre classe (ignorer "Toutes les classes")
        classe = self.filtre_classe.currentText()
        if classe == "Toutes les classes":
            classe = ""

        # Mettre à jour la liste des classes dans le filtre
        self._actualiser_filtre_classes()

        # Récupérer les élèves filtrés (avec solde et statut calculés)
        eleves = eleve_service.lister_eleves(terme, classe)
        self._remplir_tableau(eleves)

    def _actualiser_filtre_classes(self):
        """Met à jour le combo des classes sans perdre la sélection."""
        classe_actuelle = self.filtre_classe.currentText()
        self.filtre_classe.blockSignals(True)
        self.filtre_classe.clear()
        self.filtre_classe.addItem("Toutes les classes")
        for classe in eleve_service.lister_classes():
            self.filtre_classe.addItem(classe)
        # Restaurer la sélection précédente si elle existe encore
        index = self.filtre_classe.findText(classe_actuelle)
        if index >= 0:
            self.filtre_classe.setCurrentIndex(index)
        self.filtre_classe.blockSignals(False)

    def _remplir_tableau(self, eleves: list[dict]):
        """Remplit le tableau avec la liste d'élèves fournie."""
        self.tableau.setUpdatesEnabled(False)
        self.tableau.blockSignals(True)
        try:
            self.tableau.setRowCount(len(eleves))

            for ligne, eleve in enumerate(eleves):
                # Stocker l'id dans la première cellule (donnée cachée)
                item_nom = QTableWidgetItem(eleve["nom"])
                item_nom.setData(Qt.ItemDataRole.UserRole, eleve["id_eleve"])
                item_nom.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
                self.tableau.setItem(ligne, 0, item_nom)

                self.tableau.setItem(ligne, 1, QTableWidgetItem(eleve["prenom"]))

                item_classe = QTableWidgetItem(eleve["classe"])
                item_classe.setForeground(QColor(PALETTE["textMuted"]))
                self.tableau.setItem(ligne, 2, item_classe)

                item_annee = QTableWidgetItem(eleve["annee_scolaire"])
                item_annee.setForeground(QColor(PALETTE["textMuted"]))
                self.tableau.setItem(ligne, 3, item_annee)

                self.tableau.setItem(
                    ligne, 4, QTableWidgetItem(formater_montant(eleve["total_du"]))
                )

                item_solde = QTableWidgetItem(formater_montant(eleve["solde"]))
                item_solde.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                if eleve["solde"] > 0:
                    item_solde.setForeground(QColor(COULEUR_STATUT["Non payé"]))
                else:
                    item_solde.setForeground(QColor(COULEUR_STATUT["Soldé"]))
                self.tableau.setItem(ligne, 5, item_solde)

                # Statut avec couleur
                item_statut = QTableWidgetItem(eleve["statut"])
                item_statut.setForeground(QColor(couleur_statut(eleve["statut"])))
                item_statut.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self.tableau.setItem(ligne, 6, item_statut)
        finally:
            self.tableau.blockSignals(False)
            self.tableau.setUpdatesEnabled(True)

        self.lbl_resume.setText(f"{len(eleves)} élève(s) affiché(s)")

    def _obtenir_id_selectionne(self) -> int | None:
        """Retourne l'id_eleve de la ligne sélectionnée, ou None."""
        ligne = self.tableau.currentRow()
        if ligne < 0:
            return None
        item = self.tableau.item(ligne, 0)
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def ouvrir_formulaire_ajout(self):
        """Point d'entrée public : ouvre le formulaire de création d'élève."""
        self._ajouter_eleve()

    def _ajouter_eleve(self):
        """Ouvre le formulaire d'ajout d'élève et actualise la liste."""
        from ui.eleve_form import FormulaireEleve

        form = FormulaireEleve(self)
        if form.exec():
            self.actualiser()

    def _modifier_eleve(self):
        """Ouvre le formulaire de modification pour l'élève sélectionné."""
        id_eleve = self._obtenir_id_selectionne()
        if id_eleve is None:
            QMessageBox.information(
                self, "Information",
                "Veuillez sélectionner un élève dans la liste à modifier."
            )
            return

        eleve = eleve_service.obtenir_eleve(id_eleve)
        from ui.eleve_form import FormulaireEleve

        form = FormulaireEleve(self, eleve=eleve)
        if form.exec():
            self.actualiser()

    def _enregistrer_paiement_selectionne(self):
        """Ouvre le dialogue de paiement pour l'élève sélectionné."""
        id_eleve = self._obtenir_id_selectionne()
        if id_eleve is None:
            QMessageBox.information(
                self, "Information",
                "Veuillez sélectionner un élève dans la liste pour "
                "enregistrer un versement."
            )
            return

        from ui.paiement_dialog import DialoguePaiement

        dlg = DialoguePaiement(self, id_eleve=id_eleve)
        if dlg.exec():
            self.actualiser()
            if dlg.imprimer_demande and dlg.paiement_cree:
                self.fiche_demandee.emit(id_eleve)

    def _ouvrir_fiche(self):
        """Émet le signal pour ouvrir la fiche de l'élève sélectionné."""
        id_eleve = self._obtenir_id_selectionne()
        if id_eleve is None:
            QMessageBox.information(
                self, "Information",
                "Veuillez sélectionner un élève dans la liste."
            )
            return
        self.fiche_demandee.emit(id_eleve)

    def _supprimer_eleve(self):
        """Demande confirmation puis supprime l'élève sélectionné."""
        id_eleve = self._obtenir_id_selectionne()
        if id_eleve is None:
            QMessageBox.information(
                self, "Information",
                "Veuillez sélectionner un élève dans la liste."
            )
            return

        # Confirmation
        reponse = QMessageBox.question(
            self, "Confirmer la suppression",
            "Voulez-vous vraiment supprimer cet élève ?\n"
            "Cette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reponse != QMessageBox.StandardButton.Yes:
            return

        # Tentative de suppression
        try:
            eleve_service.supprimer_eleve(id_eleve)
            QMessageBox.information(
                self, "Succès", "L'élève a été supprimé avec succès."
            )
            self.actualiser()
        except ValueError as e:
            QMessageBox.warning(self, "Suppression impossible", str(e))
