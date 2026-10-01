"""
Génération des ressources de marque EduPaie.

Le logo est défini une seule fois dans `ui/logo.py` (dessin vectoriel
QPainter). Ce script le rend en plusieurs tailles et produit :

    resources/logo.png        → 512 px (affichages généraux)
    resources/logo_256.png    → 256 px
    resources/logo_128.png    → 128 px
    resources/logo_48.png     →  48 px
    resources/logo_32.png     →  32 px
    resources/icon.ico        → icône multi-tailles pour l'exécutable

Usage :
    python tools/generate_assets.py
"""

import os
import struct
import sys

# Rendu hors écran : aucune fenêtre n'est nécessaire pour produire les images
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Rendre le dossier racine du projet importable
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter

from ui.logo import dessiner_logo

DOSSIER_RESSOURCES = os.path.join(RACINE, "resources")

#: Tailles PNG exportées
TAILLES_PNG = [512, 256, 128, 48, 32]
#: Tailles intégrées dans le fichier .ico (Windows)
TAILLES_ICO = [16, 24, 32, 48, 64, 128, 256]


def rendre_png_bytes(taille: int) -> bytes:
    """Rend le logo dans un buffer PNG (octets)."""
    image = QImage(taille, taille, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    dessiner_logo(painter, taille)
    painter.end()

    octets = QByteArray()
    buffer = QBuffer(octets)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return bytes(octets)


def ecrire_png(taille: int, chemin: str):
    """Écrit un PNG du logo sur le disque."""
    with open(chemin, "wb") as fichier:
        fichier.write(rendre_png_bytes(taille))
    print(f"  [OK] {os.path.relpath(chemin, RACINE)} ({taille}x{taille})")


def ecrire_ico(chemin: str, tailles: list[int]):
    """Assemble un fichier .ico multi-tailles à partir de PNG.

    Le format ICO accepte des images compressées PNG (Vista et versions
    suivantes) : chaque entrée pointe vers un bloc PNG complet.
    """
    pngs = [(taille, rendre_png_bytes(taille)) for taille in tailles]

    en_tete = struct.pack("<HHH", 0, 1, len(pngs))  # réservé, type=icône, nb images
    decalage = 6 + 16 * len(pngs)
    repertoires = bytearray()
    donnees = bytearray()

    for taille, blob in pngs:
        # Une dimension de 256 se note 0 dans le répertoire ICO
        largeur = 0 if taille >= 256 else taille
        hauteur = 0 if taille >= 256 else taille
        repertoires.extend(struct.pack(
            "<BBBBHHII",
            largeur,          # largeur
            hauteur,          # hauteur
            0,                # nombre de couleurs de la palette
            0,                # réservé
            1,                # plans
            32,               # bits par pixel
            len(blob),        # taille des données
            decalage,         # offset des données
        ))
        donnees.extend(blob)
        decalage += len(blob)

    with open(chemin, "wb") as fichier:
        fichier.write(en_tete)
        fichier.write(bytes(repertoires))
        fichier.write(bytes(donnees))

    print(
        f"  [OK] {os.path.relpath(chemin, RACINE)} "
        f"({len(pngs)} tailles : {', '.join(str(t) for t in tailles)})"
    )


def ecrire_svg(chemin: str, taille: int = 512):
    """Exporte le logo en SVG vectoriel (si le module QtSvg est disponible)."""
    try:
        from PySide6.QtSvg import QSvgGenerator
    except ImportError:
        print("  [!] QtSvg indisponible : export SVG ignoré.")
        return

    generateur = QSvgGenerator()
    generateur.setFileName(chemin)
    generateur.setSize(QSize(taille, taille))
    generateur.setViewBox(QRect(0, 0, taille, taille))
    generateur.setTitle("Logo EduPaie")
    generateur.setDescription("Logo vectoriel de l'application EduPaie")

    painter = QPainter(generateur)
    dessiner_logo(painter, taille)
    painter.end()

    print(f"  [OK] {os.path.relpath(chemin, RACINE)} ({taille}x{taille})")


def main():
    """Point d'entrée : génère toutes les ressources de marque."""
    # Une QGuiApplication est nécessaire pour la base de polices (texte « F »)
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)

    os.makedirs(DOSSIER_RESSOURCES, exist_ok=True)

    print("Génération des ressources de marque EduPaie...")

    for taille in TAILLES_PNG:
        nom = "logo.png" if taille == 512 else f"logo_{taille}.png"
        ecrire_png(taille, os.path.join(DOSSIER_RESSOURCES, nom))

    ecrire_ico(os.path.join(DOSSIER_RESSOURCES, "icon.ico"), TAILLES_ICO)

    print("Terminé.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
