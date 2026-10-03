"""
Repository (accès aux données) pour la table eleve.

Toutes les requêtes SQL concernant les élèves sont centralisées ici.
Aucune logique métier, aucun import PySide6.
Toutes les requêtes utilisent des paramètres (?) pour la sécurité.
"""

import sqlite3
from db.connection import get_connection


def inserer(nom: str, prenom: str, classe: str, annee_scolaire: str,
            total_du: int) -> int:
    """Insère un nouvel élève et retourne son id.

    Args:
        nom: Nom de famille de l'élève
        prenom: Prénom de l'élève
        classe: Classe (ex: '6ème A')
        annee_scolaire: Année scolaire (ex: '2025-2026')
        total_du: Montant total des frais de scolarité en FCFA

    Returns:
        L'identifiant (id_eleve) du nouvel élève
    """
    conn = get_connection()
    try:
        curseur = conn.execute(
            "INSERT INTO eleve (nom, prenom, classe, annee_scolaire, total_du) "
            "VALUES (?, ?, ?, ?, ?)",
            (nom, prenom, classe, annee_scolaire, total_du),
        )
        conn.commit()
        return curseur.lastrowid
    finally:
        conn.close()


def modifier(id_eleve: int, nom: str, prenom: str, classe: str,
             annee_scolaire: str, total_du: int):
    """Met à jour les informations d'un élève existant.

    Args:
        id_eleve: Identifiant de l'élève à modifier
        nom, prenom, classe, annee_scolaire, total_du: Nouvelles valeurs
    """
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE eleve SET nom = ?, prenom = ?, classe = ?, "
            "annee_scolaire = ?, total_du = ? WHERE id_eleve = ?",
            (nom, prenom, classe, annee_scolaire, total_du, id_eleve),
        )
        conn.commit()
    finally:
        conn.close()


def supprimer(id_eleve: int):
    """Supprime un élève par son identifiant.

    Lève une exception sqlite3.IntegrityError si l'élève a des paiements
    (grâce à ON DELETE RESTRICT sur la clé étrangère).

    Args:
        id_eleve: Identifiant de l'élève à supprimer
    """
    conn = get_connection()
    try:
        conn.execute("DELETE FROM eleve WHERE id_eleve = ?", (id_eleve,))
        conn.commit()
    finally:
        conn.close()


def obtenir_par_id(id_eleve: int,
                   conn: sqlite3.Connection | None = None) -> dict | None:
    """Retourne un élève sous forme de dictionnaire, ou None s'il n'existe pas.

    Args:
        id_eleve: Identifiant de l'élève recherché
        conn: Connexion existante optionnelle (transaction)

    Returns:
        Dictionnaire avec les colonnes de l'élève, ou None
    """
    fermer = False
    if conn is None:
        conn = get_connection()
        fermer = True
    try:
        curseur = conn.execute(
            "SELECT * FROM eleve WHERE id_eleve = ?", (id_eleve,)
        )
        ligne = curseur.fetchone()
        return dict(ligne) if ligne else None
    finally:
        if fermer:
            conn.close()


def obtenir_par_id_avec_conn(id_eleve: int, conn) -> dict | None:
    """Alias pour obtenir_par_id avec connexion existante."""
    return obtenir_par_id(id_eleve, conn=conn)


def obtenir_total_du(id_eleve: int,
                     conn: sqlite3.Connection | None = None) -> int:
    """Retourne le montant total dû pour un élève.

    Args:
        id_eleve: Identifiant de l'élève
        conn: Connexion existante optionnelle (transaction)

    Returns:
        Total dû en FCFA

    Raises:
        ValueError: Si l'élève n'existe pas
    """
    fermer = False
    if conn is None:
        conn = get_connection()
        fermer = True
    try:
        curseur = conn.execute(
            "SELECT total_du FROM eleve WHERE id_eleve = ?", (id_eleve,)
        )
        ligne = curseur.fetchone()
        if not ligne:
            raise ValueError(f"L'élève #{id_eleve} est introuvable.")
        return ligne["total_du"]
    finally:
        if fermer:
            conn.close()


def existe_doublon(nom: str, prenom: str, classe: str,
                   annee_scolaire: str, id_exclu: int | None = None) -> bool:
    """Vérifie si un élève identique existe déjà (fix/validation-eleve).

    Deux élèves sont considérés identiques si (nom, prénom, classe,
    année scolaire) correspondent, sans tenir compte de la casse
    ni des espaces en trop.

    Args:
        nom, prenom, classe, annee_scolaire: Valeurs saisies à contrôler
        id_exclu: Id de l'élève à ignorer dans la comparaison
                  (cas d'une modification : l'élève lui-même ne compte pas
                  comme un doublon), ou None pour un ajout

    Returns:
        True si un autre élève avec les mêmes clés existe déjà
    """
    conn = get_connection()
    try:
        # LOWER(TRIM(...)) : comparaison insensible à la casse et aux espaces
        requete = (
            "SELECT COUNT(*) FROM eleve "
            "WHERE LOWER(TRIM(nom)) = LOWER(TRIM(?)) "
            "AND LOWER(TRIM(prenom)) = LOWER(TRIM(?)) "
            "AND LOWER(TRIM(classe)) = LOWER(TRIM(?)) "
            "AND LOWER(TRIM(annee_scolaire)) = LOWER(TRIM(?))"
        )
        parametres = [nom, prenom, classe, annee_scolaire]

        # Pour une modification, ignorer l'élève lui-même
        if id_exclu is not None:
            requete += " AND id_eleve != ?"
            parametres.append(id_exclu)

        curseur = conn.execute(requete, parametres)
        return curseur.fetchone()[0] > 0
    finally:
        conn.close()


