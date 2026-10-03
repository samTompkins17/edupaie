"""
Fonctions utilitaires de formatage des données (montants, dates, libellés).

Indépendantes de toute bibliothèque graphique (PySide6) pour pouvoir
être utilisées aussi bien par les services métier, les générateurs de documents
que par la couche d'interface utilisateur.
"""


def formater_montant(montant: int) -> str:
    """Formate un montant entier en FCFA avec séparateur de milliers.

    Exemple : 250000 → '250 000 FCFA'
    """
    # Utiliser l'espace comme séparateur de milliers
    texte = f"{montant:,}".replace(",", " ")
    return f"{texte} FCFA"


def formater_date_affichage(date_iso: str) -> str:
    """Convertit une date ISO (YYYY-MM-DD) en format d'affichage (JJ/MM/AAAA).

    Exemple : '2025-09-15' → '15/09/2025'
    """
    if not date_iso or len(date_iso) != 10:
        return date_iso or ""
    parties = date_iso.split("-")
    if len(parties) != 3:
        return date_iso
    return f"{parties[2]}/{parties[1]}/{parties[0]}"


def annee_debut_scolaire(annee_scolaire: str) -> int:
    """Première année d'une année scolaire au format AAAA-AAAA.

    Exemple : '2025-2026' → 2025 ; '2025' → 2025.

    Centralise un parsing utilisé à la fois par la validation métier et
    par l'interface (bornage du sélecteur de date) : une seule définition,
    un seul message d'erreur explicite.

    Args:
        annee_scolaire: Texte saisi pour l'année scolaire

    Returns:
        L'année de début (entier entre 1 et 9999, bornes de `datetime.date`)

    Raises:
        ValueError: Si le texte ne contient pas d'année exploitable
    """
    texte = (annee_scolaire or "").strip()
    premiere_partie = texte.split("-")[0].strip()
    try:
        annee = int(premiere_partie)
    except ValueError:
        annee = 0  # force le refus ci-dessous

    if not 1 <= annee <= 9999:
        raise ValueError(
            f"L'année scolaire « {texte} » est invalide "
            "(format attendu : 2025-2026)."
        )
    return annee


def libelle_mode_paiement(mode: str) -> str:
    """Convertit le code du mode de paiement en libellé lisible.

    Exemple : 'mobile_money' → 'Mobile Money'
    """
    correspondances = {
        "especes": "Espèces",
        "cheque": "Chèque",
        "virement": "Virement",
        "mobile_money": "Mobile Money",
    }
    return correspondances.get(mode, mode)
