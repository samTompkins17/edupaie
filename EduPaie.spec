# -*- mode: python ; coding: utf-8 -*-
#
# Spec PyInstaller pour EduPaie.
#
# Build :  .venv/Scripts/pyinstaller EduPaie.spec --noconfirm
# Sortie : dist/EduPaie.exe (onefile, sans console, avec icône et version)
#
# Deux éditions, choisies par la variable d'environnement EDUPAIE_DATA :
#   demo   (défaut) : embarque la base de démonstration (18 élèves)
#   clean           : démarre avec une base vide (déploiement école)
import os

edition_donnees = os.environ.get('EDUPAIE_DATA', 'demo')

datas = [
    # Script DDL lu par db/init_db.py
    ('db/schema.sql', 'db'),
    # Marque : logo et icône utilisés par l'UI et les reçus PDF
    ('resources/logo.png', 'resources'),
    ('resources/icon.ico', 'resources'),
]
if edition_donnees == 'demo':
    # Base de test livrée (copiée vers %APPDATA%/EduPaie au 1er lancement)
    datas.insert(0, ('data/edupaie.db', 'data'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='EduPaie',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Identité visuelle de l'exécutable
    icon='resources/icon.ico',
    version='version_info.txt',
)
