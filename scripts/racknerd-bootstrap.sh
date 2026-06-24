#!/usr/bin/env bash
# One-time RackNerd (or any Ubuntu VPS) setup for Pupbot.
# Run as root on the server:
#   curl -fsSL https://raw.githubusercontent.com/FriskyDevelopments/STIX-MAGIC--Magic-text-bot/main/scripts/racknerd-bootstrap.sh | bash
# Or copy this repo and: sudo bash scripts/racknerd-bootstrap.sh

set -euo pipefail

DEPLOY_PATH="${RACKNERD_DEPLOY_PATH:-/opt/pupbot}"
REPO_URL="${PUPBOT_REPO_URL:-https://github.com/FriskyDevelopments/STIX-MAGIC--Magic-text-bot.git}"
REPO_BRANCH="${PUPBOT_REPO_BRANCH:-main}"
ENV_FILE="${PUPBOT_ENV_FILE:-/etc/pupbot/pupbot.env}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root (sudo)." >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git python3 python3-venv python3-pip ca-certificates

id -u pupbot &>/dev/null || useradd --system --home-dir "$DEPLOY_PATH" --shell /usr/sbin/nologin pupbot
mkdir -p "$DEPLOY_PATH" /etc/pupbot
chown pupbot:pupbot "$DEPLOY_PATH"

if [[ ! -d "$DEPLOY_PATH/.git" ]]; then
  sudo -u pupbot git clone --branch "$REPO_BRANCH" --depth 1 "$REPO_URL" "$DEPLOY_PATH"
else
  sudo -u pupbot git -C "$DEPLOY_PATH" fetch origin "$REPO_BRANCH"
  sudo -u pupbot git -C "$DEPLOY_PATH" checkout "$REPO_BRANCH"
  sudo -u pupbot git -C "$DEPLOY_PATH" pull --ff-only origin "$REPO_BRANCH"
fi

sudo -u pupbot python3 -m venv "$DEPLOY_PATH/venv"
sudo -u pupbot "$DEPLOY_PATH/venv/bin/pip" install --upgrade pip
sudo -u pupbot "$DEPLOY_PATH/venv/bin/pip" install -r "$DEPLOY_PATH/requirements.txt"

if [[ ! -f "$ENV_FILE" ]]; then
  cat >"$ENV_FILE" <<'EOF'
# Pupbot on RackNerd — edit then: systemctl restart pupbot
TELEGRAM_BOT_TOKEN=
STIX_ALLOW_POLLING=1
STIX_TRANSPORT=polling
STIX_CLEAR_WEBHOOK_BEFORE_POLL=1
EOF
  chmod 600 "$ENV_FILE"
  echo "Created ${ENV_FILE} — add TELEGRAM_BOT_TOKEN before starting."
fi

install -m 644 "$DEPLOY_PATH/deploy/systemd/pupbot.service" /etc/systemd/system/pupbot.service
systemctl daemon-reload
systemctl enable pupbot

echo "Bootstrap done."
echo "  1. Edit ${ENV_FILE} (set TELEGRAM_BOT_TOKEN)"
echo "  2. systemctl start pupbot"
echo "  3. systemctl status pupbot"
