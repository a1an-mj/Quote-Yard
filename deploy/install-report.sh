#!/usr/bin/env bash
# Email a status report (counts and server health, no names or emails) at
# 07:00 and 14:00 every day. Run ON the server:
#
#   deploy/install-report.sh owner@example.com   install, or change the address
#   deploy/install-report.sh --remove            stop and remove it
#
# Try it without sending: .venv/bin/python -m api.status_report --print
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
NAME=quote-yard-report

if [[ "${1:-}" == "--remove" ]]; then
    systemctl --user disable --now "$NAME.timer" 2>/dev/null || true
    rm -f "$UNIT_DIR/$NAME.service" "$UNIT_DIR/$NAME.timer"
    systemctl --user daemon-reload
    echo "Removed $NAME"
    exit 0
fi

TO="${1:?usage: deploy/install-report.sh owner@example.com}"
[[ "$TO" == *@*.* ]] || { echo "That does not look like an email address: $TO" >&2; exit 1; }

mkdir -p "$UNIT_DIR"
cat > "$UNIT_DIR/$NAME.service" <<UNIT
[Unit]
Description=Email the Quote Yard status report
OnFailure=quote-yard-notify@%n.service

[Service]
Type=oneshot
WorkingDirectory=$REPO
EnvironmentFile=-$REPO/.env
Environment=QUOTE_YARD_REPORT_EMAIL=$TO
ExecStart=$REPO/.venv/bin/python -m api.status_report
UNIT
# The times here and SLOTS in api/status_report.py must match.
cat > "$UNIT_DIR/$NAME.timer" <<UNIT
[Unit]
Description=Email the Quote Yard status report at 07:00 and 14:00

[Timer]
OnCalendar=*-*-* 07,14:00:00
Persistent=true

[Install]
WantedBy=timers.target
UNIT
"$REPO/deploy/install-notify.sh"
systemctl --user daemon-reload
systemctl --user enable --now "$NAME.timer"
systemctl --user list-timers "$NAME.timer" --no-pager
