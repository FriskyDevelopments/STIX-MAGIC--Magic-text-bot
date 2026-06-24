#!/usr/bin/env bash
# Deploy Pupbot to a RackNerd VPS over SSH (from laptop or GitHub Actions).
#
# Required:
#   RACKNERD_HOST          — IP or hostname from RackNerd welcome email
# Optional:
#   RACKNERD_USER          — default root
#   RACKNERD_SSH_KEY_FILE  — path to private key (default: ~/.ssh/id_ed25519)
#   RACKNERD_DEPLOY_PATH   — default /opt/pupbot
#   PUPBOT_REPO_BRANCH     — default main

set -euo pipefail

: "${RACKNERD_HOST:?Set RACKNERD_HOST}"

RACKNERD_USER="${RACKNERD_USER:-root}"
RACKNERD_DEPLOY_PATH="${RACKNERD_DEPLOY_PATH:-/opt/pupbot}"
PUPBOT_REPO_BRANCH="${PUPBOT_REPO_BRANCH:-main}"
SSH_KEY="${RACKNERD_SSH_KEY_FILE:-${HOME}/.ssh/id_ed25519}"

SSH_OPTS=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new)
if [[ -f "$SSH_KEY" ]]; then
  SSH_OPTS+=(-i "$SSH_KEY")
fi

REMOTE="${RACKNERD_USER}@${RACKNERD_HOST}"

echo "Deploying to ${REMOTE}:${RACKNERD_DEPLOY_PATH} (branch ${PUPBOT_REPO_BRANCH})"

ssh "${SSH_OPTS[@]}" "$REMOTE" bash -s <<EOF
set -euo pipefail
DEPLOY_PATH="${RACKNERD_DEPLOY_PATH}"
BRANCH="${PUPBOT_REPO_BRANCH}"

if [[ ! -d "\${DEPLOY_PATH}/.git" ]]; then
  echo "No git repo at \${DEPLOY_PATH}. Run racknerd-bootstrap.sh on the server first." >&2
  exit 1
fi

cd "\${DEPLOY_PATH}"
sudo -u pupbot git fetch origin "\${BRANCH}"
sudo -u pupbot git checkout "\${BRANCH}"
sudo -u pupbot git pull --ff-only origin "\${BRANCH}"
sudo -u pupbot "\${DEPLOY_PATH}/venv/bin/pip" install -r requirements.txt
sudo systemctl restart pupbot
sudo systemctl is-active --quiet pupbot && echo "pupbot service: active"
EOF

echo "Deploy complete."
