📘 Cahier des Charges Fonctionnel
=================================

Application de gestion de campagnes Donjons & Dragons
-----------------------------------------------------

1\. 🎯 Objectif du projet
=========================

Développer une application web permettant aux Maîtres du Jeu (MJ) et aux Joueurs (PJ) de gérer des campagnes de Donjons & Dragons, incluant :

*   Gestion des utilisateurs
    
*   Création et administration de campagnes
    
*   Gestion des personnages (PJ / PNJ)
    
*   Gestion des combats
    
*   Gestion des droits d’accès et visibilité
    
*   Stockage et exploitation des statistiques de combat
    

2\. 👤 Gestion des utilisateurs
===============================

2.1 Rôles
---------

Il existe 3 types d’utilisateurs :

*   Utilisateur non connecté
    
*   Joueur (PJ)
    
*   Maître du Jeu (MJ)
    

Un utilisateur inscrit peut être MJ et/ou joueur selon les actions réalisées.

2.2 Fonctionnalités communes
----------------------------

Un utilisateur inscrit peut :

*   Créer un compte
    
*   Se connecter
    
*   Se déconnecter
    
*   Modifier son profil utilisateur
    

Un utilisateur non connecté peut :

*   Voir la page d’accueil
    
*   Voir les campagnes publiques en cours
    
*   Créer un compte
    
*   Se connecter
    

3\. 🎲 Gestion des campagnes
============================

3.1 Définition d’une campagne
-----------------------------

Une campagne est définie par :

*   Nom
    
*   Description
    
*   MJ propriétaire
    
*   Statut : publique ou privée
    

Si campagne privée :→ Personne ne peut demander à rejoindre→ Seul le MJ peut inviter

3.2 Droits du MJ propriétaire
-----------------------------

Le MJ propriétaire peut :

*   Créer une campagne
    
*   Modifier sa campagne
    
*   Supprimer sa campagne
    
*   Inviter des utilisateurs (MJ ou joueurs)
    
*   Accepter/refuser des demandes d’adhésion
    
*   Modifier les PJ de la campagne
    
*   Ajouter des notes privées sur les PJ
    
*   Gérer l’XP des PJ et PNJ
    
*   Accéder à toutes les informations de la campagne
    
*   Être le seul à voir la page "gestion combat"
    

⚠️ Seul le MJ propriétaire a accès aux informations complètes de la campagne.

3.3 Droits des joueurs
----------------------

Un joueur peut :

*   Demander à rejoindre une campagne publique
    
*   Accepter/refuser une invitation
    
*   Voir les informations partagées des PJ/PNJ
    
*   Participer aux combats via la vue joueur uniquement
    

4\. 📖 Gestion des arcs narratifs
=================================

Un arc narratif :

*   Est rattaché à une campagne
    
*   Est défini par :
    
    *   Nom
        
    *   Description
        

Seul le MJ peut :

*   Créer un arc
    
*   Modifier un arc
    
*   Supprimer un arc
    

5\. 🧙 Gestion des personnages
==============================

5.1 Types
---------

*   PJ (Personnage Joueur)
    
*   PNJ (Personnage Non Joueur)
    

5.2 Structure d’un personnage
-----------------------------

Un PJ ou PNJ est défini par :

*   Nom
    
*   Race
    
*   Classe
    
*   Niveau
    
*   XP
    
*   Caractéristiques :
    
    *   HP
        
    *   CA
        
    *   Initiative
        
    *   Force
        
    *   Dextérité
        
    *   Constitution
        
    *   Intelligence
        
    *   Sagesse
        
    *   Charisme
        
*   Photo de profil
    
*   Fiche personnage
    
*   Historique
    

Spécifique aux PJ :

*   Username du joueur propriétaire
    

5.3 Droits sur les PJ
---------------------

Un joueur peut :

*   Créer un PJ
    
*   Ajouter un PJ à une ou plusieurs campagnes
    
*   Modifier son PJ
    
*   Supprimer son PJ
    

Le MJ propriétaire peut :

*   Modifier les PJ de sa campagne
    
*   Ajouter des notes privées visibles uniquement par lui
    
*   Modifier l’XP
    

5.4 Droits sur les PNJ
----------------------

Seul le MJ peut :

*   Créer un PNJ
    
*   Modifier un PNJ
    
*   Supprimer un PNJ
    
*   Choisir le niveau de partage des informations :
    
    *   Partage complet
        
    *   Partage partiel
        
    *   Aucune information visible
        

6\. ⚔️ Gestion des combats
==========================

6.1 Définition d’un combat
--------------------------

Un combat :

*   Est rattaché à un arc narratif
    
*   Contient des combattants (PJ et/ou PNJ)
    
*   Est structuré par :
    
    *   Durée totale
        
    *   Rounds
        
    *   Tours
        

Seul le MJ peut :

*   Créer un combat
    
*   Modifier un combat
    
*   Supprimer un combat
    
*   Accéder à la vue complète du combat
    

6.2 Gestion des combattants
---------------------------

Chaque combattant peut :

*   Perdre des HP (dégâts)
    
*   Gagner des HP (soins)
    
*   Recevoir des PV temporaires
    
*   Modifier sa CA
    
*   Recevoir ou perdre des états :
    
    *   Aveuglé
        
    *   Charmé
        
    *   Etc.
        
*   Prendre la fuite
    
*   Être supprimé du combat (par le MJ)
    

Le MJ est le seul à :

*   Appliquer les modifications
    
*   Gérer les états
    
*   Gérer les soins/blessures
    
*   Affecter les changements en combat
    

Les joueurs ont accès à une **vue combat player**, limitée aux informations autorisées.

7\. 📊 Logs & Statistiques
==========================

Toutes les actions d’un combat sont :

*   Enregistrées dans des logs
    
*   Stockées en base de données
    

Les données doivent permettre une agrégation par :

*   Combat
    
*   Arc narratif
    
*   Campagne
    

8\. 🔐 Gestion des droits & visibilité
======================================

Le système doit garantir :

*   Séparation stricte des droits MJ / PJ
    
*   Isolation des campagnes
    
*   Gestion fine du partage d’informations PNJ
    
*   Notes MJ invisibles aux joueurs
    
*   Vue combat différenciée MJ / Player