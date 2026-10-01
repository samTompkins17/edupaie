"""
Initialisation de la base de données EduPaie.

Lit le fichier db/schema.sql et exécute le script DDL pour créer
les tables si elles n'existent pas encore (CREATE TABLE IF NOT EXISTS).

Compatibilité : les premières versions de l'application utilisaient un
schéma différent (table `classe` séparée, clé primaire `id`). Une base
créée par ces versions empêche le code actuel de fonctionner (KeyError
sur `id_eleve`). Elle est détectée au démarrage, sauvegardée, puis
remplacée par une base au schéma actuel.
"""

import os
import shutil
import time

from db.connection import get_connection
from utils.paths import resource_path


def _detecter_schema_obsolete(conn) -> bool:
    """Détecte une base créée par une ancienne version d'EduPaie.

    L'ancien schéma possédait une table `classe` et nommait la clé
    primaire de la table `eleve` simplement `id`. Le schéma actuel
    stocke la classe en texte et utilise `id_eleve`.

    Args:
        conn: connexion SQLite ouverte

    Returns:
        True si la base utilise l'ancien schéma, sinon False
    """
    tables = {
        ligne[0]
        for ligne in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    if "eleve" not in tables:
        return False

    colonnes = {ligne[1] for ligne in conn.execute("PRAGMA table_info(eleve)")}
    return "classe" in tables and "id" in colonnes and "id_eleve" not in colonnes


def _archiver_base_obsolete(chemin_base: str) -> str:
    """Sauvegarde une base obsolète avant de la remplacer.

    Args:
        chemin_base: chemin complet du fichier edupaie.db obsolète

    Returns:
        Le chemin de la copie de sauvegarde créée
    """
    horodatage = time.strftime("%Y%m%d-%H%M%S")
    chemin_sauvegarde = f"{chemin_base}.ancienne-version-{horodatage}"
    shutil.copy2(chemin_base, chemin_sauvegarde)
    return chemin_sauvegarde


def initialiser_base():
    """Prépare la base de données au schéma actuel.

    Cette fonction est idempotente : elle peut être appelée plusieurs
    fois sans risque grâce à IF NOT EXISTS dans le script SQL.

    Si une base d'une ancienne version est détectée (schéma incompatible),
    elle est sauvegardée à côté du fichier original puis remplacée par une
    base neuve : l'application repart avec une base vide mais fonctionnelle
    au lieu de planter au démarrage.
    """
    # Lire le script SQL depuis le fichier schema.sql
    chemin_sql = resource_path(os.path.join("db", "schema.sql"))
    with open(chemin_sql, "r", encoding="utf-8") as fichier:
        script_sql = fichier.read()

    conn = get_connection()
    try:
        schema_obsolete = _detecter_schema_obsolete(conn)
    finally:
        conn.close()

    if schema_obsolete:
        # Base d'une ancienne version : sauvegarder puis recréer à neuf
        import db.connection

        chemin_base = os.path.join(db.connection.get_data_dir(), "edupaie.db")
        _archiver_base_obsolete(chemin_base)
        os.remove(chemin_base)

    conn = get_connection()
    try:
        conn.executescript(script_sql)
        conn.commit()
    finally:
        conn.close()
