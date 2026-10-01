"""
Service métier pour la gestion des paiements scolaires.

Responsabilités :
- Validation stricte des données du paiement (montant > 0, date valide, mode autorisé)
- Application des règles métier : interdiction absolue de paiement supérieur au solde
- Enregistrement transactionnel unique : calcul du solde restant, attribution du numéro
  de reçu et insertion en base de données au sein d'une même transaction ACID.
"""

from datetime import datetime
import sqlite3

from db.connection import get_connection
from repositories import eleve_repository, paiement_repository
from services import recu_service


MODES_PAIEMENT_AUTORISES = ("especes", "cheque", "virement", "mobile_money")


def valider_donnees_paiement(id_eleve: int, montant: int, date_paiement: str, mode_paiement: str):
    """Valide les critères formels d'une saisie de paiement.

    Raises:
        ValueError: Si un paramètre est invalide ou manquant
    """
    if not id_eleve or not isinstance(id_eleve, int):
        raise ValueError("L'élève rattaché au paiement est obligatoire.")

    if not isinstance(montant, int) or montant <= 0:
        raise ValueError("Le montant du paiement doit être un entier strictement positif.")

    if not date_paiement or not date_paiement.strip():
        raise ValueError("La date de paiement est obligatoire.")

    # Validation du format date (YYYY-MM-DD)
    try:
        datetime.strptime(date_paiement.strip(), "%Y-%m-%d")
    except ValueError:
        raise ValueError("La date de paiement doit respecter le format AAAA-MM-JJ (ex: 2026-03-30).")

    if not mode_paiement or mode_paiement not in MODES_PAIEMENT_AUTORISES:
        modes_str = ", ".join(MODES_PAIEMENT_AUTORISES)
        raise ValueError(f"Mode de paiement invalide ('{mode_paiement}'). Modes autorisés : {modes_str}.")


def enregistrer_paiement(id_eleve: int, montant: int, date_paiement: str, mode_paiement: str) -> dict:
    """Enregistre un paiement de scolarité dans une transaction atomique.

    Vérifie le solde actuel de l'élève. Si le montant dépasse le solde restant,
    l'enregistrement est immédiatement refusé avec une exception explicite.

    Enregistre le paiement et réserve le numéro de reçu dans la même transaction.

    Args:
        id_eleve: Identifiant de l'élève
        montant: Montant versé en FCFA (> 0)
        date_paiement: Date au format YYYY-MM-DD
        mode_paiement: Mode ('especes', 'cheque', 'virement', 'mobile_money')

    Returns:
        Dictionnaire récapitulatif du paiement créé avec son numéro de reçu

    Raises:
        ValueError: En cas de données invalides ou de dépassement de solde
    """
    # 1. Validations formelles
    valider_donnees_paiement(id_eleve, montant, date_paiement, mode_paiement)
    date_paiement = date_paiement.strip()

    # 2. Transaction SQLite unique
    conn = get_connection()
    try:
        with conn:
            # Vérifier l'existence de l'élève
            curseur = conn.execute(
                "SELECT id_eleve, total_du FROM eleve WHERE id_eleve = ?",
                (id_eleve,),
            )
            ligne_eleve = curseur.fetchone()
            if not ligne_eleve:
                raise ValueError(f"L'élève #{id_eleve} est introuvable.")

            total_du = ligne_eleve["total_du"]

            # Calculer la somme déjà payée sous verrou de transaction
            curseur = conn.execute(
                "SELECT COALESCE(SUM(montant), 0) AS total_paye FROM paiement WHERE id_eleve = ?",
                (id_eleve,),
            )
            total_paye = curseur.fetchone()["total_paye"]
            solde_restant = total_du - total_paye

            # RÈGLE MÉTIER CRITIQUE : Dépassement de solde interdit
            if montant > solde_restant:
                from ui.utils import formater_montant
                raise ValueError(
                    f"Paiement refusé : le montant saisi ({formater_montant(montant)}) "
                    f"dépasse le solde restant dû ({formater_montant(solde_restant)}).\n"
                    f"Le solde d'un élève ne peut jamais être négatif."
                )

            # Calcul du solde après paiement
            solde_apres = solde_restant - montant

            # Génération du numéro de reçu pour l'année du paiement
            annee = date_paiement[:4]
            numero_recu = recu_service.generer_numero_recu(annee, conn=conn)

            # Insertion du paiement
            id_paiement = paiement_repository.inserer(
                id_eleve=id_eleve,
                montant=montant,
                date_paiement=date_paiement,
                mode_paiement=mode_paiement,
                numero_recu=numero_recu,
                solde_apres=solde_apres,
                conn=conn,
            )

        # Fin du bloc with conn : commit automatique si aucune exception levée
        return {
            "id_paiement": id_paiement,
            "id_eleve": id_eleve,
            "montant": montant,
            "date_paiement": date_paiement,
            "mode_paiement": mode_paiement,
            "numero_recu": numero_recu,
            "solde_apres": solde_apres,
        }

    except sqlite3.IntegrityError as e:
        raise ValueError(f"Erreur d'intégrité de la base de données : {e}")
    finally:
        conn.close()
