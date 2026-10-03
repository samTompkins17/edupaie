"""
Service métier pour la gestion des élèves.

Responsabilités :
- Validation des données avant insertion/modification
- Calcul du solde restant et du statut de paiement
- Vérification des règles métier (ex: suppression interdite si paiements)
- Agrégation des statistiques pour le tableau de bord

Aucun SQL ici : tout passe par les repositories.
Aucun import PySide6.
"""

from repositories import eleve_repository
from repositories import paiement_repository


# --- Constantes des statuts ---
STATUT_SOLDE = "Soldé"
STATUT_PARTIEL = "Partiellement payé"
STATUT_NON_PAYE = "Non payé"

# --- Classes autorisées (liste fermée) ---
CLASSES_AUTORISEES = ["6ème", "5ème", "4ème", "3ème"]


def valider_donnees(nom: str, prenom: str, classe: str,
                    annee_scolaire: str, total_du: int):
    """Vérifie que les données d'un élève sont valides.

    Lève une ValueError avec un message explicite si une donnée est invalide.
    """
    if not nom or not nom.strip():
        raise ValueError("Le nom est obligatoire.")
    if not prenom or not prenom.strip():
        raise ValueError("Le prénom est obligatoire.")
    if not classe or not classe.strip():
        raise ValueError("La classe est obligatoire.")
    if classe.strip() not in CLASSES_AUTORISEES:
        raise ValueError(
            "Classe invalide. Classes autorisées : "
            + ", ".join(CLASSES_AUTORISEES) + "."
        )
    if not annee_scolaire or not annee_scolaire.strip():
        raise ValueError("L'année scolaire est obligatoire.")
    if not isinstance(total_du, int) or total_du < 0:
        raise ValueError("Le montant total dû doit être un entier positif ou nul.")


def ajouter_eleve(nom: str, prenom: str, classe: str,
                  annee_scolaire: str, total_du: int) -> int:
    """Valide et ajoute un nouvel élève.

    Args:
        nom, prenom, classe, annee_scolaire, total_du: Données de l'élève

    Returns:
        L'identifiant du nouvel élève

    Raises:
        ValueError: Si les données sont invalides
    """
    valider_donnees(nom, prenom, classe, annee_scolaire, total_du)
    return eleve_repository.inserer(
        nom.strip().upper(), prenom.strip(), classe.strip(),
        annee_scolaire.strip(), total_du,
    )


def modifier_eleve(id_eleve: int, nom: str, prenom: str, classe: str,
                   annee_scolaire: str, total_du: int):
    """Valide et modifie un élève existant.

    Vérifie aussi que le nouveau total_du n'est pas inférieur
    à la somme déjà payée (ce qui créerait un solde négatif).

    Raises:
        ValueError: Si les données sont invalides ou incohérentes
    """
    valider_donnees(nom, prenom, classe, annee_scolaire, total_du)

    # Vérifier que le nouveau total_du ne crée pas de solde négatif
    somme_payee = paiement_repository.somme_paiements(id_eleve)
    if total_du < somme_payee:
        raise ValueError(
            f"Le montant total dû ({total_du}) ne peut pas être inférieur "
            f"à la somme déjà payée ({somme_payee})."
        )

    eleve_repository.modifier(
        id_eleve, nom.strip().upper(), prenom.strip(), classe.strip(),
        annee_scolaire.strip(), total_du,
    )


def supprimer_eleve(id_eleve: int):
    """Supprime un élève après vérification.

    Refuse la suppression si l'élève a des paiements enregistrés.

    Raises:
        ValueError: Si l'élève a des paiements
    """
    nombre_paiements = paiement_repository.compter_par_eleve(id_eleve)
    if nombre_paiements > 0:
        raise ValueError(
            f"Impossible de supprimer cet élève : il a {nombre_paiements} "
            "paiement(s) enregistré(s). Un élève ayant des paiements ne peut pas "
            "être supprimé afin de conserver l'historique des reçus."
        )
    eleve_repository.supprimer(id_eleve)


