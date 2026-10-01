"""
Logo vectoriel EduPaie.

Le logo est entièrement dessiné avec QPainter : il reste net à toutes les
tailles et ne dépend d'aucun fichier image externe (l'icône .ico générée
pour l'exécutable provient exactement de ce même code).

Composition :
    - un badge « squircle » dégradé indigo → violet ;
    - une toque de diplômé (éducation) ;
    - une pièce marquée d'un « F » (finance / FCFA).

Usage :
    from ui.logo import LogoWidget, rendre_logo
    widget = LogoWidget(44)
    pixmap = rendre_logo(256)
"""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (
    QBrush, QColor, QLinearGradient, QPainter, QPainterPath,
    QPen, QPixmap,
)
from PySide6.QtWidgets import QWidget

# Teintes de marque (dupliquées volontairement : le logo doit pouvoir être
# rendu hors application graphique, par ex. depuis un script de build).
INDIGO = "#ECEBF4"
VIOLET = "#181321"


def dessiner_logo(painter: QPainter, taille: int, avec_badge: bool = True):
    """Dessine le logo EduPaie dans un carré de `taille` pixels.

    Args:
        painter: QPainter déjà actif
        taille: côté du carré de rendu en pixels
        avec_badge: si False, ne dessine que la toque et la pièce
            (utile sur un fond clair ou pour un filigrane)
    """
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    painter.scale(taille, taille)  # on travaille en coordonnées 0..1

    # ------------------------------------------------------------------
    # 1. Badge dégradé
    # ------------------------------------------------------------------
    marge = 0.015
    if avec_badge:
        cadre = QRectF(marge, marge, 1 - 2 * marge, 1 - 2 * marge)
        rayon = 0.235
        chemin_badge = QPainterPath()
        chemin_badge.addRoundedRect(cadre, rayon, rayon)

        degrade = QLinearGradient(0, 0, 1, 1)
        degrade.setColorAt(0.0, QColor(INDIGO))
        degrade.setColorAt(1.0, QColor(VIOLET))
        painter.fillPath(chemin_badge, QBrush(degrade))

        # Léger halo clair en haut pour donner du relief au badge
        halo = QLinearGradient(0, 0, 0, 1)
        halo.setColorAt(0.0, QColor(255, 255, 255, 38))
        halo.setColorAt(0.45, QColor(255, 255, 255, 0))
        painter.fillPath(chemin_badge, QBrush(halo))

    blanc = QColor("#FFFFFF")

    # ------------------------------------------------------------------
    # 2. Toque de diplômé (mortier)
    # ------------------------------------------------------------------
    plateau = QPainterPath()
    plateau.moveTo(0.50, 0.185)
    plateau.lineTo(0.795, 0.315)
    plateau.lineTo(0.50, 0.445)
    plateau.lineTo(0.205, 0.315)
    plateau.closeSubpath()
    painter.fillPath(plateau, QBrush(blanc))

    # Corps de la toque (calotte)
    calotte = QPainterPath()
    calotte.moveTo(0.355, 0.365)
    calotte.lineTo(0.645, 0.365)
    calotte.lineTo(0.615, 0.520)
    calotte.quadTo(0.50, 0.565, 0.385, 0.520)
    calotte.closeSubpath()
    couleur_calotte = QColor(255, 255, 255, 232)
    painter.fillPath(calotte, QBrush(couleur_calotte))

    # Pompon relié au plateau (petit pompon rond à droite)
    pen_pompon = QPen(blanc)
    pen_pompon.setWidthF(0.028)
    pen_pompon.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen_pompon)
    pompon = QPainterPath()
    pompon.moveTo(0.775, 0.325)
    pompon.cubicTo(0.878, 0.355, 0.862, 0.452, 0.830, 0.475)
    painter.drawPath(pompon)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(blanc))
    painter.drawEllipse(QRectF(0.800, 0.455, 0.062, 0.062))

    # ------------------------------------------------------------------
    # 3. Pièce de monnaie marquée « F » (finance / FCFA)
    # ------------------------------------------------------------------
    centre_x, centre_y, rayon_piece = 0.50, 0.715, 0.163
    piece = QRectF(
        centre_x - rayon_piece, centre_y - rayon_piece,
        2 * rayon_piece, 2 * rayon_piece,
    )
    painter.setBrush(QBrush(blanc))
    painter.drawEllipse(piece)

    # Anneau intérieur
    pen_anneau = QPen(QColor(INDIGO))
    pen_anneau.setWidthF(0.022)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(pen_anneau)
    marge_anneau = 0.030
    painter.drawEllipse(piece.adjusted(marge_anneau, marge_anneau,
                                       -marge_anneau, -marge_anneau))

    # Symbole « F » centré (dessiné en traits pour rester fidèle
    # indépendamment des polices installées)
    t = 0.062   # épaisseur du trait du F (unités relatives)
    # Barre verticale
    painter.fillRect(QRectF(0.440, 0.640, t, 0.150), QColor(INDIGO))
    # Barre supérieure
    painter.fillRect(QRectF(0.440, 0.640, 0.105, t), QColor(INDIGO))
    # Barre médiane
    painter.fillRect(QRectF(0.440, 0.686, 0.085, t), QColor(INDIGO))

    painter.restore()


def rendre_logo(taille: int = 256, avec_badge: bool = True) -> QPixmap:
    """Retourne un QPixmap du logo (fond transparent autour du badge)."""
    pixmap = QPixmap(taille, taille)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    dessiner_logo(painter, taille, avec_badge=avec_badge)
    painter.end()
    return pixmap


class LogoWidget(QWidget):
    """Widget affichant le logo, redimensionnable et net en haute densité."""

    def __init__(self, taille: int = 44, parent=None):
        super().__init__(parent)
        self._taille = taille
        self.setFixedSize(taille, taille)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def setTaille(self, taille: int):
        """Change la taille du logo et déclenche un repaint."""
        self._taille = taille
        self.setFixedSize(taille, taille)
        self.update()

    def paintEvent(self, event):  # noqa: N802 (API Qt)
        ratio = self.devicePixelRatioF()
        pixmap = QPixmap(int(self._taille * ratio), int(self._taille * ratio))
        pixmap.fill(Qt.GlobalColor.transparent)
        pixmap.setDevicePixelRatio(ratio)
        painter = QPainter(pixmap)
        dessiner_logo(painter, int(self._taille * ratio))
        painter.end()

        painter_widget = QPainter(self)
        painter_widget.drawPixmap(0, 0, pixmap)
        painter_widget.end()
