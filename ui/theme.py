"""
Design system EduPaie — palette, feuille de style globale et helpers.

Toute l'identité visuelle de l'application est centralisée ici afin que
les écrans restent purement déclaratifs (ils posent un `objectName` et la
feuille de style s'occupe du rendu).

Parti pris graphique : sobre et monochrome. Barre latérale noire, surfaces
blanches, bordures grises neutres. La couleur est réservée à la sémantique
(statuts de paiement : vert / orange / rouge).

Usage :
    from ui.theme import appliquer_theme
    appliquer_theme(app)

Conventions d'`objectName` utilisables dans les écrans :
    sidebar, sidebarWordmark, sidebarTagline, sidebarSection, sidebarFooter,
    sidebarDivider, sidebarInfo, sidebarInfoTitle, sidebarInfoText, navButton,
    sidebarCta, pageTitle, pageSubtitle, sectionTitle, muted, card, kpiCard,
    kpiLabel, kpiValue, kpiHint, kpiAccent, heroCard, heroName, heroMeta,
    heroAvatar, infoBanner, btnPrimary, btnSuccess, btnDanger, btnGhost,
    btnIcon, searchField, separator
"""

from string import Template

from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import QFrame, QWidget


# ---------------------------------------------------------------------------
# 1. Palette sobre (neutre + accents sémantiques uniquement)
# ---------------------------------------------------------------------------
PALETTE = {
    # Marque : indigo discret, réservé aux éléments interactifs clés
    "primary": "#374151",        # gris anthracite (boutons principaux)
    "primaryDark": "#1F2937",
    "primaryLight": "#F3F4F6",   # gris très clair (sélection, fonds doux)
    "primarySoft": "#E5E7EB",
    "violet": "#374151",
    "accent": "#374151",

    # Surfaces
    "bg": "#F5F5F5",
    "surface": "#FFFFFF",
    "surfaceAlt": "#FAFAFA",
    "border": "#E5E5E5",
    "borderStrong": "#D4D4D4",

    # Textes
    "text": "#171717",
    "textMuted": "#525252",
    "textSoft": "#737373",
    "textOnDark": "#FFFFFF",

    # Sidebar : noir profond, dégradé à peine perceptible
    "sidebarTop": "#0A0A0A",
    "sidebarBottom": "#151414",

    # Sémantique (statuts uniquement)
    "success": "#15803D",
    "successBg": "#F0FDF4",
    "warning": "#B45309",
    "warningBg": "#FFFBEB",
    "danger": "#B91C1C",
    "dangerBg": "#FEF2F2",
    "info": "#1D4ED8",
    "infoBg": "#EFF6FF",

    # Tableaux
    "rowHover": "#FAFAFA",
    "rowSelected": "#F3F4F6",
}

#: Couleurs de statut de paiement (réutilisées par ui/utils.py)
COULEUR_STATUT = {
    "Soldé": PALETTE["success"],
    "Partiellement payé": PALETTE["warning"],
    "Non payé": PALETTE["danger"],
}

FAMILLE_POLICE = '"Segoe UI", "Inter", "Noto Sans", Arial, sans-serif'


