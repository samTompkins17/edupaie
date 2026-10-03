"""
Dialogue de consultation détaillée d'un paiement effectué.

Permet de reconsulter l'intégralité des données d'un versement passé :
élève concerné, date, montant, mode de règlement, solde après paiement,
et propose un bouton d'accès direct au reçu PDF.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout,
)

from services import recu_service
from ui.theme import PALETTE, creer_carte
from ui.utils import (
    formater_date_affichage, formater_montant, libelle_mode_paiement,
)


class DialogueDetailPaiement(QDialog):
    """Dialogue de consultation d'un versement et réimpression de son reçu."""

    reimprimer_recu = Signal(int)  # émet id_paiement

    def __init__(self, parent=None, id_paiement: int | None = None):
        super().__init__(parent)
        self.id_paiement = id_paiement

        self.setWindowTitle("Détails du versement — EduPaie")
        self.setMinimumWidth(500)
        self.setModal(True)

        self.donnees = recu_service.obtenir_donnees_recu(id_paiement)
        self._construire_interface()

    def _construire_interface(self):
        """Construit l'affichage clair et structuré du paiement."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        # --- En-tête coloré avec le numéro de reçu ---
        cadre_entete = QFrame()
        cadre_entete.setObjectName("infoBanner")
        layout_entete = QVBoxLayout(cadre_entete)
        layout_entete.setContentsMargins(16, 12, 16, 12)
        layout_entete.setSpacing(2)

        titre = QLabel(f"Reçu N° {self.donnees['numero_recu']}")
        titre.setStyleSheet(
            f"color: {PALETTE['primaryDark']};"
            "font-family: Consolas, monospace;"
            "font-size: 16px; font-weight: 700;"
        )
        layout_entete.addWidget(titre)

        date_lbl = QLabel(
            f"Émis le {formater_date_affichage(self.donnees['date_paiement'])}"
        )
        date_lbl.setObjectName("muted")
        layout_entete.addWidget(date_lbl)

        layout.addWidget(cadre_entete)

        # --- Carte des détails ---
        carte = creer_carte()
        formulaire = QFormLayout(carte)
        formulaire.setContentsMargins(18, 18, 18, 18)
        formulaire.setSpacing(11)
        formulaire.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        nom_eleve = f"{self.donnees['nom']} {self.donnees['prenom']}"
        formulaire.addRow("<b>Élève :</b>", QLabel(nom_eleve))
        formulaire.addRow("<b>Classe :</b>", QLabel(self.donnees["classe"]))
        formulaire.addRow(
            "<b>Année scolaire :</b>", QLabel(self.donnees["annee_scolaire"])
        )
        formulaire.addRow(
            "<b>Frais annuels dus :</b>",
            QLabel(formater_montant(self.donnees["total_du"])),
        )
        formulaire.addRow(
            "<b>Mode de versement :</b>",
            QLabel(libelle_mode_paiement(self.donnees["mode_paiement"])),
        )

        lbl_montant = QLabel(formater_montant(self.donnees["montant"]))
        lbl_montant.setStyleSheet(
            f"color: {PALETTE['success']}; font-size: 14px; font-weight: 700;"
        )
        formulaire.addRow("<b>Montant réglé :</b>", lbl_montant)

        lbl_solde = QLabel(formater_montant(self.donnees["solde_apres"]))
        lbl_solde.setStyleSheet(
            f"color: {PALETTE['danger']}; font-size: 14px; font-weight: 700;"
        )
        formulaire.addRow("<b>Solde restant après versement :</b>", lbl_solde)

        layout.addWidget(carte)

        # --- Boutons ---
        boutons = QHBoxLayout()
        boutons.setSpacing(10)

        btn_fermer = QPushButton("Fermer")
        btn_fermer.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_fermer.clicked.connect(self.accept)
        boutons.addWidget(btn_fermer)

        boutons.addStretch()

        btn_imprimer = QPushButton("Voir / Imprimer le reçu")
        btn_imprimer.setObjectName("btnPrimary")
        btn_imprimer.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_imprimer.clicked.connect(self._action_imprimer)
        boutons.addWidget(btn_imprimer)

        layout.addLayout(boutons)

    def _action_imprimer(self):
        """Déclenche la réimpression du reçu."""
        self.reimprimer_recu.emit(self.id_paiement)
