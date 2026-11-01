#!/usr/bin/env bash
# Run deploy/backup.sh every day at 03:30, after the nightly update.
#
#   deploy/install-backup.sh            install and start the timer
#   deploy/install-backup.sh --remove   stop and remove it (backups stay)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
NAME=quote-yard-backup

if [[ "${1:-}" == "--remove" ]]; then
    systemctl --user disable --now "$NAME.timer" 2>/dev/null || true
    rm -f "$UNIT_DIR/$NAME.service" "$UNIT_DIR/$NAME.timer"
    systemctl --user daemon-reload
    echo "Removed $NAME"
    exit 0
fi

mkdir -p "$UNIT_DIR"
cat > "$UNIT_DIR/$NAME.service" <<UNIT
[Unit]
Description=Quote Yard database and data backup
OnFailure=quote-yard-notify@%n.service

[Service]
Type=oneshot
ExecStart=$REPO/deploy/backup.sh
Nice=10
UNIT
cat > "$UNIT_DIR/$NAME.timer" <<UNIT
[Unit]
Description=Back up Quote Yard every day at 03:30

[Timer]
OnCalendar=*-*-* 03:30:00
Persistent=true

[Install]
WantedBy=timers.target
UNIT
"$REPO/deploy/install-notify.sh"
systemctl --user daemon-reload
systemctl --user enable --now "$NAME.timer"
systemctl --user list-timers "$NAME.timer" --no-pager
