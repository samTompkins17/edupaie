"""
Helpers d'affichage pour l'interface EduPaie.

Fonctions de formatage (montants, dates, statuts) et constantes
de couleurs utilisées dans toute l'interface. La palette provient du
design system (`ui.theme`) afin de garantir une cohérence globale.
"""

from ui.theme import COULEUR_STATUT, FOND_STATUT, PALETTE

# --- Couleurs des statuts de paiement ---
COULEUR_SOLDE = COULEUR_STATUT["Soldé"]        # Vert → Soldé
COULEUR_PARTIEL = COULEUR_STATUT["Partiellement payé"]  # Orange → Partiel
COULEUR_NON_PAYE = COULEUR_STATUT["Non payé"]  # Rouge → Non payé

# --- Couleurs de la marque (raccourcis pratiques) ---
COULEUR_PRIMAIRE = PALETTE["primary"]
COULEUR_PRIMAIRE_FONCE = PALETTE["primaryDark"]
COULEUR_TEXTE = PALETTE["text"]
COULEUR_TEXTE_MUET = PALETTE["textMuted"]
COULEUR_SURFACE = PALETTE["surface"]
COULEUR_FOND = PALETTE["bg"]
COULEUR_BORDURE = PALETTE["border"]

__all__ = [
    "COULEUR_SOLDE", "COULEUR_PARTIEL", "COULEUR_NON_PAYE",
    "COULEUR_PRIMAIRE", "COULEUR_PRIMAIRE_FONCE", "COULEUR_TEXTE",
    "COULEUR_TEXTE_MUET", "COULEUR_SURFACE", "COULEUR_FOND",
    "COULEUR_BORDURE", "FOND_STATUT", "PALETTE",
    "formater_montant", "formater_date_affichage", "couleur_statut",
    "libelle_mode_paiement", "initiales",
]


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


def couleur_statut(statut: str) -> str:
    """Retourne la couleur associée à un statut de paiement."""
    return COULEUR_STATUT.get(statut, PALETTE["textMuted"])


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


def initiales(nom: str, prenom: str = "") -> str:
    """Retourne les initiales d'un élève (ex: 'DIALLO Aminata' → 'DA')."""
    partie_nom = (nom or "").strip()[:1].upper()
    partie_prenom = (prenom or "").strip()[:1].upper()
    return f"{partie_nom}{partie_prenom}" or "?"
