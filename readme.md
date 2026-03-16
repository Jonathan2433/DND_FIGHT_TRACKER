# D&D Combat Tracker - README

## 📦 Installation

### Prérequis
- Python 3.10+
- pip (gestionnaire de paquets Python)

### Installation

1. **Créer un dossier pour l'application**
```bash
mkdir dnd_combat_tracker
cd dnd_combat_tracker

python -m venv venv
source venv/bin/activate  # Pour Linux/Mac
venv\Scripts\activate     # Pour Windows

pip install flask flask_sqlalchemy

python app.py
```

L'application sera accessible à : http://127.0.0.1:5000

---

## 🎮 Fonctionnalités

### Gestion des Combats
- Création et gestion de plusieurs combats
- Suivi du temps (combat/round/tour)
- Vue Maître du jeu et Vue joueurs séparée
- Résumé détaillé post-combat

### Gestion des Combattants
- Ajout manuel de combattants
- Templates de monstres prédéfinis
- Templates de PJ personnalisables
- Gestion des groupes
- Suivi des :
  - Points de vie (PV)
  - PV temporaires
  - Classe d'armure (CA)
  - États et conditions
  - Fuite

### Interface Combat
- Ordre d'initiative automatique
- Barre latérale d'initiative
- Mise en évidence du tour actif
- Chronomètre intégré
- Auto-scroll sur le combattant actif

---

## 💡 Comment Utiliser

### Démarrer un Combat
- Cliquer sur "Nouveau combat"
- Nommer votre combat
- Ajouter vos combattants :
  - Manuellement
  - Via templates
  - Via encounters prédéfinis

### Pendant le Combat
- Cliquer "Lancer le combat"
- Utiliser "Tour suivant" pour la progression
- Gérer :
  - Points de vie (dégâts/soins)
  - États (conditions)
  - CA et PV temporaires
  - Fuites éventuelles

### Fin de Combat
- Cliquer "Clôturer le combat"
- Consulter le résumé détaillé
- Accéder à l'historique complet

### Vue Joueurs
- Accessible via bouton dédié
- Rafraîchissement automatique
- Affichage adapté aux joueurs (sans PV des ennemis)

---

## 📁 Structure du Projet

```
dnd_tracker/
├── app.py              # Application principale
├── requirements.txt    # Dépendances
├── /templates         # Templates HTML
│   ├── base.html
│   ├── index.html
│   ├── combat.html
│   └── combat_summary.html
└── /static           # Fichiers statiques
    └── style.css
```

---

## ℹ️ Notes
- Application locale (pas de serveur distant)
- Sauvegarde automatique en SQLite
- Compatible D&D 2024
- Conçu pour une utilisation à table

---

## 🐛 Résolution de problèmes
- En cas d'erreur de base de données : supprimer `tracker.db` et redémarrer
- Si la vue joueur ne se met pas à jour : rafraîchir la page
- Pour réinitialiser : redémarrer l'application

---

## 🔧 Développement
Pour contribuer ou modifier :
- Forker le projet
- Créer une branche
- Faire les modifications
- Soumettre une pull request

### Workflow dev / preprod / prod

Un guide complet est disponible ici :

- `docs/deployment/git-flow-preprod-prod.md`

Résumé rapide:

- `develop` pour le dev local
- `preprod` pour déployer sur la préprod VPS privée
- `master` pour déployer la production VPS
---

## 📧 Configuration email (Hostinger)

Créez un fichier `.env` à la racine avec au minimum :

```env
MAIL_SERVER=smtp.hostinger.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=no-reply@jonathan-dupau.com
MAIL_PASSWORD=VOTRE_MOT_DE_PASSE_EMAIL
MAIL_DEFAULT_SENDER=no-reply@jonathan-dupau.com
```

Notes importantes :
- `MAIL_USERNAME` doit être la boîte email complète Hostinger.
- `MAIL_DEFAULT_SENDER` doit généralement être la même adresse (ou un alias autorisé par Hostinger).
- Utilisez `MAIL_PORT=465`, `MAIL_USE_TLS=false`, `MAIL_USE_SSL=true` si vous préférez SSL implicite.

Variables utiles en complément :

```env
SECRET_KEY=change-me
FLASK_CONFIG=development
DATABASE_URL=sqlite:///tracker.db
SESSION_COOKIE_SECURE=false
MAX_CONTENT_LENGTH_MB=256
```
