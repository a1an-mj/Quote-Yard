#!/usr/bin/env bash
# Run the website and API as a systemd user service on this machine.
#
#   deploy/install-api.sh          listen on this machine only (behind a tunnel)
#   deploy/install-api.sh --lan    also reachable on the home network, for testing
#   deploy/install-api.sh --remove stop and remove it
#
# Needs `loginctl enable-linger $USER` to run without a login session.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
NAME=quote-yard-api

if [[ "${1:-}" == "--remove" ]]; then
    systemctl --user disable --now "$NAME.service" 2>/dev/null || true
    rm -f "$UNIT_DIR/$NAME.service"
    systemctl --user daemon-reload
    echo "Removed $NAME.service"
    exit 0
fi

HOST=127.0.0.1
[[ "${1:-}" == "--lan" ]] && HOST=0.0.0.0
mkdir -p "$UNIT_DIR"

cat > "$UNIT_DIR/$NAME.service" <<UNIT
[Unit]
Description=Quote Yard website and API
After=network-online.target postgresql.service

[Service]
WorkingDirectory=$REPO
EnvironmentFile=-$REPO/.env
# The proxy flags let the rate limiters see real visitors behind a local tunnel.
ExecStart=$REPO/.venv/bin/uvicorn api.main:app --host $HOST --port 8000 --proxy-headers --forwarded-allow-ips=127.0.0.1
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
UNIT

systemctl --user daemon-reload
systemctl --user enable "$NAME.service"
systemctl --user restart "$NAME.service"
echo "Running on $HOST:8000"