# ---------------------------------------------------------------------------
# 2. Feuille de style globale
# ---------------------------------------------------------------------------
_QSS = Template(r"""
QWidget {
    color: $text;
    font-family: $family;
    font-size: 13px;
}

QMainWindow, QDialog {
    background-color: $bg;
}

QToolTip {
    background-color: $text;
    color: $textOnDark;
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
}

/* ------------------------------- Sidebar ------------------------------- */
QWidget#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 $sidebarTop, stop:1 $sidebarBottom);
    border: none;
}
QLabel#sidebarWordmark {
    color: $textOnDark;
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 0.3px;
}
QLabel#sidebarTagline {
    color: #D4D4D4;
    font-size: 11px;
}
QLabel#sidebarSection {
    color: #A3A3A3;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.2px;
    padding: 0 14px;
}
QLabel#sidebarFooter {
    color: #A3A3A3;
    font-size: 10px;
}
QFrame#sidebarDivider {
    background-color: #262626;
    border: none;
}
QFrame#sidebarInfo {
    background-color: #111111;
    border: 1px solid #262626;
    border-radius: 10px;
}
QLabel#sidebarInfoTitle {
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 600;
}
QLabel#sidebarInfoText {
    color: #D4D4D4;
    font-size: 10px;
}

QPushButton#navButton {
    color: #E5E5E5;
    background-color: transparent;
    border: none;
    border-radius: 8px;
    text-align: left;
    padding: 0 14px;
    font-size: 13.5px;
    min-height: 42px;
}
QPushButton#navButton:hover {
    background-color: #1F1F1F;
    color: $textOnDark;
}
QPushButton#navButton:checked {
    background-color: $textOnDark;
    color: $text;
    font-weight: 600;
}

QPushButton#sidebarCta {
    background-color: $textOnDark;
    color: $text;
    border: none;
    border-radius: 8px;
    min-height: 38px;
    font-weight: 600;
}
QPushButton#sidebarCta:hover {
    background-color: #E5E5E5;
}
QPushButton#sidebarCta:pressed {
    background-color: #D4D4D4;
}

/* ------------------------------ Typographie ---------------------------- */
QLabel#pageTitle {
    font-size: 22px;
    font-weight: 600;
    color: $text;
}
QLabel#pageSubtitle {
    font-size: 12.5px;
    color: $textMuted;
}
QLabel#sectionTitle {
    font-size: 14.5px;
    font-weight: 600;
    color: $text;
}
QLabel#muted {
    color: $textMuted;
}

/* -------------------------------- Cartes ------------------------------- */
QFrame#card {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 12px;
}
QFrame#kpiCard {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 12px;
}
QLabel#kpiLabel {
    color: $textMuted;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.6px;
}
QLabel#kpiValue {
    font-size: 21px;
    font-weight: 600;
    color: $text;
}
QLabel#kpiHint {
    color: $textSoft;
    font-size: 11px;
}
QFrame#kpiAccent {
    border: none;
    border-radius: 0px;
}
QFrame#heroCard {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 12px;
}
QLabel#heroName {
    color: $text;
    font-size: 20px;
    font-weight: 600;
}
QLabel#heroMeta {
    color: $textMuted;
    font-size: 12px;
}
QLabel#heroAvatar {
    background-color: $text;
    border: none;
    border-radius: 26px;
    color: $textOnDark;
    font-size: 18px;
    font-weight: 600;
    qproperty-alignment: AlignCenter;
}
QFrame#infoBanner {
    background-color: $primaryLight;
    border: 1px solid $border;
    border-radius: 10px;
}

/* -------------------------------- Boutons ------------------------------ */
QPushButton {
    background-color: $surface;
    color: $text;
    border: 1px solid $borderStrong;
    border-radius: 8px;
    padding: 7px 16px;
    min-height: 22px;
    font-size: 13px;
}
QPushButton:hover {
    background-color: $surfaceAlt;
    border-color: #A3A3A3;
}
QPushButton:pressed {
    background-color: $primaryLight;
}
QPushButton:disabled {
    color: $textSoft;
    background-color: $surfaceAlt;
    border-color: $border;
}

QPushButton#btnPrimary {
    background-color: $text;
    color: $textOnDark;
    border: 1px solid $text;
    font-weight: 600;
}
QPushButton#btnPrimary:hover {
    background-color: #333333;
    border-color: #333333;
}
QPushButton#btnPrimary:pressed {
    background-color: $primaryDark;
}
QPushButton#btnPrimary:disabled {
    background-color: $primarySoft;
    border-color: $primarySoft;
    color: $textSoft;
}

QPushButton#btnSuccess {
    background-color: $text;
    color: $textOnDark;
    border: 1px solid $text;
    font-weight: 600;
}
QPushButton#btnSuccess:hover {
    background-color: #333333;
    border-color: #333333;
}
QPushButton#btnSuccess:pressed {
    background-color: $primaryDark;
}
QPushButton#btnSuccess:disabled {
    background-color: $primarySoft;
    border-color: $primarySoft;
    color: $textSoft;
}

QPushButton#btnDanger {
    background-color: $surface;
    color: $danger;
    border: 1px solid $borderStrong;
    font-weight: 600;
}
QPushButton#btnDanger:hover {
    background-color: $dangerBg;
    border-color: #FCA5A5;
}

QPushButton#btnGhost {
    background-color: transparent;
    color: $text;
    border: 1px solid $borderStrong;
    font-weight: 600;
}
QPushButton#btnGhost:hover {
    background-color: $primaryLight;
}

QPushButton#btnIcon {
    background-color: $surface;
    border: 1px solid $borderStrong;
    border-radius: 7px;
    padding: 3px 9px;
    font-size: 11.5px;
    color: $text;
}
QPushButton#btnIcon:hover {
    background-color: $primaryLight;
    border-color: #A3A3A3;
}

/* -------------------------------- Champs ------------------------------- */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
    background-color: $surface;
    border: 1px solid $borderStrong;
    border-radius: 8px;
    padding: 6px 11px;
    min-height: 22px;
    selection-background-color: $primarySoft;
    selection-color: $text;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QDateEdit:focus {
    border: 1.5px solid #525252;
    background-color: #FFFFFF;
}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDateEdit:disabled {
    background-color: $surfaceAlt;
    color: $textSoft;
}
QLineEdit#searchField {
    padding-left: 12px;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 28px;
    border: none;
    background: transparent;
}
QComboBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid $textMuted;
    margin-right: 10px;
}
QComboBox QAbstractItemView {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 4px;
    outline: none;
    selection-background-color: $primaryLight;
    selection-color: $text;
}

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    width: 18px;
    border: none;
    background: transparent;
}
QDateEdit::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border: none;
    background: transparent;
}

/* ------------------------------ Tableaux ------------------------------- */
QTableView {
    background-color: $surface;
    alternate-background-color: $surfaceAlt;
    border: 1px solid $border;
    border-radius: 10px;
    gridline-color: $border;
    selection-background-color: $rowSelected;
    selection-color: $text;
    outline: none;
}
QTableView::item {
    padding: 6px 10px;
    border: none;
}
QTableView::item:hover {
    background-color: $rowHover;
}
QTableView::item:selected {
    background-color: $rowSelected;
    color: $text;
}
QHeaderView {
    background-color: transparent;
}
QHeaderView::section {
    background-color: $surfaceAlt;
    color: $textMuted;
    padding: 10px 12px;
    border: none;
    border-bottom: 1px solid $border;
    border-right: 1px solid $border;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.4px;
}
QHeaderView::section:first {
    border-top-left-radius: 10px;
}
QHeaderView::section:last {
    border-right: none;
    border-top-right-radius: 10px;
}
QTableCornerButton::section {
    background-color: $surfaceAlt;
    border: none;
}

/* --------------------------- Cases à cocher ---------------------------- */
QCheckBox {
    color: $text;
    spacing: 9px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1.5px solid $borderStrong;
    border-radius: 5px;
    background-color: $surface;
}
QCheckBox::indicator:hover {
    border-color: #525252;
}
QCheckBox::indicator:checked {
    background-color: $text;
    border-color: $text;
}

/* ----------------------------- Ascenseurs ------------------------------ */
QScrollBar:vertical {
    background: transparent;
    width: 11px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background-color: #D4D4D4;
    border-radius: 5px;
    min-height: 32px;
}
QScrollBar::handle:vertical:hover {
    background-color: #A3A3A3;
}
QScrollBar:horizontal {
    background: transparent;
    height: 11px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background-color: #D4D4D4;
    border-radius: 5px;
    min-width: 32px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #A3A3A3;
}
QScrollBar::add-line, QScrollBar::sub-line {
    height: 0;
    width: 0;
    background: none;
    border: none;
}
QScrollBar::add-page, QScrollBar::sub-page {
    background: none;
}

/* --------------------------- Barres & divers --------------------------- */
QFrame#separator {
    background-color: $border;
    border: none;
}
QMessageBox {
    background-color: $surface;
}
QMessageBox QLabel {
    color: $text;
}
QProgressBar {
    background-color: $surfaceAlt;
    border: 1px solid $border;
    border-radius: 7px;
    height: 12px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: $text;
    border-radius: 6px;
}
""")


