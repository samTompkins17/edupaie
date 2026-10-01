# EduPaie — Guide Utilisateur Simplifié

> **Application de gestion des paiements et frais de scolarité**  
> *Guide pratique d'une page à destination du secrétariat scolaire.*

---

## 1. Démarrer l'application

1. Double-cliquez sur l'exécutable `EduPaie.exe` (ou lancez `python main.py`).
2. La fenêtre principale s'ouvre directement sur le **Tableau de bord financier**.
3. La barre latérale à gauche permet de basculer à tout moment entre :
   - 📊 **Tableau de bord** (vue globale, statistiques, relances)
   - 👨‍🎓 **Élèves** (répertoire complet, inscriptions, encaissements)

---

## 2. Enregistrer un nouvel élève

1. Dans la barre latérale, cliquez sur **👨‍🎓 Élèves**.
2. Cliquez sur le bouton bleu **Ajouter un élève** en bas à droite.
3. Renseignez les informations de l'élève :
   - **Nom** (ex : *DIALLO*) et **Prénom** (ex : *Aminata*)
   - **Classe** (sélectionnez dans la liste déroulante ou tapez une nouvelle classe)
   - **Année scolaire** (ex : *2025-2026*)
   - **Total des frais de scolarité dus** en FCFA (ex : *250 000*)
4. Cliquez sur **Enregistrer** : un message confirme l'ajout et l'élève apparaît immédiatement avec le statut rouge **Non payé**.

---

## 3. Enregistrer un versement (paiement)

Deux méthodes simples sont disponibles :

### Méthode A : Depuis la liste des élèves
1. Sélectionnez la ligne de l'élève dans le tableau.
2. Cliquez sur le bouton vert **💳 Enregistrer paiement**.

### Méthode B : Depuis la fiche détaillée de l'élève
1. Double-cliquez sur l'élève ou cliquez sur **👤 Voir la fiche**.
2. Cliquez sur le bouton vert **+ Enregistrer un paiement**.

### Dans le formulaire de versement :
1. Vérifiez le **Solde actuel restant** rappelé en haut.
2. Indiquez le **Montant versé** (le système interdit automatiquement tout montant supérieur au solde dû).
3. Sélectionnez la **Date du versement** et le **Mode de règlement** (*Espèces*, *Mobile Money*, *Chèque*, *Virement*).
4. Laissez cochée la case *Générer et ouvrir le reçu PDF immédiatement*.
5. Cliquez sur **Confirmer le paiement** :
   - Le paiement est validé de façon sécurisée.
   - Un **numéro de reçu unique** (ex : `REC-2026-0001`) est généré.
   - Le reçu PDF s'ouvre instantanément à l'écran.

---

## 4. Consulter et réimprimer un reçu existant

1. Rendez-vous sur la **Fiche de l'élève** concerné.
2. Dans le tableau **Historique des versements**, chaque paiement passé est listé par ordre chronologique.
3. Deux actions au choix :
   - Cliquez sur **🔍 Détails** pour inspecter les informations complètes du versement.
   - Cliquez sur **📄 Reçu** pour réimprimer ou réouvrir le document PDF officiel **à l'identique de l'original**.
4. Les reçus PDF générés sont également toujours archivés dans votre dossier personnel :  
   `Documents \ EduPaie \ Recus \`

---

## 5. Suivre les impayés depuis le Tableau de bord

1. Cliquez sur **📊 Tableau de bord** dans la barre latérale.
2. Consultez d'un coup d'œil les 4 cartes maîtresses :
   - **Total des élèves inscrits**
   - **Total encaissé (FCFA)** et taux de recouvrement global
   - **Total restant dû (FCFA)** à recouvrer
   - **Nombre d'élèves non soldés**
3. Utilisez le filtre **"Élèves non soldés uniquement"** au-dessus du tableau pour lister instantanément tous les élèves redevables et préparer les relances des familles.
