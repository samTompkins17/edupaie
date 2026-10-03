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

    # Rejeter d'abord les booléens : en Python, True/False sont des int,
    # ils passeraient donc à travers le contrôle isinstance(total_du, int).
    if isinstance(total_du, bool):
        raise ValueError("Le montant total dû doit être un entier strictement positif.")

    # total_du doit être strictement supérieur à 0 (fix/validation-eleve)
    if not isinstance(total_du, int) or total_du <= 0:
        raise ValueError("Le montant total dû doit être un entier strictement positif.")


def _refuser_si_doublon(nom: str, prenom: str, classe: str,
                        annee_scolaire: str,
                        id_exclu: int | None = None, action: str = "ajouter"):
    """Refuse l'ajout ou la modification si l'élève existe déjà (doublon).

    La comparaison est faite par le repository sans tenir compte de la
    casse ni des espaces en trop. Pour une modification, l'élève lui-même
    est ignoré (id_exclu) : il a le droit de garder son identité.

    Raises:
        ValueError: Si un autre élève avec les mêmes clés existe déjà
    """
    if eleve_repository.existe_doublon(nom, prenom, classe, annee_scolaire, id_exclu):
        if action == "modifier":
            raise ValueError(
                f"Impossible de modifier cet élève : un autre élève « {nom} {prenom} » "
                f"existe déjà en {classe} pour l'année scolaire {annee_scolaire}. "
                "Les doublons sont refusés."
            )
        raise ValueError(
            f"Impossible d'ajouter cet élève : un élève « {nom} {prenom} » "
            f"existe déjà en {classe} pour l'année scolaire {annee_scolaire}. "
            "Les doublons sont refusés."
        )


def ajouter_eleve(nom: str, prenom: str, classe: str,
                  annee_scolaire: str, total_du: int) -> int:
    """Valide et ajoute un nouvel élève.

    Args:
        nom, prenom, classe, annee_scolaire, total_du: Données de l'élève

    Returns:
        L'identifiant du nouvel élève

    Raises:
        ValueError: Si les données sont invalides ou en cas de doublon
    """
    valider_donnees(nom, prenom, classe, annee_scolaire, total_du)

    # Normalisation identique à celle utilisée pour l'insertion
    nom_propre = nom.strip().upper()
    prenom_propre = prenom.strip()
    classe_propre = classe.strip()
    annee_propre = annee_scolaire.strip()

    # Refus d'un doublon (même élève déjà inscrit, casse/espaces ignorés)
    _refuser_si_doublon(nom_propre, prenom_propre, classe_propre, annee_propre,
                        action="ajouter")

    return eleve_repository.inserer(
        nom_propre, prenom_propre, classe_propre, annee_propre, total_du,
    )


def modifier_eleve(id_eleve: int, nom: str, prenom: str, classe: str,
                   annee_scolaire: str, total_du: int):
    """Valide et modifie un élève existant.

    Vérifie aussi que le nouveau total_du n'est pas inférieur
    à la somme déjà payée (ce qui créerait un solde négatif).

    Raises:
        ValueError: Si les données sont invalides, incohérentes ou en cas de doublon
    """
    valider_donnees(nom, prenom, classe, annee_scolaire, total_du)

    # Normalisation identique à celle utilisée pour l'enregistrement
    nom_propre = nom.strip().upper()
    prenom_propre = prenom.strip()
    classe_propre = classe.strip()
    annee_propre = annee_scolaire.strip()

    # Refus d'un doublon : l'élève modifié ne doit pas entrer en collision
    # avec un autre élève (lui-même est ignoré dans la comparaison)
    _refuser_si_doublon(nom_propre, prenom_propre, classe_propre, annee_propre,
                        id_exclu=id_eleve, action="modifier")

    # Vérifier que le nouveau total_du ne crée pas de solde négatif
    somme_payee = paiement_repository.somme_paiements(id_eleve)
    if total_du < somme_payee:
        raise ValueError(
            f"Le montant total dû ({total_du}) ne peut pas être inférieur "
            f"à la somme déjà payée ({somme_payee})."
        )

    eleve_repository.modifier(
        id_eleve, nom_propre, prenom_propre, classe_propre,
        annee_propre, total_du,
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

    Les cumuls de paiements sont calculés directement par la requête SQL
    du repository (évite les N requêtes par élève).

    Args:
        terme: Texte de recherche (nom ou prénom)
        classe_filtre: Filtre par classe (vide = toutes)

    Returns:
        Liste de dictionnaires enrichis
    """
    eleves = eleve_repository.rechercher(terme, classe_filtre)
    for eleve in eleves:
        eleve["solde"] = eleve["total_du"] - eleve["somme_payee"]
        eleve["statut"] = _determiner_statut(eleve["solde"], eleve["nb_paiements"])
    return eleves


def lister_classes() -> list[str]:
    """Retourne la liste des classes distinctes."""
    return eleve_repository.lister_classes()


def obtenir_statistiques() -> dict:
    """Calcule les indicateurs clés pour le tableau de bord (F6).

    Délègue à une requête agrégée SQL unique pour des performances instantanées.

    Returns:
        Dictionnaire avec les indicateurs obligatoires du tableau de bord
    """
    return eleve_repository.obtenir_statistiques_globales()