def calculer_solde(id_eleve: int) -> int:
    """Calcule le solde restant dû pour un élève.

    solde = total_du - somme des paiements

    Returns:
        Le solde en FCFA (toujours >= 0 grâce aux validations)
    """
    eleve = eleve_repository.obtenir_par_id(id_eleve)
    if eleve is None:
        raise ValueError("Élève introuvable.")
    somme = paiement_repository.somme_paiements(id_eleve)
    return eleve["total_du"] - somme


def _determiner_statut(solde: int, nombre_paiements: int) -> str:
    if solde == 0:
        return STATUT_SOLDE
    if nombre_paiements > 0:
        return STATUT_PARTIEL
    return STATUT_NON_PAYE


def _enrichir_eleve(eleve: dict, somme_payee: int, nombre_paiements: int) -> dict:
    eleve["somme_payee"] = somme_payee
    eleve["solde"] = eleve["total_du"] - somme_payee
    eleve["statut"] = _determiner_statut(eleve["solde"], nombre_paiements)
    return eleve


def obtenir_eleve(id_eleve: int) -> dict:
    """Retourne un élève enrichi avec son solde et son statut.

    Returns:
        Dictionnaire avec toutes les colonnes + 'solde' + 'statut'

    Raises:
        ValueError: Si l'élève n'existe pas
    """
    eleve = eleve_repository.obtenir_par_id(id_eleve)
    if eleve is None:
        raise ValueError("Élève introuvable.")

    somme = paiement_repository.somme_paiements(id_eleve)
    nb_paiements = paiement_repository.compter_par_eleve(id_eleve)

    return _enrichir_eleve(eleve, somme, nb_paiements)


def lister_eleves(terme: str = "", classe_filtre: str = "") -> list[dict]:
    """Retourne la liste des élèves enrichie du solde et du statut.

    Args:
        terme: Texte de recherche (nom ou prénom)
        classe_filtre: Filtre par classe (vide = toutes)

    Returns:
        Liste de dictionnaires enrichis
    """
    eleves = eleve_repository.rechercher(terme, classe_filtre)
    for eleve in eleves:
        somme = paiement_repository.somme_paiements(eleve["id_eleve"])
        nb = paiement_repository.compter_par_eleve(eleve["id_eleve"])
        _enrichir_eleve(eleve, somme, nb)
    return eleves


def lister_classes() -> list[str]:
    """Retourne la liste des classes distinctes."""
    return eleve_repository.lister_classes()


def obtenir_statistiques() -> dict:
    """Calcule les indicateurs clés pour le tableau de bord (F6).

    Returns:
        Dictionnaire avec :
        - nombre_eleves: nombre total d'élèves
        - total_encaisse: somme de tous les paiements effectués
        - total_restant_du: somme de tous les soldes restants
        - nombre_non_soldes: nombre d'élèves dont le solde > 0
        - nombre_soldes: nombre d'élèves dont le solde = 0
        - nombre_partiellement_payes: nombre d'élèves partiellement réglés
        - nombre_non_payes: nombre d'élèves n'ayant encore rien versé
        - taux_recouvrement: pourcentage encaissé par rapport au total dû global
    """
    tous = lister_eleves()
    total_encaisse = paiement_repository.total_encaisse()
    total_restant = sum(e["solde"] for e in tous)
    total_global_du = total_encaisse + total_restant

    nb_soldes = sum(1 for e in tous if e["statut"] == STATUT_SOLDE)
    nb_partiels = sum(1 for e in tous if e["statut"] == STATUT_PARTIEL)
    nb_non_payes = sum(1 for e in tous if e["statut"] == STATUT_NON_PAYE)
    non_soldes = nb_partiels + nb_non_payes

    taux = (total_encaisse / total_global_du * 100) if total_global_du > 0 else 0.0

    return {
        "nombre_eleves": len(tous),
        "total_encaisse": total_encaisse,
        "total_restant_du": total_restant,
        "nombre_non_soldes": non_soldes,
        "nombre_soldes": nb_soldes,
        "nombre_partiellement_payes": nb_partiels,
        "nombre_non_payes": nb_non_payes,
        "taux_recouvrement": round(taux, 1),
    }
