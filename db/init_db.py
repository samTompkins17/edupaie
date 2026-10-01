"""
Initialisation de la base de données EduPaie.

Lit le fichier db/schema.sql et exécute le script DDL pour créer
les tables si elles n'existent pas encore (CREATE TABLE IF NOT EXISTS).
"""

import os

from db.connection import get_connection
from utils.paths import resource_path


def initialiser_base():
    """Crée les tables de la base de données à partir de schema.sql.

    Cette fonction est idempotente : elle peut être appelée plusieurs
    fois sans risque grâce à IF NOT EXISTS dans le script SQL.
    """
    # Lire le script SQL depuis le fichier schema.sql
    chemin_sql = resource_path(os.path.join("db", "schema.sql"))
    with open(chemin_sql, "r", encoding="utf-8") as fichier:
        script_sql = fichier.read()

    # Exécuter le script DDL
    conn = get_connection()
    try:
        conn.executescript(script_sql)
        conn.commit()
    finally:
        conn.close()
