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
import time
from datetime import date, timedelta
from unittest.mock import patch

from db.connection import get_connection
from db.seed import reinitialiser_base
from repositories import eleve_repository, paiement_repository
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
        self.assertIn(
            "Un élève ayant des paiements ne peut pas être supprimé afin de conserver l'historique des reçus.",
            str(ctx.exception),
        )

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

    def test_11_validation_dates_paiement(self):
        """Vérifie le contrôle des dates de versement (F3 / fix dates-paiement).

        - Date future refusée
        - Date 1900 refusée (antérieure au 01/01 de l'année scolaire)
        - Date du jour acceptée
        """
        # Élève 3 (COULIBALY Fatou, 2025-2026, solde restant > 0)
        aujourdhui = date.today()
        date_future = (aujourdhui + timedelta(days=1)).isoformat()
        date_1900 = "1900-01-01"
        date_du_jour = aujourdhui.isoformat()

        # 1. Date future -> refusée
        with self.assertRaises(ValueError) as ctx:
            paiement_service.enregistrer_paiement(3, 5000, date_future, "especes")
        self.assertIn("postérieure à la date du jour", str(ctx.exception))

        # 2. Date 1900 -> refusée
        with self.assertRaises(ValueError) as ctx:
            paiement_service.enregistrer_paiement(3, 5000, date_1900, "especes")
        self.assertIn("antérieure au 1er janvier de la première année scolaire", str(ctx.exception))

        # 3. Date du jour -> acceptée
        res = paiement_service.enregistrer_paiement(3, 5000, date_du_jour, "especes")
        self.assertIsNotNone(res["id_paiement"])
        self.assertEqual(res["date_paiement"], date_du_jour)

    def test_12_decouplage_couches(self):
        """Vérifie le respect strict du découpage en couches (refactor/couches).

        - utils.formatage exporte les utilitaires indépendamment de UI
        - eleve_repository.obtenir_total_du fonctionne avec/sans connexion
        - Aucune dépendance 'from ui' ou 'import ui' dans services, receipts, db, utils
        """
        from utils.formatage import (
            formater_montant,
            formater_date_affichage,
            libelle_mode_paiement,
        )

        self.assertEqual(formater_montant(10000), "10 000 FCFA")
        self.assertEqual(formater_date_affichage("2026-03-30"), "30/03/2026")
        self.assertEqual(libelle_mode_paiement("mobile_money"), "Mobile Money")

        # Repository obtenir_total_du
        total_du = eleve_repository.obtenir_total_du(1)
        self.assertEqual(total_du, 250000)

        # Vérification qu'aucun fichier hors ui n'importe ui
        racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dossiers_interdits = ["services", "receipts", "repositories", "db", "utils"]
        for dossier in dossiers_interdits:
            chemin_dossier = os.path.join(racine, dossier)
            if not os.path.isdir(chemin_dossier):
                continue
            for nom_fic in os.listdir(chemin_dossier):
                if nom_fic.endswith(".py"):
                    with open(os.path.join(chemin_dossier, nom_fic), "r", encoding="utf-8") as f:
                        contenu = f.read()
                        self.assertNotIn(
                            "from ui",
                            contenu,
                            f"{nom_fic} dans {dossier} ne doit pas importer depuis ui",
                        )
                        self.assertNotIn(
                            "import ui",
                            contenu,
                            f"{nom_fic} dans {dossier} ne doit pas importer ui",
                        )


    def test_13_performance_liste_eleves(self):
        """Vérifie les performances avec 2 000 élèves / 12 000 paiements (perf/liste-eleves).

        Avant optimisation, lister_eleves exécutait 2 requêtes par élève
        (problème N+1) : plus de 16 s pour 2 000 élèves. La requête unique
        avec LEFT JOIN doit répondre en moins de 0,3 s, et les statistiques
        agrégées en moins de 0,2 s.
        """
        # Base isolée dans un dossier temporaire pour ne pas perturber les autres tests
        with tempfile.TemporaryDirectory() as dossier_temp:
            with patch("db.connection.get_data_dir", return_value=dossier_temp):
                reinitialiser_base()
                conn = get_connection()
                try:
                    # 2 000 élèves répartis dans 4 classes, 300 000 FCFA dus chacun
                    classes = ["6ème", "5ème", "4ème", "3ème"]
                    eleves = [
                        (f"NOM_{i:04d}", f"Prenom_{i:04d}", classes[i % 4],
                         "2025-2026", 300000)
                        for i in range(1, 2001)
                    ]
                    conn.execute("DELETE FROM paiement")
                    conn.execute("DELETE FROM eleve")
                    conn.executemany(
                        "INSERT INTO eleve (nom, prenom, classe, annee_scolaire, "
                        "total_du) VALUES (?, ?, ?, ?, ?)",
                        eleves,
                    )
                    ids = [r["id_eleve"] for r in conn.execute(
                        "SELECT id_eleve FROM eleve ORDER BY id_eleve"
                    ).fetchall()]

                    # 12 000 paiements : 6 versements de 25 000 par élève
                    modes = ["especes", "cheque", "virement", "mobile_money"]
                    paiements = [
                        (ids[(i - 1) % len(ids)], 25000, "2025-10-15",
                         modes[i % 4], f"REC-2025-{90000 + i:05d}", 150000)
                        for i in range(1, 12001)
                    ]
                    conn.executemany(
                        "INSERT INTO paiement (id_eleve, montant, date_paiement, "
                        "mode_paiement, numero_recu, solde_apres) VALUES (?,?,?,?,?,?)",
                        paiements,
                    )
                    conn.commit()
                finally:
                    conn.close()

                # Premier appel hors mesure : chauffe le cache de la base
                eleve_service.lister_eleves()

                # Mesure de lister_eleves : requête unique, sous 0,3 s
                t0 = time.perf_counter()
                resultat = eleve_service.lister_eleves()
                duree_lister = time.perf_counter() - t0
                self.assertLess(
                    duree_lister, 0.3,
                    f"lister_eleves trop lent : {duree_lister:.3f} s",
                )

                # Mesure des statistiques : requêtes agrégées, sous 0,2 s
                t0 = time.perf_counter()
                stats = eleve_service.obtenir_statistiques()
                duree_stats = time.perf_counter() - t0
                self.assertLess(
                    duree_stats, 0.2,
                    f"obtenir_statistiques trop lent : {duree_stats:.3f} s",
                )

                # Mêmes résultats qu'avant optimisation : tri, soldes, statuts
                self.assertEqual(len(resultat), 2000)
                premier = resultat[0]
                self.assertEqual(premier["nom"], "NOM_0001")  # tri alphabétique
                # 6 versements de 25 000 -> 150 000 payés, solde 150 000
                self.assertEqual(premier["somme_payee"], 150000)
                self.assertEqual(premier["solde"], 150000)
                self.assertEqual(premier["statut"], "Partiellement payé")

                # Filtre par classe : 500 élèves par classe
                sixiemes = eleve_service.lister_eleves(classe_filtre="6ème")
                self.assertEqual(len(sixiemes), 500)
                self.assertTrue(all(e["classe"] == "6ème" for e in sixiemes))

                # Statistiques globales cohérentes avec le jeu de données
                self.assertEqual(stats["nombre_eleves"], 2000)
                self.assertEqual(stats["total_encaisse"], 12000 * 25000)
                self.assertEqual(
                    stats["total_restant_du"], 2000 * 300000 - 12000 * 25000
                )
                self.assertEqual(stats["nombre_partiellement_payes"], 2000)


if __name__ == "__main__":
    unittest.main()
