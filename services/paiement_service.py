"""
Service métier pour la gestion des paiements scolaires.

Responsabilités :
- Validation stricte des données du paiement (montant > 0, date valide, mode autorisé)
- Application des règles métier : interdiction absolue de paiement supérieur au solde
- Enregistrement transactionnel unique : calcul du solde restant, attribution du numéro
  de reçu et insertion en base de données au sein d'une même transaction ACID.
"""

from datetime import date, datetime
import sqlite3

from db.connection import get_connection
from repositories import eleve_repository, paiement_repository
from services import recu_service


MODES_PAIEMENT_AUTORISES = ("especes", "cheque", "virement", "mobile_money")


def valider_donnees_paiement(id_eleve: int, montant: int, date_paiement: str, mode_paiement: str):
    """Valide les critères formels et temporels d'une saisie de paiement.

    Raises:
        ValueError: Si un paramètre est invalide, date future ou antérieure à l'année scolaire
    """
    if not id_eleve or not isinstance(id_eleve, int):
        raise ValueError("L'élève rattaché au paiement est obligatoire.")

    if not isinstance(montant, int) or montant <= 0:
        raise ValueError("Le montant du paiement doit être un entier strictement positif.")

    if not date_paiement or not date_paiement.strip():
        raise ValueError("La date de paiement est obligatoire.")

    # Validation du format date (YYYY-MM-DD)
    try:
        date_obj = datetime.strptime(date_paiement.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("La date de paiement doit respecter le format AAAA-MM-JJ (ex: 2026-03-30).")

    # Règle : date postérieure à aujourd'hui interdite
    aujourdhui = date.today()
    if date_obj > aujourdhui:
        raise ValueError(
            f"La date de paiement ne peut pas être postérieure à la date du jour ({aujourdhui.strftime('%d/%m/%Y')})."
        )

    # Règle : date antérieure au 1er janvier de la première année de l'année scolaire de l'élève interdite
    eleve = eleve_repository.obtenir_par_id(id_eleve)
    if not eleve:
        raise ValueError(f"L'élève #{id_eleve} est introuvable.")

    annee_scolaire = eleve.get("annee_scolaire", "")
    try:
        annee_debut = int(annee_scolaire.split("-")[0].strip())
    except (ValueError, IndexError):
        annee_debut = int(str(annee_scolaire)[:4])

    date_min = date(annee_debut, 1, 1)
    if date_obj < date_min:
        raise ValueError(
            f"La date de paiement ne peut pas être antérieure au 1er janvier de la première "
            f"année scolaire de l'élève ({date_min.strftime('%d/%m/%Y')})."
        )

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

    # 2. Transaction SQLite avec retry en cas de conflit de numéro de reçu
    #    (deux fenêtres enregistrent un paiement au même instant)
    MAX_TENTATIVES = 3
    for tentative in range(1, MAX_TENTATIVES + 1):
        conn = get_connection()
        try:
            with conn:
                # Récupérer le total dû et la somme déjà payée via les repositories
                total_du = eleve_repository.obtenir_total_du(id_eleve, conn=conn)
                total_paye = paiement_repository.somme_paiements(id_eleve, conn=conn)
                solde_restant = total_du - total_paye

                # RÈGLE MÉTIER CRITIQUE : Dépassement de solde interdit
                if montant > solde_restant:
                    raise ValueError(
                        f"Paiement refusé : le montant saisi ({montant} FCFA) "
                        f"dépasse le solde restant dû ({solde_restant} FCFA).\n"
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

            # Fin du bloc with conn : commit automatique
            return {
                "id_paiement": id_paiement,
                "id_eleve": id_eleve,
                "montant": montant,
                "date_paiement": date_paiement,
                "mode_paiement": mode_paiement,
                "numero_recu": numero_recu,
                "solde_apres": solde_apres,
            }

        except sqlite3.IntegrityError:
            # Conflit de numéro de reçu (doublon) → réessayer
            if tentative >= MAX_TENTATIVES:
                raise ValueError(
                    "Impossible d'attribuer un numéro de reçu unique après "
                    f"{MAX_TENTATIVES} tentatives. Veuillez réessayer."
                )
            # Sinon on boucle pour régénérer un nouveau numéro
        finally:
            conn.close()
