"""
Dialogue d'enregistrement d'un paiement.

Formulaire modal permettant d'enregistrer un versement pour un élève :
- Rappel du solde actuel restant
- Saisie du montant à verser (plafonné par défaut au solde restant)
- Choix de la date (par défaut aujourd'hui)
- Sélection du mode de paiement (espèces, chèque, virement, mobile money)
- Enregistrement transactionnel et retour d'information avec le numéro de reçu
"""

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDialog, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QMessageBox, QPushButton, QSpinBox, QVBoxLayout,
)

from services import eleve_service, paiement_service
from ui.theme import PALETTE, creer_carte
from ui.utils import formater_montant


class DialoguePaiement(QDialog):
    """Dialogue modal pour enregistrer un versement de scolarité."""

    def __init__(self, parent=None, id_eleve: int = None):
        super().__init__(parent)
        self.id_eleve = id_eleve
        self.paiement_cree = None  # Contient les données du paiement après succès
        self.imprimer_demande = False

        self.setWindowTitle("Enregistrer un paiement — EduPaie")
        self.setMinimumWidth(520)
        self.setModal(True)

        self._charger_infos_eleve()
        self._construire_interface()

    def _charger_infos_eleve(self):
        """Récupère les informations et le solde courant de l'élève."""
        try:
            self.eleve = eleve_service.obtenir_eleve(self.id_eleve)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger l'élève : {e}")
            self.reject()

    def _construire_interface(self):
        """Construit l'interface du formulaire de paiement."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        # --- En-tête ---
        titre = QLabel("Nouveau versement scolaire")
        titre.setObjectName("pageTitle")
        layout.addWidget(titre)

        sous_titre = QLabel(
            "Le versement est enregistré de façon transactionnelle et "
            "un numéro de reçu unique lui est attribué."
        )
        sous_titre.setObjectName("pageSubtitle")
        sous_titre.setWordWrap(True)
        layout.addWidget(sous_titre)

        # --- Bandeau récapitulatif de l'élève ---
        bandeau = QFrame()
        bandeau.setObjectName("infoBanner")
        bandeau_layout = QVBoxLayout(bandeau)
        bandeau_layout.setContentsMargins(16, 12, 16, 12)
        bandeau_layout.setSpacing(4)

        nom_lbl = QLabel(
            f"{self.eleve['nom']} {self.eleve['prenom']} "
            f"— {self.eleve['classe']}"
        )
        nom_lbl.setStyleSheet(
            f"color: {PALETTE['primaryDark']}; font-weight: 700; font-size: 14px;"
        )
        bandeau_layout.addWidget(nom_lbl)

        frais_lbl = QLabel(
            f"Total des frais annuels : {formater_montant(self.eleve['total_du'])}"
        )
        frais_lbl.setObjectName("muted")
        bandeau_layout.addWidget(frais_lbl)

        solde_lbl = QLabel(
            f"Solde restant à régler : "
            f"<span style='color:{PALETTE['danger']}; font-weight:700;'>"
            f"{formater_montant(self.eleve['solde'])}</span>"
        )
        bandeau_layout.addWidget(solde_lbl)

        layout.addWidget(bandeau)

        # --- Carte contenant le formulaire ---
        carte = creer_carte()
        formulaire = QFormLayout(carte)
        formulaire.setContentsMargins(18, 18, 18, 18)
        formulaire.setSpacing(13)
        formulaire.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 1. Montant (+ bouton de remplissage rapide)
        self.champ_montant = QSpinBox()
        self.champ_montant.setMinimum(1)
        self.champ_montant.setMaximum(10_000_000)
        self.champ_montant.setSingleStep(5000)
        self.champ_montant.setSuffix(" FCFA")
        solde_dispo = max(1, self.eleve["solde"])
        self.champ_montant.setValue(solde_dispo)

        ligne_montant = QHBoxLayout()
        ligne_montant.setSpacing(8)
        ligne_montant.addWidget(self.champ_montant, stretch=1)

        btn_solde = QPushButton("Tout régler")
        btn_solde.setObjectName("btnGhost")
        btn_solde.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_solde.setToolTip("Régler la totalité du solde restant")
        btn_solde.clicked.connect(
            lambda: self.champ_montant.setValue(solde_dispo)
        )
        ligne_montant.addWidget(btn_solde)
        formulaire.addRow("Montant versé :", ligne_montant)

        # 2. Date de versement
        self.champ_date = QDateEdit()
        self.champ_date.setDate(QDate.currentDate())
        self.champ_date.setCalendarPopup(True)
        self.champ_date.setDisplayFormat("dd/MM/yyyy")
        self.champ_date.setMaximumDate(QDate.currentDate())
        try:
            annee_debut = int(self.eleve["annee_scolaire"].split("-")[0].strip())
        except Exception:
            annee_debut = int(str(self.eleve["annee_scolaire"])[:4])
        self.champ_date.setMinimumDate(QDate(annee_debut, 1, 1))
        formulaire.addRow("Date du paiement :", self.champ_date)

        # 3. Mode de paiement
        self.champ_mode = QComboBox()
        self.modes_map = [
            ("Espèces", "especes"),
            ("Mobile Money (Orange/Moov/Wave)", "mobile_money"),
            ("Chèque bancaire", "cheque"),
            ("Virement bancaire", "virement"),
        ]
        for libelle, code in self.modes_map:
            self.champ_mode.addItem(libelle, code)
        formulaire.addRow("Mode de règlement :", self.champ_mode)

        layout.addWidget(carte)

        # --- Option d'impression immédiate ---
        self.check_imprimer = QCheckBox(
            "Générer et ouvrir le reçu PDF immédiatement"
        )
        self.check_imprimer.setChecked(True)
        layout.addWidget(self.check_imprimer)

        # --- Boutons d'action ---
        boutons = QHBoxLayout()
        boutons.addStretch()

        btn_annuler = QPushButton("Annuler")
        btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_annuler.clicked.connect(self.reject)
        boutons.addWidget(btn_annuler)

        btn_valider = QPushButton("Confirmer le paiement")
        btn_valider.setObjectName("btnSuccess")
        btn_valider.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_valider.setDefault(True)
        btn_valider.clicked.connect(self._valider_paiement)
        boutons.addWidget(btn_valider)

        layout.addLayout(boutons)

    def _valider_paiement(self):
        """Valide et enregistre le paiement via le service métier."""
        montant = self.champ_montant.value()
        date_qdate = self.champ_date.date()
        date_iso = (
            f"{date_qdate.year():04d}-{date_qdate.month():02d}-"
            f"{date_qdate.day():02d}"
        )
        mode = self.champ_mode.currentData()

        # Vérification préventive côté interface
        if montant <= 0:
            QMessageBox.warning(
                self, "Montant invalide",
                "Le montant doit être strictement supérieur à 0.",
            )
            return

        if montant > self.eleve["solde"]:
            QMessageBox.warning(
                self,
                "Dépassement du solde",
                f"Le montant saisi ({formater_montant(montant)}) dépasse le "
                f"solde dû ({formater_montant(self.eleve['solde'])}).\n\n"
                "Un paiement ne peut pas rendre le solde négatif.",
            )
            return

        # Appel au service métier transactionnel
        try:
            res = paiement_service.enregistrer_paiement(
                id_eleve=self.id_eleve,
                montant=montant,
                date_paiement=date_iso,
                mode_paiement=mode,
            )
            self.paiement_cree = res
            self.imprimer_demande = self.check_imprimer.isChecked()

            QMessageBox.information(
                self,
                "Paiement enregistré avec succès",
                f"Le paiement de {formater_montant(montant)} a été enregistré !\n\n"
                f"Numéro de reçu attribué : {res['numero_recu']}\n"
                f"Nouveau solde restant : {formater_montant(res['solde_apres'])}",
            )
            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Paiement refusé", str(e))
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur inattendue",
                f"Une erreur s'est produite lors de l'enregistrement : {e}",
            )
