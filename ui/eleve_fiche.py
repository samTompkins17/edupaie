"""
Écran de la fiche détaillée d'un élève.

Affiche :
- Une bannière d'identité (initiales, nom, classe, année)
- Les cartes de synthèse financière : Total dû, Somme versée,
  Solde restant, Statut
- Le tableau chronologique des versements effectués
- Les actions : enregistrer un paiement, consulter un versement,
  réimprimer un reçu
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView, QFrame, QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from repositories import paiement_repository
from services import eleve_service
from ui.theme import COULEUR_STATUT, PALETTE
from ui.utils import (
    couleur_statut, formater_date_affichage, formater_montant, initiales,
    libelle_mode_paiement,
)
from ui.widgets import CarteKPI, EnTetePage, separateur_horizontal


class FicheEleve(QWidget):
    """Widget affichant la fiche détaillée d'un élève et ses paiements."""

    # Signaux pour la navigation et les actions
    retour_demande = Signal()
    nouveau_paiement_demande = Signal(int)  # émet id_eleve
    reimprimer_recu_demande = Signal(int)   # émet id_paiement

    def __init__(self, parent=None):
        super().__init__(parent)
        self.id_eleve = None
        self._construire_interface()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _construire_interface(self):
        """Construit l'interface graphique de la fiche élève."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(18)

        # --- Barre supérieure : retour + actions ---
        entete = EnTetePage(
            "Fiche élève", "Dossier scolaire et suivi des versements"
        )
        self.titre_fiche = entete.lbl_sous_titre  # compatibilité

        self.btn_retour = QPushButton("Retour à la liste")
        self.btn_retour.setObjectName("btnGhost")
        self.btn_retour.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_retour.clicked.connect(self.retour_demande.emit)
        entete.ajouter_action_gauche(self.btn_retour)

        self.btn_payer = QPushButton("Enregistrer un paiement")
        self.btn_payer.setObjectName("btnSuccess")
        self.btn_payer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_payer.clicked.connect(self._action_nouveau_paiement)
        entete.ajouter_action(self.btn_payer)

        layout.addWidget(entete)

        # --- Bannière d'identité (carte sobre) ---
        hero = QFrame()
        hero.setObjectName("heroCard")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(20, 18, 20, 18)
        hero_layout.setSpacing(16)

        self.lbl_avatar = QLabel("?")
        self.lbl_avatar.setObjectName("heroAvatar")
        self.lbl_avatar.setFixedSize(52, 52)
        self.lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(self.lbl_avatar)

        colonne = QVBoxLayout()
        colonne.setSpacing(2)

        self.lbl_nom_complet = QLabel("Nom et prénom")
        self.lbl_nom_complet.setObjectName("heroName")
        colonne.addWidget(self.lbl_nom_complet)

        self.lbl_classe_annee = QLabel("Classe : -  |  Année scolaire : -")
        self.lbl_classe_annee.setObjectName("heroMeta")
        colonne.addWidget(self.lbl_classe_annee)

        hero_layout.addLayout(colonne)
        hero_layout.addStretch()

        self.lbl_recu_count = QLabel("0 versement(s)")
        self.lbl_recu_count.setObjectName("heroMeta")
        hero_layout.addWidget(self.lbl_recu_count)

        layout.addWidget(hero)

        # --- Cartes de synthèse financière (sobres) ---
        cartes = QHBoxLayout()
        cartes.setSpacing(14)

        carte_total = CarteKPI("TOTAL DES FRAIS DUS", "0 FCFA")
        self.lbl_val_total_du = carte_total.lbl_valeur
        cartes.addWidget(carte_total, stretch=1)

        carte_paye = CarteKPI("SOMME VERSÉE", "0 FCFA")
        self.lbl_val_deja_paye = carte_paye.lbl_valeur
        cartes.addWidget(carte_paye, stretch=1)

        carte_solde = CarteKPI("SOLDE RESTANT DÛ", "0 FCFA")
        self.lbl_val_solde = carte_solde.lbl_valeur
        cartes.addWidget(carte_solde, stretch=1)

        carte_statut = CarteKPI("STATUT ACTUEL", "Non payé")
        self.lbl_val_statut = carte_statut.lbl_valeur
        cartes.addWidget(carte_statut, stretch=1)

        layout.addLayout(cartes)

        layout.addWidget(separateur_horizontal())

        # --- Section historique ---
        ligne_titre = QHBoxLayout()
        titre_hist = QLabel("Historique des paiements")
        titre_hist.setObjectName("sectionTitle")
        ligne_titre.addWidget(titre_hist)
        ligne_titre.addStretch()

        lbl_aide = QLabel("Double-cliquez sur une ligne pour consulter le versement.")
        lbl_aide.setObjectName("muted")
        ligne_titre.addWidget(lbl_aide)
        layout.addLayout(ligne_titre)

        self.tableau_paiements = QTableWidget()
        self._configurer_tableau()
        layout.addWidget(self.tableau_paiements, stretch=1)

    def _configurer_tableau(self):
        """Configure le tableau d'historique des versements."""
        self.tableau_paiements.setColumnCount(6)
        self.tableau_paiements.setHorizontalHeaderLabels([
            "N° Reçu", "Date", "Mode de paiement", "Montant payé",
            "Solde après", "Actions",
        ])
        self.tableau_paiements.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tableau_paiements.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.tableau_paiements.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.tableau_paiements.setAlternatingRowColors(True)
        self.tableau_paiements.setShowGrid(False)
        self.tableau_paiements.verticalHeader().setVisible(False)
        self.tableau_paiements.verticalHeader().setDefaultSectionSize(44)

        entete = self.tableau_paiements.horizontalHeader()
        entete.setHighlightSections(False)
        entete.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        entete.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        entete.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        entete.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        entete.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        entete.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.tableau_paiements.doubleClicked.connect(self._sur_double_clic_paiement)

    # ------------------------------------------------------------------
    # Données
    # ------------------------------------------------------------------
    def charger_eleve(self, id_eleve: int):
        """Charge les informations complètes d'un élève et son historique."""
        self.id_eleve = id_eleve
        try:
            eleve = eleve_service.obtenir_eleve(id_eleve)
        except ValueError as e:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Erreur", str(e))
            self.retour_demande.emit()
            return

        # Renseigner l'identité
        nom_complet = f"{eleve['nom']} {eleve['prenom']}"
        self.titre_fiche.setText(
            f"Classe {eleve['classe']}  ·  Année {eleve['annee_scolaire']}"
        )
        self.lbl_nom_complet.setText(nom_complet)
        self.lbl_classe_annee.setText(
            f"Classe : {eleve['classe']}  |  Année scolaire : {eleve['annee_scolaire']}"
        )
        self.lbl_avatar.setText(initiales(eleve["nom"], eleve["prenom"]))

        # Renseigner les montants
        self.lbl_val_total_du.setText(formater_montant(eleve["total_du"]))
        self.lbl_val_deja_paye.setText(formater_montant(eleve["somme_payee"]))
        self.lbl_val_solde.setText(formater_montant(eleve["solde"]))

        # Renseigner le statut avec sa couleur sémantique
        statut = eleve["statut"]
        self.lbl_val_statut.setText(statut)
        self.lbl_val_statut.setStyleSheet(
            f"color: {couleur_statut(statut)}; font-size: 17px; font-weight: 600;"
        )

        # Le solde n'est coloré que sémantiquement (rouge si restant dû)
        self.lbl_val_solde.setStyleSheet(
            f"color: {COULEUR_STATUT['Non payé'] if eleve['solde'] > 0 else COULEUR_STATUT['Soldé']};"
            "font-size: 21px; font-weight: 600;"
        )

        # Adapter le bouton de paiement selon le solde
        if eleve["solde"] == 0:
            self.btn_payer.setEnabled(False)
            self.btn_payer.setToolTip("Cet élève est entièrement soldé.")
        else:
            self.btn_payer.setEnabled(True)
            self.btn_payer.setToolTip("Enregistrer un nouveau paiement pour cet élève.")

        # Charger l'historique des versements
        self._charger_historique()

    def _charger_historique(self):
        """Remplit le tableau d'historique des paiements."""
        if not self.id_eleve:
            return

        paiements = paiement_repository.lister_par_eleve(self.id_eleve)
        self.tableau_paiements.setRowCount(len(paiements))
        self.lbl_recu_count.setText(f"{len(paiements)} versement(s)")

        for ligne, p in enumerate(paiements):
            # 0: N° Reçu
            item_recu = QTableWidgetItem(p["numero_recu"])
            item_recu.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
            item_recu.setData(Qt.ItemDataRole.UserRole, p["id_paiement"])
            self.tableau_paiements.setItem(ligne, 0, item_recu)

            # 1: Date
            self.tableau_paiements.setItem(
                ligne, 1, QTableWidgetItem(formater_date_affichage(p["date_paiement"]))
            )

            # 2: Mode
            self.tableau_paiements.setItem(
                ligne, 2, QTableWidgetItem(libelle_mode_paiement(p["mode_paiement"]))
            )

            # 3: Montant
            item_montant = QTableWidgetItem(formater_montant(p["montant"]))
            item_montant.setForeground(QColor(COULEUR_STATUT["Soldé"]))
            item_montant.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.tableau_paiements.setItem(ligne, 3, item_montant)

            # 4: Solde après
            item_solde = QTableWidgetItem(formater_montant(p["solde_apres"]))
            if p["solde_apres"] == 0:
                item_solde.setForeground(QColor(COULEUR_STATUT["Soldé"]))
            self.tableau_paiements.setItem(ligne, 4, item_solde)

            # 5: Boutons d'action (Consulter et Reçu)
            widget_actions = QWidget()
            layout_actions = QHBoxLayout(widget_actions)
            layout_actions.setContentsMargins(6, 4, 6, 4)
            layout_actions.setSpacing(6)

            btn_details = QPushButton("Détails")
            btn_details.setObjectName("btnIcon")
            btn_details.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_details.clicked.connect(
                lambda _, pid=p["id_paiement"]: self._ouvrir_detail_paiement(pid)
            )
            layout_actions.addWidget(btn_details)

            btn_imprimer = QPushButton("Reçu")
            btn_imprimer.setObjectName("btnIcon")
            btn_imprimer.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_imprimer.clicked.connect(
                lambda _, pid=p["id_paiement"]: self.reimprimer_recu_demande.emit(pid)
            )
            layout_actions.addWidget(btn_imprimer)

            self.tableau_paiements.setCellWidget(ligne, 5, widget_actions)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _action_nouveau_paiement(self):
        """Ouvre le dialogue de paiement et recharge la fiche."""
        if not self.id_eleve:
            return

        from ui.paiement_dialog import DialoguePaiement

        dlg = DialoguePaiement(self, id_eleve=self.id_eleve)
        if dlg.exec():
            # Recharger immédiatement les métriques et l'historique
            self.charger_eleve(self.id_eleve)
            if dlg.imprimer_demande and dlg.paiement_cree:
                self.reimprimer_recu_demande.emit(dlg.paiement_cree["id_paiement"])

    def _ouvrir_detail_paiement(self, id_paiement: int):
        """Affiche la fenêtre détaillée d'un paiement."""
        from ui.paiement_detail import DialogueDetailPaiement

        dlg = DialogueDetailPaiement(self, id_paiement=id_paiement)
        dlg.reimprimer_recu.connect(self.reimprimer_recu_demande.emit)
        dlg.exec()

    def _sur_double_clic_paiement(self, index):
        """Ouvre les détails du paiement lors d'un double-clic sur une ligne."""
        item = self.tableau_paiements.item(index.row(), 0)
        if item:
            id_paiement = item.data(Qt.ItemDataRole.UserRole)
            if id_paiement:
                self._ouvrir_detail_paiement(id_paiement)
