"""
Service de gestion des numéros et données de reçus de paiement.

Génère les numéros uniques au format REC-AAAA-NNNN.
Prépare les données consolidées pour l'édition et l'impression des reçus.
"""

import sqlite3
from repositories import paiement_repository, eleve_repository


def generer_numero_recu(annee: str, conn: sqlite3.Connection | None = None) -> str:
    """Génère le prochain numéro de reçu unique pour une année donnée.

    Format standard : REC-AAAA-NNNN (ex: REC-2026-0001)
    Le compteur NNNN est séquentiel et remis à 0001 chaque nouvelle année.

    Cette méthode s'exécute typiquement au sein de la transaction
    d'enregistrement du paiement pour éviter toute concurrence.

    Args:
        annee: Année civile sur 4 chiffres (ex: '2026')
        conn: Connexion SQLite participant à la transaction courante

    Returns:
        Numéro de reçu formaté
    """
    dernier = paiement_repository.dernier_numero_recu(annee, conn=conn)

    if dernier is None:
        prochain_numero = 1
    else:
        # Format attendu : REC-AAAA-NNNN
        try:
            parties = dernier.split("-")
            compteur_actuel = int(parties[2])
            prochain_numero = compteur_actuel + 1
        except (IndexError, ValueError):
            prochain_numero = 1

    return f"REC-{annee}-{prochain_numero:04d}"


def obtenir_donnees_recu(id_paiement: int) -> dict:
    """Récupère l'ensemble des données nécessaires pour éditer le reçu PDF.

    Combine les informations de l'élève et du paiement correspondant.

    Args:
        id_paiement: Identifiant unique du paiement

    Returns:
        Dictionnaire complet pour l'impression du reçu

    Raises:
        ValueError: Si le paiement ou l'élève n'existe pas
    """
    paiement = paiement_repository.obtenir_par_id(id_paiement)
    if not paiement:
        raise ValueError(f"Paiement #{id_paiement} introuvable.")

    eleve = eleve_repository.obtenir_par_id(paiement["id_eleve"])
    if not eleve:
        raise ValueError(f"Élève associé au paiement #{id_paiement} introuvable.")

    return {
        "id_paiement": paiement["id_paiement"],
        "numero_recu": paiement["numero_recu"],
        "date_paiement": paiement["date_paiement"],
        "montant": paiement["montant"],
        "mode_paiement": paiement["mode_paiement"],
        "solde_apres": paiement["solde_apres"],
        "id_eleve": eleve["id_eleve"],
        "nom": eleve["nom"],
        "prenom": eleve["prenom"],
        "classe": eleve["classe"],
        "annee_scolaire": eleve["annee_scolaire"],
        "total_du": eleve["total_du"],
    }
