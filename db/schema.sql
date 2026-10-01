-- =============================================================
-- EduPaie - Script de création de la base de données
-- Généré depuis docs/mld.mmd
-- =============================================================

-- Table des élèves
-- Stocke les informations de chaque élève et le montant total
-- des frais de scolarité qu'il doit payer.
CREATE TABLE IF NOT EXISTS eleve (
    id_eleve        INTEGER PRIMARY KEY AUTOINCREMENT,
    nom             TEXT    NOT NULL,
    prenom          TEXT    NOT NULL,
    classe          TEXT    NOT NULL,
    annee_scolaire  TEXT    NOT NULL,
    total_du        INTEGER NOT NULL CHECK (total_du >= 0)
);

-- Table des paiements
-- Chaque paiement est rattaché à un élève (clé étrangère).
-- Le numéro de reçu est unique pour garantir l'intégrité.
-- ON DELETE RESTRICT empêche la suppression d'un élève ayant des paiements.
CREATE TABLE IF NOT EXISTS paiement (
    id_paiement     INTEGER PRIMARY KEY AUTOINCREMENT,
    id_eleve        INTEGER NOT NULL,
    montant         INTEGER NOT NULL CHECK (montant > 0),
    date_paiement   TEXT    NOT NULL,
    mode_paiement   TEXT    NOT NULL CHECK (mode_paiement IN ('especes', 'cheque', 'virement', 'mobile_money')),
    numero_recu     TEXT    NOT NULL UNIQUE,
    solde_apres     INTEGER NOT NULL CHECK (solde_apres >= 0),
    FOREIGN KEY (id_eleve) REFERENCES eleve (id_eleve) ON DELETE RESTRICT
);
