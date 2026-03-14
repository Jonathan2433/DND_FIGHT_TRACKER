#!/usr/bin/env bash
set -euo pipefail

# Setup d'un déploiement Git bare-repo pour preprod + prod sur un VPS.
# Usage:
#   ./scripts/vps/setup_git_deploy.sh /opt/exalquest.git /var/www/exalquest-prod /var/www/exalquest-preprod

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 <bare_repo_path> <prod_work_tree> <preprod_work_tree>"
  exit 1
fi

BARE_REPO="$1"
PROD_WORK_TREE="$2"
PREPROD_WORK_TREE="$3"

mkdir -p "$BARE_REPO" "$PROD_WORK_TREE" "$PREPROD_WORK_TREE"

if [[ ! -d "$BARE_REPO/refs" ]]; then
  git init --bare "$BARE_REPO"
fi

cat > "$BARE_REPO/hooks/post-receive" <<'HOOK'
#!/usr/bin/env bash
set -euo pipefail

while read -r _oldrev _newrev refname; do
  branch="${refname#refs/heads/}"

  case "$branch" in
    master)
      echo "[deploy] master -> production"
      git --work-tree="__PROD_WORK_TREE__" --git-dir="__BARE_REPO__" checkout -f master
      cd "__PROD_WORK_TREE__"
      docker compose -f docker-compose.prod.yml pull
      docker compose -f docker-compose.prod.yml up -d --build
      ;;
    preprod)
      echo "[deploy] preprod -> préproduction"
      git --work-tree="__PREPROD_WORK_TREE__" --git-dir="__BARE_REPO__" checkout -f preprod
      cd "__PREPROD_WORK_TREE__"
      docker compose -f docker-compose.preprod.yml pull
      docker compose -f docker-compose.preprod.yml up -d --build
      ;;
    *)
      echo "[deploy] branche ignorée: $branch"
      ;;
  esac

done
HOOK

sed -i "s|__BARE_REPO__|$BARE_REPO|g" "$BARE_REPO/hooks/post-receive"
sed -i "s|__PROD_WORK_TREE__|$PROD_WORK_TREE|g" "$BARE_REPO/hooks/post-receive"
sed -i "s|__PREPROD_WORK_TREE__|$PREPROD_WORK_TREE|g" "$BARE_REPO/hooks/post-receive"

chmod +x "$BARE_REPO/hooks/post-receive"

echo "✅ Bare repo prêt: $BARE_REPO"
echo "✅ Hook installé: $BARE_REPO/hooks/post-receive"
echo "➡️ Ensuite, sur ton poste local:"
echo "   git remote add vps ssh://<user>@<vps>$BARE_REPO"
echo "   git push vps preprod   # déploie preprod"
echo "   git push vps master    # déploie prod"
