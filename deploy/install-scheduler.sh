#!/usr/bin/env bash
# Install (or remove) the daily Quote Yard update as a systemd user timer.
#
#   deploy/install-scheduler.sh            install and start the timer
#   deploy/install-scheduler.sh --remove   stop and remove it
#
# Runs `python -m pipeline` from this repo every day at 02:00 local time
# (plus up to 15 minutes of random delay). A run missed while the machine
# was off or asleep starts at the next boot / login. On a server, also run
# `loginctl enable-linger $USER` so the timer runs without a login session.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$REPO/.venv/bin/python"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
NAME=quote-yard-pipeline

if [[ "${1:-}" == "--remove" ]]; then
    systemctl --user disable --now "$NAME.timer" 2>/dev/null || true
    rm -f "$UNIT_DIR/$NAME.service" "$UNIT_DIR/$NAME.timer"
    systemctl --user daemon-reload
    echo "Removed $NAME.timer and $NAME.service"
    exit 0
fi

[[ -x "$PYTHON" ]] || { echo "No virtualenv python at $PYTHON" >&2; exit 1; }
mkdir -p "$UNIT_DIR"

cat > "$UNIT_DIR/$NAME.service" <<UNIT
[Unit]
Description=Quote Yard daily update (scrape, process, load, match)
Documentation=file://$REPO/README.md
OnFailure=quote-yard-notify@%n.service

[Service]
Type=oneshot
WorkingDirectory=$REPO
# Mail settings; the leading - means the file is optional.
EnvironmentFile=-$REPO/.env
ExecStart=$PYTHON -m pipeline
# A full run takes about 40 minutes; stop a stuck run after 3 hours.
TimeoutStartSec=3h
Nice=10
IOSchedulingClass=idle
UNIT

cat > "$UNIT_DIR/$NAME.timer" <<UNIT
[Unit]
Description=Run the Quote Yard update every day at 02:00

[Timer]
OnCalendar=*-*-* 02:00:00
RandomizedDelaySec=15min
Persistent=true

[Install]
WantedBy=timers.target
UNIT

"$REPO/deploy/install-notify.sh"
systemctl --user daemon-reload
systemctl --user enable --now "$NAME.timer"
echo "Installed. Next run:"
systemctl --user list-timers "$NAME.timer" --no-pager