# ---------------------------------------------------------------------------
# 3. Helpers
# ---------------------------------------------------------------------------
def _palette_complete() -> dict:
    """Retourne la palette enrichie des valeurs dérivées."""
    valeurs = dict(PALETTE)
    valeurs.setdefault("family", FAMILLE_POLICE)
    return valeurs


def feuille_de_style() -> str:
    """Construit la feuille de style Qt complète depuis la palette."""
    return _QSS.substitute(_palette_complete())


def appliquer_theme(app):
    """Applique l'identité visuelle globale à l'application Qt.

    Args:
        app: instance de QApplication (ou QGuiApplication)
    """
    app.setStyle("Fusion")
    police = QFont("Segoe UI", 10)
    police.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(police)
    app.setStyleSheet(feuille_de_style())
    return app


def creer_carte(parent=None, object_name: str = "card") -> QFrame:
    """Crée un cadre « carte » cohérent avec le design system."""
    cadre = QFrame(parent)
    cadre.setObjectName(object_name)
    return cadre


def activer_fond_stylise(widget: QWidget):
    """Force le rendu du fond CSS pour un QWidget nu (non-QFrame)."""
    from PySide6.QtCore import Qt

    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    return widget


def pixmap_logo(taille: int = 256) -> QPixmap:
    """Rend le logo de l'application dans un QPixmap (import paresseux).

    L'import de ui.logo est différé pour éviter une dépendance circulaire.
    """
    from ui.logo import rendre_logo

    return rendre_logo(taille)


def icone_application() -> QIcon:
    """Construit l'icône de l'application (fichier .ico s'il existe)."""
    import os

    from utils.paths import resource_path

    icone = QIcon()
    for nom in ("resources/icon.ico", "resources/logo.png"):
        chemin = resource_path(nom)
        if os.path.exists(chemin):
            icone.addFile(chemin)
    if icone.isNull():
        # Repli : rendu vectoriel direct, disponible même sans assets générés
        pix = pixmap_logo(256)
        icone = QIcon(pix)
    return icone
