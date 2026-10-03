"""
Générateur de reçus scolaires au format PDF avec ReportLab.

Responsabilités :
- Générer un document PDF professionnel et infalsifiable
- Sauvegarder dans le dossier utilisateur Documents/EduPaie/Recus/
- Garantir la réimpression à l'identique : réouverture du fichier existant
  ou régénération déterministe à partir des données immuables en base
- Ouvrir le PDF avec le visualiseur par défaut du système
"""

import os
import sys

from reportlab.lib.pagesizes import A5, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    Image, SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from utils.paths import get_receipts_dir, resource_path
from services import recu_service
from utils.formatage import (
    formater_montant, formater_date_affichage, libelle_mode_paiement,
)


def chemin_logo() -> str | None:
    """Retourne le chemin du logo embarqué, ou None s'il est absent.

    Le PNG est généré par tools/generate_assets.py et embarqué dans
    l'exécutable via le dossier resources/. En cas d'absence, le reçu
    est généré sans logo (dégradation gracieuse).
    """
    chemin = resource_path(os.path.join("resources", "logo.png"))
    return chemin if os.path.exists(chemin) else None


def generer_recu_pdf(id_paiement: int, forcer_regeneration: bool = False) -> str:
    """Génère le reçu PDF d'un paiement ou retourne le fichier existant.

    Args:
        id_paiement: Identifiant du paiement
        forcer_regeneration: Si True, recrée le fichier même s'il existe déjà

    Returns:
        Chemin absolu vers le fichier PDF généré

    Raises:
        ValueError: Si le paiement ou l'élève n'existe pas
    """
    donnees = recu_service.obtenir_donnees_recu(id_paiement)
    numero_recu = donnees["numero_recu"]

    dossier_recus = get_receipts_dir()
    nom_fichier = f"{numero_recu}.pdf"
    chemin_pdf = os.path.join(dossier_recus, nom_fichier)

    # Réimpression à l'identique : réutiliser le fichier existant si présent
    if os.path.exists(chemin_pdf) and not forcer_regeneration:
        return chemin_pdf

    # Création du document au format A5 Paysage (idéal pour un reçu de caisse)
    doc = SimpleDocTemplate(
        chemin_pdf,
        pagesize=landscape(A5),
        rightMargin=25,
        leftMargin=25,
        topMargin=20,
        bottomMargin=20,
    )

    styles = getSampleStyleSheet()

    # Styles personnalisés
    style_titre_etablissement = ParagraphStyle(
        "TitreEtablissement",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1a237e"),
        alignment=0,
    )
    style_sous_titre = ParagraphStyle(
        "SousTitre",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#555555"),
        alignment=0,
    )
    style_recu_badge = ParagraphStyle(
        "BadgeRecu",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#c62828"),
        alignment=2,
    )
    style_date_emission = ParagraphStyle(
        "DateEmission",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#333333"),
        alignment=2,
    )
    style_cellule_label = ParagraphStyle(
        "CelluleLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#222222"),
    )
    style_cellule_valeur = ParagraphStyle(
        "CelluleValeur",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#111111"),
    )
    style_cellule_montant = ParagraphStyle(
        "CelluleMontant",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#2e7d32"),
    )
    style_cellule_solde = ParagraphStyle(
        "CelluleSolde",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#c62828"),
    )
    style_mention_legale = ParagraphStyle(
        "MentionLegale",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#777777"),
        alignment=1,
    )

    elements = []

    # --- 1. En-tête : Établissement et Numéro de reçu ---
    ligne_entete = [
        [
            Paragraph("<b>COMPLEXE SCOLAIRE EXCELLENCE</b>", style_titre_etablissement),
            Paragraph(f"<b>REÇU N° {numero_recu}</b>", style_recu_badge),
        ],
        [
            Paragraph("Service de Comptabilité & Scolarité — Système EduPaie", style_sous_titre),
            Paragraph(f"Date de règlement : {formater_date_affichage(donnees['date_paiement'])}", style_date_emission),
        ],
    ]
    tableau_entete = Table(ligne_entete, colWidths=[300, 220])
    tableau_entete.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))

    # Logo de l'établissement (si la ressource est disponible)
    logo = chemin_logo()
    if logo:
        bloc_entete = Table(
            [[Image(logo, width=46, height=46), tableau_entete]],
            colWidths=[54, 520],
        )
        bloc_entete.setStyle(TableStyle([
            ("VALIGN", (0, 0), (0, 0), "TOP"),
            ("VALIGN", (1, 0), (1, 0), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(bloc_entete)
    else:
        elements.append(tableau_entete)

    elements.append(Spacer(1, 10))

    # --- 2. Tableau principal des détails ---
    donnees_tableau = [
        [
            Paragraph("Nom & Prénom de l'élève", style_cellule_label),
            Paragraph(f"<b>{donnees['nom']}</b> {donnees['prenom']}", style_cellule_valeur),
            Paragraph("Classe", style_cellule_label),
            Paragraph(donnees["classe"], style_cellule_valeur),
        ],
        [
            Paragraph("Année scolaire", style_cellule_label),
            Paragraph(donnees["annee_scolaire"], style_cellule_valeur),
            Paragraph("Mode de paiement", style_cellule_label),
            Paragraph(libelle_mode_paiement(donnees["mode_paiement"]), style_cellule_valeur),
        ],
        [
            Paragraph("Total annuel des frais", style_cellule_label),
            Paragraph(formater_montant(donnees["total_du"]), style_cellule_valeur),
            Paragraph("Montant versé", style_cellule_label),
            Paragraph(formater_montant(donnees["montant"]), style_cellule_montant),
        ],
        [
            Paragraph("Solde restant dû après versement", style_cellule_label),
            Paragraph(formater_montant(donnees["solde_apres"]), style_cellule_solde),
            Paragraph("Statut", style_cellule_label),
            Paragraph("SOLDÉ" if donnees["solde_apres"] == 0 else "PARTIELLEMENT RÉGLÉ", style_cellule_label),
        ],
    ]

    tableau_corps = Table(
        donnees_tableau,
        colWidths=[150, 150, 110, 130],
    )
    tableau_corps.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fafafa")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        # Ligne de solde mise en valeur
        ("BACKGROUND", (0, 3), (1, 3), colors.HexColor("#fff3e0")),
        ("BACKGROUND", (2, 2), (3, 2), colors.HexColor("#e8f5e9")),
    ]))
    elements.append(tableau_corps)

    elements.append(Spacer(1, 14))

    # --- 3. Signatures ---
    tableau_signatures = Table(
        [
            [
                Paragraph("<b>Signature de l'élève ou tuteur :</b>", style_sous_titre),
                Paragraph("<b>Cachet et Signature de la Caisse :</b>", style_sous_titre),
            ],
            [
                Paragraph("<br/><br/>______________________", style_sous_titre),
                Paragraph("<br/><br/>______________________", style_sous_titre),
            ],
        ],
        colWidths=[270, 270],
    )
    tableau_signatures.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))
    elements.append(tableau_signatures)

    elements.append(Spacer(1, 10))

    # --- 4. Mention légale ---
    elements.append(Paragraph(
        "Ce reçu original atteste de l'encaissement effectif des sommes susmentionnées. "
        "Il doit être soigneusement conservé par les parents ou tuteurs légaux.",
        style_mention_legale,
    ))

    # Générer le fichier
    doc.build(elements)

    return chemin_pdf


def ouvrir_recu_pdf(chemin_pdf: str):
    """Ouvre le fichier PDF dans l'application par défaut du système.

    Args:
        chemin_pdf: Chemin d'accès absolu vers le fichier PDF
    """
    if not os.path.exists(chemin_pdf):
        raise FileNotFoundError(f"Le fichier reçu {chemin_pdf} n'existe pas.")

    if sys.platform.startswith("win"):
        os.startfile(chemin_pdf)
    else:
        import subprocess
        commande = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.run([commande, chemin_pdf], check=False)
