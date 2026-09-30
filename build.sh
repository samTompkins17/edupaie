#!/usr/bin/env bash
# ============================================================
# EduPaie - Script de build (Git Bash / Linux / macOS)
# Produit dist/EduPaie.exe sous Windows (onefile, sans console)
# Usage : ./build.sh
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"

PY=.venv/Scripts/python.exe
if [ ! -x "$PY" ]; then
  PY=python
fi

echo
echo "[1/3] Generation des ressources de marque (logo, icone)..."
"$PY" tools/generate_assets.py

echo
echo "[2/3] Verification : tests metier..."
"$PY" -m unittest discover -s tests -v

echo
echo "[3/3] Construction de l'executable (PyInstaller)..."
"$PY" -m PyInstaller EduPaie.spec --noconfirm --clean

echo
echo "============================================"
echo " Configuration terminée : dist/EduPaie.exe"
echo "============================================"
