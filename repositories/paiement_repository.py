"""
Repository (accès aux données) pour la table paiement.

Toutes les requêtes SQL concernant les paiements sont centralisées ici.
Certaines méthodes acceptent une connexion existante pour participer
à une transaction ouverte par la couche service.
"""

import sqlite3
from db.connection import get_connection


def inserer(id_eleve: int, montant: int, date_paiement: str,
            mode_paiement: str, numero_recu: str, solde_apres: int,
            conn: sqlite3.Connection | None = None) -> int:
    """Insère un nouveau paiement et retourne son id.

    Args:
        id_eleve: Identifiant de l'élève concerné
        montant: Montant payé en FCFA (> 0)
        date_paiement: Date au format YYYY-MM-DD
        mode_paiement: Mode parmi 'especes', 'cheque', 'virement', 'mobile_money'
        numero_recu: Numéro de reçu unique (ex: 'REC-2026-0001')
        solde_apres: Solde restant après ce paiement
        conn: Connexion existante (pour transaction). Si None, ouvre une nouvelle.

    Returns:
        L'identifiant (id_paiement) du nouveau paiement
    """
    fermer = False
    if conn is None:
        conn = get_connection()
        fermer = True

    try:
        curseur = conn.execute(
            "INSERT INTO paiement (id_eleve, montant, date_paiement, "
            "mode_paiement, numero_recu, solde_apres) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (id_eleve, montant, date_paiement, mode_paiement,
             numero_recu, solde_apres),
        )
        if fermer:
            conn.commit()
        return curseur.lastrowid
    finally:
        if fermer:
            conn.close()


def lister_par_eleve(id_eleve: int) -> list[dict]:
    """Retourne tous les paiements d'un élève, du plus récent au plus ancien.

    Args:
        id_eleve: Identifiant de l'élève

    Returns:
        Liste de dictionnaires (un par paiement)
    """
    conn = get_connection()
    try:
        curseur = conn.execute(
            "SELECT * FROM paiement WHERE id_eleve = ? "
            "ORDER BY date_paiement DESC, id_paiement DESC",
            (id_eleve,),
        )
        return [dict(ligne) for ligne in curseur.fetchall()]
    finally:
        conn.close()


def obtenir_par_id(id_paiement: int) -> dict | None:
    """Retourne un paiement par son identifiant, ou None.

    Args:
        id_paiement: Identifiant du paiement recherché

    Returns:
        Dictionnaire avec les colonnes du paiement, ou None
    """
    conn = get_connection()
    try:
        curseur = conn.execute(
            "SELECT * FROM paiement WHERE id_paiement = ?", (id_paiement,)
        )
        ligne = curseur.fetchone()
        return dict(ligne) if ligne else None
    finally:
        conn.close()


def somme_paiements(id_eleve: int,
                    conn: sqlite3.Connection | None = None) -> int:
    """Retourne la somme totale des paiements d'un élève.

    Args:
        id_eleve: Identifiant de l'élève
        conn: Connexion existante optionnelle (transaction)

    Returns:
        Somme en FCFA (0 si aucun paiement)
    """
    fermer = False
    if conn is None:
        conn = get_connection()
        fermer = True
    try:
        curseur = conn.execute(
            "SELECT COALESCE(SUM(montant), 0) AS total "
            "FROM paiement WHERE id_eleve = ?",
            (id_eleve,),
        )
        return curseur.fetchone()["total"]
    finally:
        if fermer:
            conn.close()


def compter_par_eleve(id_eleve: int) -> int:
    """Retourne le nombre de paiements enregistrés pour un élève.

    Args:
        id_eleve: Identifiant de l'élève

    Returns:
        Nombre de paiements (entier)
    """
    conn = get_connection()
    try:
        curseur = conn.execute(
            "SELECT COUNT(*) AS total FROM paiement WHERE id_eleve = ?",
            (id_eleve,),
        )
        return curseur.fetchone()["total"]
    finally:
        conn.close()


def dernier_numero_recu(annee: str,
                        conn: sqlite3.Connection | None = None) -> str | None:
    """Retourne le dernier numéro de reçu de l'année, ou None.

    Utilisé pour générer le prochain numéro séquentiel.

    Args:
        annee: Année calendaire (ex: '2026')
        conn: Connexion existante (pour transaction)

    Returns:
        Le dernier numéro (ex: 'REC-2026-0015'), ou None si aucun reçu cette année
    """
    fermer = False
    if conn is None:
        conn = get_connection()
        fermer = True

    try:
        # Tri numérique sur le compteur (après le préfixe "REC-AAAA-" = 9 car.)
        # pour éviter que REC-2028-9999 passe devant REC-2028-10000
        curseur = conn.execute(
            "SELECT numero_recu AS dernier FROM paiement "
            "WHERE numero_recu LIKE ? "
            "ORDER BY CAST(substr(numero_recu, 10) AS INTEGER) DESC "
            "LIMIT 1",
            (f"REC-{annee}-%",),
        )
        resultat = curseur.fetchone()
        return resultat["dernier"] if resultat else None
    finally:
        if fermer:
            conn.close()
