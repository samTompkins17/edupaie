"""
Module de connexion à la base de données SQLite.

Fournit une fonction unique get_connection() qui :
- ouvre une connexion vers la base edupaie.db
- active les clés étrangères (PRAGMA foreign_keys = ON)
- configure row_factory pour accéder aux colonnes par nom
"""

import sqlite3
import os

from utils.paths import get_data_dir


def get_connection() -> sqlite3.Connection:
    """Ouvre et retourne une connexion SQLite vers edupaie.db.

    La connexion a les propriétés suivantes :
    - PRAGMA foreign_keys activé (intégrité référentielle)
    - row_factory = sqlite3.Row (accès par nom de colonne)

    L'appelant est responsable de fermer la connexion après usage.
    Utiliser de préférence un context manager (with).
    """
    chemin_base = os.path.join(get_data_dir(), "edupaie.db")
    conn = sqlite3.connect(chemin_base)

    # Activer les clés étrangères (désactivées par défaut dans SQLite)
    conn.execute("PRAGMA foreign_keys = ON")

    # Permettre l'accès aux colonnes par nom (row['nom']) en plus de l'index
    conn.row_factory = sqlite3.Row

    return conn