def rechercher(terme: str = "", classe_filtre: str = "") -> list[dict]:
    """Recherche des élèves avec calcul direct du cumul des paiements.

    Requête unique avec LEFT JOIN pour éviter les N+1 requêtes (optimisation F1/F6).

    Args:
        terme: Texte à chercher dans le nom ou le prénom
        classe_filtre: Si non vide, filtre uniquement cette classe

    Returns:
        Liste de dictionnaires avec les colonnes élève + somme_payee + nb_paiements
    """
    conn = get_connection()
    try:
        requete = (
            "SELECT e.id_eleve, e.nom, e.prenom, e.classe, e.annee_scolaire, e.total_du, "
            "COALESCE(SUM(p.montant), 0) AS somme_payee, "
            "COUNT(p.id_paiement) AS nb_paiements "
            "FROM eleve e "
            "LEFT JOIN paiement p ON p.id_eleve = e.id_eleve "
            "WHERE 1=1"
        )
        parametres = []

        # Filtre par recherche textuelle (nom ou prénom)
        if terme:
            requete += " AND (e.nom LIKE ? OR e.prenom LIKE ?)"
            motif = f"%{terme}%"
            parametres.extend([motif, motif])

        # Filtre par classe
        if classe_filtre:
            requete += " AND e.classe = ?"
            parametres.append(classe_filtre)

        requete += " GROUP BY e.id_eleve ORDER BY e.nom, e.prenom"

        curseur = conn.execute(requete, parametres)
        return [dict(ligne) for ligne in curseur.fetchall()]
    finally:
        conn.close()


def obtenir_statistiques_globales() -> dict:
    """Calcule les indicateurs financiers et démographiques globaux en requête agrégée unique.

    Returns:
        Dictionnaire des agrégats pour le tableau de bord
    """
    conn = get_connection()
    try:
        requete = """
            SELECT 
                COUNT(e.id_eleve) AS nombre_eleves,
                COALESCE(SUM(e.total_du), 0) AS total_du_global,
                COALESCE(SUM(sp.somme_payee), 0) AS total_encaisse,
                COALESCE(SUM(CASE WHEN e.total_du = COALESCE(sp.somme_payee, 0) THEN 1 ELSE 0 END), 0) AS nombre_soldes,
                COALESCE(SUM(CASE WHEN COALESCE(sp.somme_payee, 0) > 0 AND COALESCE(sp.somme_payee, 0) < e.total_du THEN 1 ELSE 0 END), 0) AS nombre_partiellement_payes,
                COALESCE(SUM(CASE WHEN COALESCE(sp.nb_paiements, 0) = 0 THEN 1 ELSE 0 END), 0) AS nombre_non_payes
            FROM eleve e
            LEFT JOIN (
                SELECT id_eleve, SUM(montant) AS somme_payee, COUNT(id_paiement) AS nb_paiements
                FROM paiement
                GROUP BY id_eleve
            ) sp ON sp.id_eleve = e.id_eleve
        """
        curseur = conn.execute(requete)
        ligne = curseur.fetchone()

        nombre_eleves = ligne["nombre_eleves"] or 0
        total_du_global = ligne["total_du_global"] or 0
        total_encaisse = ligne["total_encaisse"] or 0
        total_restant_du = total_du_global - total_encaisse
        nombre_soldes = ligne["nombre_soldes"] or 0
        nombre_partiellement_payes = ligne["nombre_partiellement_payes"] or 0
        nombre_non_payes = ligne["nombre_non_payes"] or 0
        nombre_non_soldes = nombre_partiellement_payes + nombre_non_payes
        taux_recouvrement = round((total_encaisse / total_du_global * 100), 1) if total_du_global > 0 else 0.0

        return {
            "nombre_eleves": nombre_eleves,
            "total_encaisse": total_encaisse,
            "total_restant_du": total_restant_du,
            "nombre_non_soldes": nombre_non_soldes,
            "nombre_soldes": nombre_soldes,
            "nombre_partiellement_payes": nombre_partiellement_payes,
            "nombre_non_payes": nombre_non_payes,
            "taux_recouvrement": taux_recouvrement,
        }
    finally:
        conn.close()


def lister_classes() -> list[str]:
    """Retourne la liste distincte des classes, triées par ordre alphabétique.

    Returns:
        Liste de chaînes (noms de classes uniques)
    """
    conn = get_connection()
    try:
        curseur = conn.execute(
            "SELECT DISTINCT classe FROM eleve ORDER BY classe"
        )
        return [ligne["classe"] for ligne in curseur.fetchall()]
    finally:
        conn.close()
