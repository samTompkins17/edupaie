"""
Repository (accès aux données) pour la table eleve.

Toutes les requêtes SQL concernant les élèves sont centralisées ici.
Aucune logique métier, aucun import PySide6.
Toutes les requêtes utilisent des paramètres (?) pour la sécurité.
"""

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


def obtenir_par_id(id_eleve: int) -> dict | None:
    """Retourne un élève sous forme de dictionnaire, ou None s'il n'existe pas.

    Args:
        id_eleve: Identifiant de l'élève recherché

    Returns:
        Dictionnaire avec les colonnes de l'élève, ou None
    """
    conn = get_connection()
    try:
        curseur = conn.execute(
            "SELECT * FROM eleve WHERE id_eleve = ?", (id_eleve,)
        )
        ligne = curseur.fetchone()
        return dict(ligne) if ligne else None
    finally:
        conn.close()


def rechercher(terme: str = "", classe_filtre: str = "") -> list[dict]:
    """Recherche des élèves par nom/prénom et/ou filtre par classe.

    Args:
        terme: Texte à chercher dans le nom ou le prénom (LIKE %terme%)
        classe_filtre: Si non vide, filtre uniquement cette classe

    Returns:
        Liste de dictionnaires correspondant aux critères
    """
    conn = get_connection()
    try:
        requete = "SELECT * FROM eleve WHERE 1=1"
        parametres = []

        # Filtre par recherche textuelle (nom ou prénom)
        if terme:
            requete += " AND (nom LIKE ? OR prenom LIKE ?)"
            motif = f"%{terme}%"
            parametres.extend([motif, motif])

        # Filtre par classe
        if classe_filtre:
            requete += " AND classe = ?"
            parametres.append(classe_filtre)

        requete += " ORDER BY nom, prenom"

        curseur = conn.execute(requete, parametres)
        return [dict(ligne) for ligne in curseur.fetchall()]
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
