#!/usr/bin/env bash
# Update the server from this laptop. Run from the repo root, after git push.
#
#   deploy/deploy.sh user@192.168.1.14
#
# Refuses to run while the nightly update runs or with unpushed commits.
set -euo pipefail

TARGET="${1:?usage: deploy/deploy.sh user@host}"
KEY="${QUOTE_YARD_DEPLOY_KEY:-$HOME/.ssh/quote_yard_vivobook}"
SSH=(ssh -i "$KEY" -o BatchMode=yes -o IdentitiesOnly=yes "$TARGET")

git fetch -q origin 2>/dev/null || true
if [[ -n "$(git status --porcelain)" ]]; then echo "Uncommitted changes here; commit first." >&2; exit 1; fi
if [[ -n "$(git log origin/main..HEAD --oneline)" ]]; then echo "Unpushed commits; git push first." >&2; exit 1; fi

STATE="$("${SSH[@]}" 'systemctl --user is-active quote-yard-pipeline.service || true')"
if [[ "$STATE" == "active" || "$STATE" == "activating" ]]; then
    echo "The nightly update is running on the server; try again after it finishes." >&2
    exit 1
fi

echo "Building the site..."
(cd frontend && npm ci --silent && npm run build --silent)

echo "Updating the server..."
"${SSH[@]}" 'set -e; cd ~/quote-yard; git pull --ff-only -q; .venv/bin/pip install -q -r requirements.txt; .venv/bin/alembic upgrade head 2>/dev/null'
rsync -a --delete -e "ssh -i $KEY -o BatchMode=yes -o IdentitiesOnly=yes" frontend/dist/ "$TARGET:quote-yard/frontend/dist/"
"${SSH[@]}" 'systemctl --user restart quote-yard-api.service; sleep 3; curl -sf http://127.0.0.1:8000/api/v1/health'
echo
echo "Deployed $(git rev-parse --short HEAD)."
