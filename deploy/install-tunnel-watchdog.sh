#!/usr/bin/env bash
# Every 5 minutes, open the preview link. If it has died for 15 minutes while
# the internet works, restart the tunnel (at most every 30 minutes). Email each
# new working link. Run ON the server:
#
#   deploy/install-tunnel-watchdog.sh owner@example.com   install, or change the address
#   deploy/install-tunnel-watchdog.sh --remove            stop and remove it
#
# See what it sees, changing nothing: .venv/bin/python -m api.tunnel_watchdog --print
# Remove it once the site has a domain and a named tunnel.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
NAME=quote-yard-tunnel-watchdog

if [[ "${1:-}" == "--remove" ]]; then
    systemctl --user disable --now "$NAME.timer" 2>/dev/null || true
    rm -f "$UNIT_DIR/$NAME.service" "$UNIT_DIR/$NAME.timer"
    systemctl --user daemon-reload
    echo "Removed $NAME"
    exit 0
fi

TO="${1:?usage: deploy/install-tunnel-watchdog.sh owner@example.com}"
[[ "$TO" == *@*.* ]] || { echo "That does not look like an email address: $TO" >&2; exit 1; }

mkdir -p "$UNIT_DIR"
cat > "$UNIT_DIR/$NAME.service" <<UNIT
[Unit]
Description=Check the Quote Yard preview link and restart the tunnel if it died
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=$REPO
EnvironmentFile=-$REPO/.env
Environment=QUOTE_YARD_TUNNEL_EMAIL=$TO
ExecStart=$REPO/.venv/bin/python -m api.tunnel_watchdog
UNIT
cat > "$UNIT_DIR/$NAME.timer" <<UNIT
[Unit]
Description=Check the Quote Yard preview link every 5 minutes

[Timer]
OnBootSec=3min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
UNIT
systemctl --user daemon-reload
systemctl --user enable --now "$NAME.timer"
systemctl --user list-timers "$NAME.timer" --no-pager
