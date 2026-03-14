# Déploiement Git avec environnements dev / préprod / prod

Ce document met en place exactement le flux demandé:

- **dev local**: branche `develop`
- **préprod VPS privée**: push de `preprod`
- **prod VPS**: push de `master`

## 1) Stratégie de branches

- `master` : production
- `preprod` : environnement de préproduction (staging)
- `develop` : intégration continue de dev locale
- `feature/*` : branches de travail

Flux recommandé:

1. Développer en local sur `feature/*`
2. Merge vers `develop`
3. Quand c'est stable, merge `develop` -> `preprod`
4. Push `preprod` vers le remote VPS pour déployer la préprod
5. Après validation, merge `preprod` -> `master`
6. Push `master` vers le remote VPS pour déployer prod

## 2) Fichiers d'environnement

Sur le VPS (dans les worktrees):

- Préprod: copier `.env.preprod.example` vers `.env.preprod` et renseigner les secrets.
- Prod: copier `.env.prod.example` vers `.env.prod` et renseigner les secrets.

⚠️ Ne jamais commiter les fichiers `.env.*` réels.

## 3) Compose dédiés

- `docker-compose.preprod.yml`:
  - DB dédiée `postgres_data_preprod`
  - App exposée en local VPS sur `127.0.0.1:5001`
- `docker-compose.prod.yml`:
  - DB dédiée `postgres_data_prod`
  - App prod exposée sur `5000`

Tu peux ensuite mettre un reverse proxy Nginx:

- `preprod.exemple.com` -> `127.0.0.1:5001` avec **IP whitelist** (ton IP uniquement)
- `exemple.com` -> `127.0.0.1:5000`

## 4) Installation côté VPS (une fois)

Depuis le repo applicatif (ou en copiant le script), exécuter:

```bash
bash scripts/vps/setup_git_deploy.sh /opt/exalquest.git /var/www/exalquest-prod /var/www/exalquest-preprod
```

Ce script:

- initialise un bare repo `/opt/exalquest.git`
- installe un hook `post-receive`
- route les déploiements par branche:
  - `master` -> `/var/www/exalquest-prod`
  - `preprod` -> `/var/www/exalquest-preprod`

## 5) Côté local: config Git

```bash
git checkout -b develop
git checkout -b preprod

git remote add vps ssh://<user>@<vps>/opt/exalquest.git
```

Déploiement préprod:

```bash
git checkout preprod
git push vps preprod
```

Déploiement prod:

```bash
git checkout master
git push vps master
```

## 6) Sécurisation minimale recommandée

- Accès SSH par clé uniquement (désactiver mot de passe).
- Fail2ban + firewall (ufw).
- Préprod non publique (whitelist IP dans Nginx).
- Secrets différents entre préprod et prod.
- Sauvegardes DB séparées (préprod/prod).

