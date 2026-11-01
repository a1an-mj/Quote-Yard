#!/usr/bin/env bash
# The unit that emails a failure report. The other install scripts call this.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

mkdir -p "$UNIT_DIR"
cat > "$UNIT_DIR/quote-yard-notify@.service" <<UNIT
[Unit]
Description=Email a failure report for %i

[Service]
Type=oneshot
WorkingDirectory=$REPO
EnvironmentFile=-$REPO/.env
ExecStart=$REPO/.venv/bin/python -m api.notify_failure %i
UNIT
