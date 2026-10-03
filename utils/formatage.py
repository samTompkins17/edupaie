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
