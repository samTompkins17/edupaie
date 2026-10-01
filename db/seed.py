"""
Jeu de données de test pour EduPaie.

Recrée la base de données de zéro avec :
- 18 élèves répartis dans 4 classes
- Des paiements variés couvrant les 4 modes de paiement
- Les 3 statuts représentés : Soldé, Partiellement payé, Non payé
- Des numéros de reçu cohérents et uniques

Usage : python -m db.seed (ou python db/seed.py)
"""

import os
import sys

# Ajouter la racine du projet au PYTHONPATH pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_connection
from utils.paths import resource_path


def reinitialiser_base():
    """Supprime et recrée la base de données avec le jeu de test."""

    # --- 1. Lire et exécuter le schéma SQL ---
    chemin_sql = resource_path(os.path.join("db", "schema.sql"))
    with open(chemin_sql, "r", encoding="utf-8") as f:
        script_sql = f.read()

    conn = get_connection()
    try:
        # Supprimer les tables existantes pour repartir de zéro
        conn.execute("DROP TABLE IF EXISTS paiement")
        conn.execute("DROP TABLE IF EXISTS eleve")
        conn.executescript(script_sql)

        # --- 2. Insérer les élèves (18 élèves, 4 classes) ---
        eleves = [
            # (nom, prenom, classe, annee_scolaire, total_du)
            ("DIALLO", "Aminata", "6ème", "2025-2026", 250000),
            ("TRAORE", "Moussa", "6ème", "2025-2026", 250000),
            ("COULIBALY", "Fatou", "6ème", "2025-2026", 250000),
            ("KONE", "Ibrahim", "6ème", "2025-2026", 250000),
            ("SANGARE", "Mariam", "6ème", "2025-2026", 250000),
            ("TOURE", "Abdoulaye", "6ème", "2025-2026", 250000),
            ("KEITA", "Aissatou", "5ème", "2025-2026", 300000),
            ("DIARRA", "Oumar", "5ème", "2025-2026", 300000),
            ("CAMARA", "Kadiatou", "5ème", "2025-2026", 300000),
            ("SIDIBE", "Bakary", "5ème", "2025-2026", 300000),
            ("DEMBELE", "Rokia", "5ème", "2025-2026", 300000),
            ("CISSE", "Seydou", "5ème", "2025-2026", 300000),
            ("HAIDARA", "Fatoumata", "4ème", "2025-2026", 350000),
            ("MAIGA", "Adama", "4ème", "2025-2026", 350000),
            ("SYLLA", "Oumou", "4ème", "2025-2026", 350000),
            ("BA", "Mamadou", "3ème", "2025-2026", 350000),
            ("SISSOKO", "Awa", "3ème", "2025-2026", 350000),
            ("DOUMBIA", "Lamine", "3ème", "2025-2026", 350000),
        ]

        conn.executemany(
            "INSERT INTO eleve (nom, prenom, classe, annee_scolaire, total_du) "
            "VALUES (?, ?, ?, ?, ?)",
            eleves,
        )

        # --- 3. Insérer les paiements ---
        # Compteur pour les numéros de reçu
        compteur_recu = 1

        def numero_recu():
            """Génère le prochain numéro de reçu séquentiel."""
            nonlocal compteur_recu
            num = f"REC-2025-{compteur_recu:04d}"
            compteur_recu += 1
            return num

        paiements = [
            # --- Élèves SOLDÉS (total payé = total dû) ---

            # 1. DIALLO Aminata (250 000) → 3 paiements → soldée
            (1, 100000, "2025-09-15", "especes", numero_recu(), 150000),
            (1, 100000, "2025-11-10", "mobile_money", numero_recu(), 50000),
            (1, 50000, "2026-01-20", "especes", numero_recu(), 0),

            # 2. TRAORE Moussa (250 000) → 2 paiements → soldé
            (2, 150000, "2025-09-20", "cheque", numero_recu(), 100000),
            (2, 100000, "2025-12-05", "virement", numero_recu(), 0),

            # 3. KONE Ibrahim (250 000) → 1 paiement complet → soldé
            (4, 250000, "2025-09-18", "virement", numero_recu(), 0),

            # 4. KEITA Aissatou (300 000) → 3 paiements → soldée
            (7, 100000, "2025-09-25", "especes", numero_recu(), 200000),
            (7, 100000, "2025-12-15", "mobile_money", numero_recu(), 100000),
            (7, 100000, "2026-03-10", "especes", numero_recu(), 0),

            # 5. HAIDARA Fatoumata (350 000) → 2 paiements → soldée
            (13, 200000, "2025-10-01", "cheque", numero_recu(), 150000),
            (13, 150000, "2026-02-14", "virement", numero_recu(), 0),

            # 6. BA Mamadou (350 000) → 4 paiements → soldé
            (16, 100000, "2025-09-22", "especes", numero_recu(), 250000),
            (16, 100000, "2025-11-18", "mobile_money", numero_recu(), 150000),
            (16, 100000, "2026-01-25", "cheque", numero_recu(), 50000),
            (16, 50000, "2026-03-30", "especes", numero_recu(), 0),

            # --- Élèves PARTIELLEMENT PAYÉS ---

            # 7. COULIBALY Fatou (250 000) → 1 paiement de 75 000
            (3, 75000, "2025-10-05", "especes", numero_recu(), 175000),

            # 8. SANGARE Mariam (250 000) → 2 paiements, reste 100 000
            (5, 100000, "2025-09-28", "mobile_money", numero_recu(), 150000),
            (5, 50000, "2025-12-20", "especes", numero_recu(), 100000),

            # 9. DIARRA Oumar (300 000) → 1 paiement de 150 000
            (8, 150000, "2025-10-10", "cheque", numero_recu(), 150000),

            # 10. CAMARA Kadiatou (300 000) → 2 paiements, reste 50 000
            (9, 150000, "2025-09-30", "virement", numero_recu(), 150000),
            (9, 100000, "2026-01-15", "especes", numero_recu(), 50000),

            # 11. DEMBELE Rokia (300 000) → 1 paiement de 200 000
            (11, 200000, "2025-10-12", "mobile_money", numero_recu(), 100000),

            # 12. MAIGA Adama (350 000) → 1 paiement de 175 000
            (14, 175000, "2025-11-05", "cheque", numero_recu(), 175000),

            # 13. SISSOKO Awa (350 000) → 2 paiements, reste 150 000
            (17, 100000, "2025-10-08", "especes", numero_recu(), 250000),
            (17, 100000, "2025-12-22", "virement", numero_recu(), 150000),

            # --- Élèves NON PAYÉS (aucun paiement) ---
            # 14. TOURE Abdoulaye (id=6)  → 0 paiement
            # 15. SIDIBE Bakary (id=10)   → 0 paiement
            # 16. CISSE Seydou (id=12)    → 0 paiement
            # 17. SYLLA Oumou (id=15)     → 0 paiement
            # 18. DOUMBIA Lamine (id=18)  → 0 paiement
        ]

        conn.executemany(
            "INSERT INTO paiement (id_eleve, montant, date_paiement, mode_paiement, "
            "numero_recu, solde_apres) VALUES (?, ?, ?, ?, ?, ?)",
            paiements,
        )

        conn.commit()
        print("[OK] Base de donnees recreee avec succes !")
        print(f"   - {len(eleves)} eleves inseres")
        print(f"   - {len(paiements)} paiements inseres")
        print("   - 6 eleves soldes, 7 partiellement payes, 5 non payes")

    except Exception as e:
        conn.rollback()
        print(f"[ERREUR] Erreur lors du remplissage : {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    reinitialiser_base()
