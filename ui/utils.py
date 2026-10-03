"""
Helpers d'affichage pour l'interface EduPaie.

Fonctions de formatage (montants, dates, statuts) et constantes
de couleurs utilisées dans toute l'interface. La palette provient du
design system (`ui.theme`) afin de garantir une cohérence globale.
"""

from ui.theme import COULEUR_STATUT, PALETTE
from utils.formatage import (
    annee_debut_scolaire,
    formater_montant,
    formater_date_affichage,
    libelle_mode_paiement,
)

__all__ = [
    "PALETTE",
    "annee_debut_scolaire", "formater_montant", "formater_date_affichage",
    "couleur_statut", "libelle_mode_paiement", "initiales",
]


def couleur_statut(statut: str) -> str:
    """Retourne la couleur associée à un statut de paiement."""
    return COULEUR_STATUT.get(statut, PALETTE["textMuted"])


def initiales(nom: str, prenom: str = "") -> str:
    """Retourne les initiales d'un élève (ex: 'DIALLO Aminata' → 'DA')."""
    partie_nom = (nom or "").strip()[:1].upper()
    partie_prenom = (prenom or "").strip()[:1].upper()
    return f"{partie_nom}{partie_prenom}" or "?"
