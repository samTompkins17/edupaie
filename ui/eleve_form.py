"""
Formulaire d'ajout et de modification d'un élève.

Dialogue modal avec les champs : nom, prénom, classe, année scolaire,
montant total dû. Valide les saisies avant soumission.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QSpinBox, QVBoxLayout,
)

from services import eleve_service
from services.eleve_service import CLASSES_AUTORISEES
from ui.theme import creer_carte


class FormulaireEleve(QDialog):
    """Dialogue modal pour ajouter ou modifier un élève.

    Args:
        parent: Widget parent
        eleve: Dictionnaire de l'élève à modifier (None pour un ajout)
    """

    def __init__(self, parent=None, eleve: dict | None = None):
        super().__init__(parent)
        self.eleve = eleve
        self.id_cree = None  # Stocke l'id du nouvel élève après ajout

        # Configuration de la fenêtre
        if eleve:
            self.setWindowTitle("Modifier un élève")
        else:
            self.setWindowTitle("Ajouter un élève")
        self.setMinimumWidth(520)
        self.setModal(True)

        self._construire_interface()

        # Pré-remplir si modification
        if eleve:
            self._preremplir(eleve)

    def _construire_interface(self):
        """Construit le formulaire avec tous les champs."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        # --- En-tête ---
        titre = QLabel(self.windowTitle().split(" — ")[0])
        titre.setObjectName("pageTitle")
        layout.addWidget(titre)

        sous_titre = QLabel(
            "Renseignez l'état civil et le montant annuel des frais de scolarité."
        )
        sous_titre.setObjectName("pageSubtitle")
        layout.addWidget(sous_titre)

        # --- Carte contenant le formulaire ---
        carte = creer_carte()
        formulaire = QFormLayout(carte)
        formulaire.setContentsMargins(18, 18, 18, 18)
        formulaire.setSpacing(12)
        formulaire.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Champ Nom
        self.champ_nom = QLineEdit()
        self.champ_nom.setPlaceholderText("Ex : DIALLO")
        formulaire.addRow("Nom :", self.champ_nom)

        # Champ Prénom
        self.champ_prenom = QLineEdit()
        self.champ_prenom.setPlaceholderText("Ex : Aminata")
        formulaire.addRow("Prénom :", self.champ_prenom)

        # Champ Classe (liste fermée : 6ème, 5ème, 4ème, 3ème)
        self.champ_classe = QComboBox()
        self.champ_classe.addItems(CLASSES_AUTORISEES)
        formulaire.addRow("Classe :", self.champ_classe)

        # Champ Année scolaire
        self.champ_annee = QComboBox()
        self.champ_annee.setEditable(True)
        self.champ_annee.addItems([
            "2025-2026", "2026-2027", "2027-2028",
        ])
        formulaire.addRow("Année scolaire :", self.champ_annee)

        # Champ Montant total dû
        self.champ_total_du = QSpinBox()
        self.champ_total_du.setMinimum(0)
        self.champ_total_du.setMaximum(10_000_000)  # 10 millions FCFA max
        self.champ_total_du.setSingleStep(5000)
        self.champ_total_du.setSuffix(" FCFA")
        formulaire.addRow("Total des frais :", self.champ_total_du)

        layout.addWidget(carte)

        # --- Boutons Valider / Annuler ---
        boutons = QHBoxLayout()
        boutons.addStretch()

        btn_annuler = QPushButton("Annuler")
        btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_annuler.clicked.connect(self.reject)
        boutons.addWidget(btn_annuler)

        btn_valider = QPushButton("Enregistrer")
        btn_valider.setObjectName("btnPrimary")
        btn_valider.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_valider.setDefault(True)
        btn_valider.clicked.connect(self._valider)
        boutons.addWidget(btn_valider)

        layout.addLayout(boutons)

    def _preremplir(self, eleve: dict):
        """Pré-remplit les champs avec les données de l'élève à modifier."""
        self.champ_nom.setText(eleve["nom"])
        self.champ_prenom.setText(eleve["prenom"])
        self.champ_classe.setCurrentText(eleve["classe"])
        self.champ_annee.setCurrentText(eleve["annee_scolaire"])
        self.champ_total_du.setValue(eleve["total_du"])

    def _valider(self):
        """Valide les saisies et enregistre l'élève."""
        nom = self.champ_nom.text().strip()
        prenom = self.champ_prenom.text().strip()
        classe = self.champ_classe.currentText().strip()
        annee = self.champ_annee.currentText().strip()
        total_du = self.champ_total_du.value()

        try:
            if self.eleve:
                # Modification
                eleve_service.modifier_eleve(
                    self.eleve["id_eleve"], nom, prenom, classe, annee, total_du
                )
                QMessageBox.information(
                    self, "Succès",
                    f"L'élève {nom} {prenom} a été modifié avec succès."
                )
            else:
                # Ajout
                self.id_cree = eleve_service.ajouter_eleve(
                    nom, prenom, classe, annee, total_du
                )
                QMessageBox.information(
                    self, "Succès",
                    f"L'élève {nom} {prenom} a été ajouté avec succès."
                )
            self.accept()

        except ValueError as e:
            # Erreur de validation métier → message clair
            QMessageBox.warning(self, "Erreur de saisie", str(e))
