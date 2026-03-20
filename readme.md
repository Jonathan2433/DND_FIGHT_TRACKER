# ExalQuest — Gestionnaire de campagnes et combats D&D

ExalQuest est une application web Flask pensée pour les tables **Dungeons & Dragons** (MJ + joueurs).  
Elle centralise la préparation, le suivi et l’historique d’une campagne : personnages, arcs narratifs, épisodes, combats, expérience, notifications et rappels.

---

## 🎯 But de l’application

L’objectif d’ExalQuest est de fournir un **espace unique** pour :

- préparer une campagne (structure narrative + personnages),
- piloter les sessions en temps réel (combats, état des PJ/PNJ),
- conserver un historique exploitable après partie,
- fluidifier la collaboration entre MJ et joueurs.

En pratique, l’application évite de disperser les infos entre notes papier, feuilles PDF, messagerie et tableurs.

---

## ✅ Ce que vous pouvez faire avec ExalQuest

### 1) Comptes & accès
- Créer un compte / se connecter.
- Gérer son profil.
- Distinguer les capacités MJ et joueur selon le contexte campagne.

### 2) Campagnes
- Créer une campagne.
- Rejoindre une campagne (invitation / lien).
- Consulter ses campagnes (MJ et joueur).
- Paramétrer la campagne (dont calendrier de sessions).

### 3) Narration (arcs & épisodes)
- Créer et éditer des **arcs narratifs**.
- Créer et consulter des **épisodes** liés aux arcs.
- Conserver des notes de suivi (dont notes privées MJ/PJ selon les écrans).

### 4) Personnages, templates et PNJ
- Créer des personnages via templates.
- Gérer une bibliothèque de templates de PJ.
- Gérer les PNJ et leurs notes associées.
- Préparer les fiches avec champs enrichis (stats, infos complémentaires, etc.).

### 5) Combats temps réel
- Créer un combat et y associer les bons participants.
- Suivre initiative, tours, rounds et états.
- Mettre à jour PV, PV temporaires, CA, conditions, fuite.
- Utiliser des vues séparées MJ / joueurs.
- Afficher un résumé post-combat.

### 6) Progression & XP
- Gérer l’historique d’expérience.
- Suivre la progression de personnages/campagne.

### 7) Notifications & rappels
- Notifications in-app (centre de notifications + compteur non lu).
- Rappels de session via email (commande CLI dédiée à J-7).

### 8) Base de connaissances D&D
- Catalogue local des sorts (`app/data/spells_catalog.json`).
- Catalogue local des armes (`app/data/weapons_catalog.json`).
- Synchronisation des sorts mineurs via script (`scripts/fetch_cantrips.py`).

---

## 🧱 Architecture (mise à jour)

Le backend suit une organisation en couches :

- `app/web` : routes HTTP + événements Socket.IO,
- `app/application` : cas d’usage métier,
- `app/domain` : règles métier pures,
- `app/infrastructure` : persistance/technique,
- `app/shared` : composants transverses.

Des wrappers de compatibilité existent encore dans `app/services` et `app/routes`.

---

## ⚙️ Installation locale

### Prérequis
- Python 3.10+
- pip

### Étapes

```bash
# 1) Cloner le projet
# git clone <url-du-repo>
cd DND_FIGHT_TRACKER

# 2) Créer et activer un environnement virtuel
python -m venv venv
source venv/bin/activate      # Linux / macOS
# venv\Scripts\activate      # Windows PowerShell

# 3) Installer les dépendances
pip install -r requirements.txt

# 4) Lancer l’application
python run.py
```

Application disponible sur : `http://127.0.0.1:5000`

---

## 🐳 Option Docker

Le projet inclut :

- `docker-compose.yml`
- `docker-compose.preprod.yml`
- `Dockerfile`

Vous pouvez donc exécuter l’app en environnement conteneurisé selon votre contexte (local / préprod).

---

## 🔐 Variables d’environnement utiles

Créez un fichier `.env` à la racine.

### Email (Hostinger)

```env
MAIL_SERVER=smtp.hostinger.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=no-reply@jonathan-dupau.com
MAIL_PASSWORD=VOTRE_MOT_DE_PASSE_EMAIL
MAIL_DEFAULT_SENDER=no-reply@jonathan-dupau.com
```

### App / sécurité / upload

```env
SECRET_KEY=change-me
FLASK_CONFIG=development
DATABASE_URL=sqlite:///tracker.db
SESSION_COOKIE_SECURE=false
UPLOAD_MAX_MB=64
```

> `UPLOAD_MAX_MB` doit être cohérent avec la limite serveur (ex: Nginx `client_max_body_size`).

---

## 🛠️ Commandes utiles

### Rappels de sessions (J-7)

```bash
flask send-session-reminders
```

### Synchroniser les sorts mineurs

```bash
python scripts/fetch_cantrips.py
```

---

## 📂 Structure du projet (vue rapide)

```text
DND_FIGHT_TRACKER/
├── app/
│   ├── web/
│   ├── application/
│   ├── domain/
│   ├── infrastructure/
│   └── shared/
├── migrations/
├── templates/
├── static/
├── scripts/
├── docs/
├── run.py
└── requirements.txt
```

---

## 🚀 Workflow de déploiement

Consultez le guide :

- `docs/deployment/git-flow-preprod-prod.md`

Résumé :
- `develop` : développement local,
- `preprod` : déploiement préproduction,
- `master` : déploiement production.

---

## 🧪 Dépannage rapide

- Problème de base locale : vérifier `DATABASE_URL` et l’état des migrations.
- Upload bloqué : vérifier `UPLOAD_MAX_MB` et la config reverse proxy.
- Emails non envoyés : vérifier identifiants SMTP + port/TLS.
- Vue joueur désynchronisée : vérifier la connexion Socket.IO.

---

## 🤝 Contribution

1. Créer une branche.
2. Implémenter la modification.
3. Vérifier (tests / checks).
4. Ouvrir une Pull Request.
