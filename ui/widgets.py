"""
Composants réutilisables du design system EduPaie.

Ces widgets encapsulent les motifs visuels répétés (cartes d'indicateurs,
badges de statut, en-têtes de page) afin de garder les écrans lisibles.
Parti pris : sobriété — pas d'icône décorative, pas de liseré coloré ;
la couleur n'intervient que pour la sémantique (statut de paiement).
"""

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget,
)


def separateur_horizontal() -> QFrame:
    """Retourne un séparateur horizontal d'un pixel."""
    trait = QFrame()
    trait.setObjectName("separator")
    trait.setFixedHeight(1)
    return trait


class CarteKPI(QFrame):
    """Carte d'indicateur clé, sobre : libellé, valeur et légende.

    Les attributs publics `lbl_valeur` et `lbl_sous_titre` permettent de
    rafraîchir le contenu sans reconstruire la carte.

    Args:
        titre: libellé de l'indicateur (petites capitales d'affichage)
        valeur: valeur affichée en grand
        sous_titre: légende secondaire sous la valeur
    """

    def __init__(self, titre: str, valeur: str, sous_titre: str = "",
                 parent=None):
        super().__init__(parent)
        self.setObjectName("kpiCard")

        colonne = QVBoxLayout(self)
        colonne.setContentsMargins(16, 14, 16, 14)
        colonne.setSpacing(3)

        self.lbl_titre = QLabel(titre)
        self.lbl_titre.setObjectName("kpiLabel")
        colonne.addWidget(self.lbl_titre)

        self.lbl_valeur = QLabel(valeur)
        self.lbl_valeur.setObjectName("kpiValue")
        colonne.addWidget(self.lbl_valeur)

        self.lbl_sous_titre = QLabel(sous_titre)
        self.lbl_sous_titre.setObjectName("kpiHint")
        self.lbl_sous_titre.setVisible(bool(sous_titre))
        colonne.addWidget(self.lbl_sous_titre)

    def maj(self, valeur: str, sous_titre: str | None = None):
        """Met à jour la valeur et, si fournie, la légende."""
        self.lbl_valeur.setText(valeur)
        if sous_titre is not None:
            self.lbl_sous_titre.setText(sous_titre)
            self.lbl_sous_titre.setVisible(bool(sous_titre))


class EnTetePage(QWidget):
    """En-tête de page : titre, sous-titre et zone d'actions à droite."""

    def __init__(self, titre: str, sous_titre: str = "", parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)

        colonne = QVBoxLayout()
        colonne.setContentsMargins(0, 0, 0, 0)
        colonne.setSpacing(2)

        self.lbl_titre = QLabel(titre)
        self.lbl_titre.setObjectName("pageTitle")
        colonne.addWidget(self.lbl_titre)

        self.lbl_sous_titre = QLabel(sous_titre)
        self.lbl_sous_titre.setObjectName("pageSubtitle")
        colonne.addWidget(self.lbl_sous_titre)

        self._layout.addLayout(colonne)
        self._layout.addStretch()

    def set_sous_titre(self, texte: str):
        self.lbl_sous_titre.setText(texte)

    def ajouter_action(self, widget: QWidget):
        """Ajoute un widget à droite de l'en-tête."""
        self._layout.addWidget(widget)

    def ajouter_action_gauche(self, widget: QWidget):
        """Ajoute un widget à gauche, avant le titre."""
        self._layout.insertWidget(0, widget)
