"""
Écran du Tableau de bord (Dashboard) — Fonctionnalité F6.

Affiche :
- Les indicateurs globaux d'activité :
  * Nombre total d'élèves
  * Total global encaissé + taux de recouvrement
  * Total restant à recouvrer
  * Nombre d'élèves non soldés (répartition par statut)
- Une liste filtrable par statut de paiement et par recherche rapide
- Accès rapide à la fiche de l'élève par double-clic ou bouton
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMessageBox, QProgressBar, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from services import eleve_service
from services.eleve_service import STATUT_NON_PAYE, STATUT_PARTIEL, STATUT_SOLDE
from ui.theme import COULEUR_STATUT, PALETTE
from ui.utils import couleur_statut, formater_montant
from ui.widgets import CarteKPI, EnTetePage, separateur_horizontal


class TableauDeBord(QWidget):
    """Widget d'accueil et tableau de bord de gestion des paiements."""

    fiche_demandee = Signal(int)  # émet id_eleve

    def __init__(self, parent=None):
        super().__init__(parent)
        self._construire_interface()
        self.actualiser()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _construire_interface(self):
        """Construit l'interface du tableau de bord."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(18)

        # --- En-tête ---
        entete = EnTetePage(
            "Tableau de bord",
            "Synthèse financière de l'établissement et suivi du recouvrement",
        )
        btn_actualiser = QPushButton("Actualiser")
        btn_actualiser.setObjectName("btnGhost")
        btn_actualiser.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_actualiser.setToolTip("Recharger les indicateurs (Ctrl+R)")
        btn_actualiser.clicked.connect(self.actualiser)
        entete.ajouter_action(btn_actualiser)
        layout.addWidget(entete)

        # --- Cartes d'indicateurs (sobres, sans décor) ---
        cartes = QHBoxLayout()
        cartes.setSpacing(14)

        carte_eleves = CarteKPI("ÉLÈVES INSCRITS", "0", "Inscrits au total")
        self.lbl_nb_eleves = carte_eleves.lbl_valeur
        self.lbl_sous_eleves = carte_eleves.lbl_sous_titre
        cartes.addWidget(carte_eleves, stretch=1)

        carte_encaisse = CarteKPI("TOTAL ENCAISSÉ", "0 FCFA",
                                  "Taux de recouvrement : 0 %")
        self.lbl_total_encaisse = carte_encaisse.lbl_valeur
        self.lbl_taux_recouvrement = carte_encaisse.lbl_sous_titre
        cartes.addWidget(carte_encaisse, stretch=1)

        carte_restant = CarteKPI("TOTAL RESTANT DÛ", "0 FCFA", "À recouvrer")
        self.lbl_total_restant = carte_restant.lbl_valeur
        self.lbl_sous_restant = carte_restant.lbl_sous_titre
        cartes.addWidget(carte_restant, stretch=1)

        carte_non_soldes = CarteKPI("ÉLÈVES NON SOLDÉS", "0",
                                    "0 partiel(s) | 0 non payé(s)")
        self.lbl_non_soldes = carte_non_soldes.lbl_valeur
        self.lbl_repartition_statuts = carte_non_soldes.lbl_sous_titre
        cartes.addWidget(carte_non_soldes, stretch=1)

        layout.addLayout(cartes)

        # --- Barre de taux de recouvrement ---
        cadre_taux = QHBoxLayout()
        cadre_taux.setSpacing(12)

        lbl_taux = QLabel("Taux de recouvrement global")
        lbl_taux.setObjectName("muted")
        cadre_taux.addWidget(lbl_taux)

        self.barre_taux = QProgressBar()
        self.barre_taux.setRange(0, 100)
        self.barre_taux.setValue(0)
        self.barre_taux.setTextVisible(False)
        self.barre_taux.setFixedHeight(12)
        cadre_taux.addWidget(self.barre_taux, stretch=1)

        self.lbl_taux_valeur = QLabel("0 %")
        self.lbl_taux_valeur.setStyleSheet(
            f"color: {PALETTE['text']}; font-weight: 700;"
        )
        self.lbl_taux_valeur.setFixedWidth(52)
        self.lbl_taux_valeur.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        cadre_taux.addWidget(self.lbl_taux_valeur)

        layout.addLayout(cadre_taux)

        layout.addWidget(separateur_horizontal())

        # --- Titre de section + compteur ---
        ligne_section = QHBoxLayout()
        titre_section = QLabel("Suivi des élèves par statut de paiement")
        titre_section.setObjectName("sectionTitle")
        ligne_section.addWidget(titre_section)
        ligne_section.addStretch()

        self.lbl_resume_lignes = QLabel("0 élève(s) affiché(s)")
        self.lbl_resume_lignes.setObjectName("muted")
        ligne_section.addWidget(self.lbl_resume_lignes)
        layout.addLayout(ligne_section)

        # --- Barre de filtres ---
        filtres = QHBoxLayout()
        filtres.setSpacing(10)

        # Filtre par statut : uniquement les trois statuts réels de l'application,
        # libellés issus du service métier pour rester synchronisés avec le tableau
        self.combo_statut = QComboBox()
        self.combo_statut.setMinimumWidth(240)
        self.combo_statut.addItems([STATUT_SOLDE, STATUT_PARTIEL, STATUT_NON_PAYE])
        self.combo_statut.currentTextChanged.connect(self._remplir_tableau)
        filtres.addWidget(self.combo_statut)

        self.recherche_champ = QLineEdit()
        self.recherche_champ.setObjectName("searchField")
        self.recherche_champ.setPlaceholderText(
            "Rechercher un élève (nom, prénom, classe)..."
        )
        self.recherche_champ.textChanged.connect(self._remplir_tableau)
        filtres.addWidget(self.recherche_champ, stretch=1)

        layout.addLayout(filtres)

        # --- Tableau des élèves ---
        self.tableau = QTableWidget()
        self._configurer_tableau()
        layout.addWidget(self.tableau, stretch=1)

        # --- Barre d'actions inférieure ---
        barre_bas = QHBoxLayout()
        lbl_aide = QLabel("Double-cliquez sur une ligne pour ouvrir la fiche détaillée.")
        lbl_aide.setObjectName("muted")
        barre_bas.addWidget(lbl_aide)
        barre_bas.addStretch()

        btn_fiche = QPushButton("Ouvrir la fiche de l'élève")
        btn_fiche.setObjectName("btnPrimary")
        btn_fiche.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_fiche.clicked.connect(self._ouvrir_fiche_selectionnee)
        barre_bas.addWidget(btn_fiche)

        layout.addLayout(barre_bas)

    def _configurer_tableau(self):
        """Configure le tableau des élèves (colonnes, comportement, style)."""
        self.tableau.setColumnCount(7)
        self.tableau.setHorizontalHeaderLabels([
            "Nom", "Prénom", "Classe", "Total dû",
            "Somme versée", "Solde restant", "Statut",
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

        self.tableau.doubleClicked.connect(self._ouvrir_fiche_selectionnee)

    # ------------------------------------------------------------------
    # Données
    # ------------------------------------------------------------------
    def actualiser(self):
        """Met à jour les statistiques et recharge la liste d'élèves."""
        stats = eleve_service.obtenir_statistiques()

        # 1. Nombre d'élèves
        self.lbl_nb_eleves.setText(str(stats["nombre_eleves"]))
        self.lbl_sous_eleves.setText(f"{stats['nombre_soldes']} soldé(s)")

        # 2. Total encaissé + taux
        self.lbl_total_encaisse.setText(formater_montant(stats["total_encaisse"]))
        self.lbl_taux_recouvrement.setText(
            f"Taux de recouvrement : {stats['taux_recouvrement']} %"
        )
        taux = int(round(stats["taux_recouvrement"]))
        self.barre_taux.setValue(max(0, min(100, taux)))
        self.lbl_taux_valeur.setText(f"{stats['taux_recouvrement']} %")

        # 3. Total restant dû
        self.lbl_total_restant.setText(formater_montant(stats["total_restant_du"]))
        self.lbl_sous_restant.setText(
            f"Sur {stats['nombre_non_soldes']} élève(s) redevable(s)"
        )

        # 4. Non soldés
        self.lbl_non_soldes.setText(str(stats["nombre_non_soldes"]))
        self.lbl_repartition_statuts.setText(
            f"{stats['nombre_partiellement_payes']} partiel(s) | "
            f"{stats['nombre_non_payes']} non payé(s)"
        )

        self._remplir_tableau()

    def _remplir_tableau(self):
        """Filtre et affiche les élèves selon le statut et le texte saisis."""
        choix_statut = self.combo_statut.currentText()
        terme = self.recherche_champ.text().strip().lower()

        tous = eleve_service.lister_eleves()

        # Application du filtre par statut : le libellé choisi dans le menu
        # correspond exactement à la valeur du statut de l'élève
        eleves = [e for e in tous if e["statut"] == choix_statut]

        # Application du filtre texte
        if terme:
            eleves = [
                e for e in eleves
                if terme in e["nom"].lower()
                or terme in e["prenom"].lower()
                or terme in e["classe"].lower()
            ]

        # Remplissage du tableau avec suspension des rafraîchissements pour la fluidité
        self.tableau.setUpdatesEnabled(False)
        self.tableau.blockSignals(True)
        try:
            self.tableau.setRowCount(len(eleves))
            for ligne, eleve in enumerate(eleves):
                item_nom = QTableWidgetItem(eleve["nom"])
                item_nom.setData(Qt.ItemDataRole.UserRole, eleve["id_eleve"])
                item_nom.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
                self.tableau.setItem(ligne, 0, item_nom)

                self.tableau.setItem(ligne, 1, QTableWidgetItem(eleve["prenom"]))

                item_classe = QTableWidgetItem(eleve["classe"])
                item_classe.setForeground(QColor(PALETTE["textMuted"]))
                self.tableau.setItem(ligne, 2, item_classe)

                self.tableau.setItem(
                    ligne, 3, QTableWidgetItem(formater_montant(eleve["total_du"]))
                )
                self.tableau.setItem(
                    ligne, 4, QTableWidgetItem(formater_montant(eleve["somme_payee"]))
                )

                item_solde = QTableWidgetItem(formater_montant(eleve["solde"]))
                item_solde.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                if eleve["solde"] > 0:
                    item_solde.setForeground(QColor(COULEUR_STATUT["Non payé"]))
                else:
                    item_solde.setForeground(QColor(COULEUR_STATUT["Soldé"]))
                self.tableau.setItem(ligne, 5, item_solde)

                item_statut = QTableWidgetItem(eleve["statut"])
                item_statut.setForeground(QColor(couleur_statut(eleve["statut"])))
                item_statut.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self.tableau.setItem(ligne, 6, item_statut)
        finally:
            self.tableau.blockSignals(False)
            self.tableau.setUpdatesEnabled(True)

        self.lbl_resume_lignes.setText(
            f"{len(eleves)} élève(s) affiché(s) sur {len(tous)}"
        )

    def _obtenir_id_selectionne(self) -> int | None:
        """Retourne l'id_eleve sélectionné dans le tableau."""
        ligne = self.tableau.currentRow()
        if ligne < 0:
            return None
        item = self.tableau.item(ligne, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _ouvrir_fiche_selectionnee(self):
        """Émet le signal pour ouvrir la fiche de l'élève sélectionné."""
        id_eleve = self._obtenir_id_selectionne()
        if id_eleve is None:
            QMessageBox.information(
                self, "Information",
                "Veuillez sélectionner un élève dans la liste."
            )
            return
        self.fiche_demandee.emit(id_eleve)
