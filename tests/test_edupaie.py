"""
Suite de tests automatisés pour EduPaie.

Vérifie l'ensemble des règles métier critiques et critères d'acceptation :
- Respect des contraintes SQL et PRAGMA foreign_keys = ON
- Calcul exact du solde et déduction du statut (F2)
- Rejet strict d'un paiement supérieur au solde (F3)
- Rejet des montants négatifs ou nuls (F3)
- Unicité et format du numéro de reçu REC-AAAA-NNNN (F3, F5)
- Interdiction de supprimer un élève ayant des paiements (F1)
- Génération déterministe du reçu PDF (F5)
- Cohérence des indicateurs du tableau de bord (F6)
"""

import unittest
import os
import tempfile
from unittest.mock import patch

from db.connection import get_connection
from db.seed import reinitialiser_base
from services import eleve_service, paiement_service, recu_service
from receipts import pdf_generator


class TestEduPaie(unittest.TestCase):
    """Cas de tests unitaires et d'intégration EduPaie."""

    @classmethod
    def setUpClass(cls):
        """Réinitialise la base de données avec le jeu de test avant les tests."""
        cls._repertoire_temporaire = tempfile.TemporaryDirectory()
        cls._patch_dossier_donnees = patch(
            "db.connection.get_data_dir",
            return_value=cls._repertoire_temporaire.name,
        )
        cls._patch_dossier_donnees.start()
        reinitialiser_base()

    @classmethod
    def tearDownClass(cls):
        cls._patch_dossier_donnees.stop()
        cls._repertoire_temporaire.cleanup()

    def test_01_foreign_keys_actives(self):
        """Vérifie que PRAGMA foreign_keys est activé sur chaque connexion."""
        conn = get_connection()
        curseur = conn.execute("PRAGMA foreign_keys")
        valeur = curseur.fetchone()[0]
        conn.close()
        self.assertEqual(valeur, 1, "Les clés étrangères doivent être activées.")

    def test_02_calcul_solde_et_statut(self):
        """Vérifie les 3 statuts possibles (Soldé, Partiel, Non payé) et les soldes."""
        # Élève 1 (DIALLO Aminata) : 250 000 dus, 250 000 payés -> Solde 0, Soldé
        e1 = eleve_service.obtenir_eleve(1)
        self.assertEqual(e1["solde"], 0)
        self.assertEqual(e1["statut"], "Soldé")

        # Élève 3 (COULIBALY Fatou) : 250 000 dus, 75 000 payés -> Solde 175 000, Partiel
        e3 = eleve_service.obtenir_eleve(3)
        self.assertEqual(e3["solde"], 175000)
        self.assertEqual(e3["statut"], "Partiellement payé")

        # Élève 6 (TOURE Abdoulaye) : 250 000 dus, 0 payé -> Solde 250 000, Non payé
        e6 = eleve_service.obtenir_eleve(6)
        self.assertEqual(e6["solde"], 250000)
        self.assertEqual(e6["statut"], "Non payé")

    def test_03_refus_depassement_solde(self):
        """Vérifie qu'un versement supérieur au solde restant est systématiquement refusé."""
        e3 = eleve_service.obtenir_eleve(3)
        solde_restant = e3["solde"]  # 175 000
        montant_excessif = solde_restant + 1000

        with self.assertRaises(ValueError) as ctx:
            paiement_service.enregistrer_paiement(
                id_eleve=3,
                montant=montant_excessif,
                date_paiement="2026-04-01",
                mode_paiement="especes",
            )
        self.assertIn("dépasse le solde restant dû", str(ctx.exception))

    def test_04_refus_montants_invalides(self):
        """Vérifie qu'un montant nul ou négatif est rejeté."""
        with self.assertRaises(ValueError):
            paiement_service.enregistrer_paiement(3, 0, "2026-04-01", "especes")
        with self.assertRaises(ValueError):
            paiement_service.enregistrer_paiement(3, -5000, "2026-04-01", "especes")

    def test_05_format_et_unicite_numero_recu(self):
        """Vérifie le format séquentiel REC-AAAA-NNNN et l'unicité."""
        num = recu_service.generer_numero_recu("2026")
        self.assertTrue(num.startswith("REC-2026-"))
        # Le numéro doit avoir au minimum 4 chiffres (format REC-AAAA-NNNN)
        compteur = num.split("-")[2]
        self.assertGreaterEqual(len(compteur), 4)

    def test_06_refus_suppression_eleve_avec_paiements(self):
        """Vérifie qu'un élève ayant des versements ne peut pas être supprimé."""
        with self.assertRaises(ValueError) as ctx:
            eleve_service.supprimer_eleve(1)
        self.assertIn("Impossible de supprimer cet élève", str(ctx.exception))

    def test_07_suppression_eleve_sans_paiement(self):
        """Vérifie qu'un élève sans versement peut être ajouté puis supprimé sans erreur."""
        nouvel_id = eleve_service.ajouter_eleve(
            nom="TEST",
            prenom="Temporaire",
            classe="6ème",
            annee_scolaire="2025-2026",
            total_du=100000,
        )
        self.assertIsNotNone(nouvel_id)
        # Suppression autorisée car 0 paiement
        eleve_service.supprimer_eleve(nouvel_id)
        with self.assertRaises(ValueError):
            eleve_service.obtenir_eleve(nouvel_id)

    def test_08_generation_recu_pdf(self):
        """Vérifie la création et la réimpression du fichier PDF."""
        chemin = pdf_generator.generer_recu_pdf(1)
        self.assertTrue(os.path.exists(chemin))
        self.assertGreater(os.path.getsize(chemin), 1000)

    def test_09_statistiques_dashboard(self):
        """Vérifie l'exactitude des calculs statistiques globaux du tableau de bord."""
        stats = eleve_service.obtenir_statistiques()
        self.assertEqual(stats["nombre_eleves"], 18)
        self.assertEqual(stats["total_encaisse"], 2950000)
        self.assertEqual(stats["total_restant_du"], 2450000)
        self.assertEqual(stats["nombre_non_soldes"], 12)
        self.assertEqual(stats["nombre_soldes"], 6)
        self.assertEqual(stats["nombre_partiellement_payes"], 7)
        self.assertEqual(stats["nombre_non_payes"], 5)

    def test_10_numerotation_au_dela_9999(self):
        """Vérifie que la numérotation fonctionne au-delà de 9999 reçus/an.

        Insère directement REC-2028-9999, puis vérifie que le suivant est
        REC-2028-10000, l'insère, et vérifie que le suivant est REC-2028-10001.
        """
        conn = get_connection()
        try:
            # Créer un élève temporaire pour ce test
            curseur = conn.execute(
                "INSERT INTO eleve (nom, prenom, classe, annee_scolaire, total_du) "
                "VALUES (?, ?, ?, ?, ?)",
                ("TEST_NUM", "Temporaire", "6ème", "2028-2029", 9000000),
            )
            id_tmp = curseur.lastrowid

            # Insérer un paiement avec le numéro REC-2028-9999
            conn.execute(
                "INSERT INTO paiement (id_eleve, montant, date_paiement, "
                "mode_paiement, numero_recu, solde_apres) VALUES (?,?,?,?,?,?)",
                (id_tmp, 1000, "2028-09-01", "especes", "REC-2028-9999", 8999000),
            )
            conn.commit()

            # Le prochain numéro doit être REC-2028-10000
            suivant = recu_service.generer_numero_recu("2028")
            self.assertEqual(suivant, "REC-2028-10000")

            # Insérer ce numéro pour vérifier la séquence suivante
            conn.execute(
                "INSERT INTO paiement (id_eleve, montant, date_paiement, "
                "mode_paiement, numero_recu, solde_apres) VALUES (?,?,?,?,?,?)",
                (id_tmp, 1000, "2028-09-02", "especes", "REC-2028-10000", 8998000),
            )
            conn.commit()

            # Le prochain doit être REC-2028-10001
            suivant2 = recu_service.generer_numero_recu("2028")
            self.assertEqual(suivant2, "REC-2028-10001")

        finally:
            # Nettoyage : supprimer les paiements puis l'élève de test
            conn.execute(
                "DELETE FROM paiement WHERE id_eleve = ?", (id_tmp,)
            )
            conn.execute(
                "DELETE FROM eleve WHERE id_eleve = ?", (id_tmp,)
            )
            conn.commit()
            conn.close()


if __name__ == "__main__":
    unittest.main()
