#!/usr/bin/env bash
# The site's public address, https://quoteyard.in, through a Cloudflare named
# tunnel: no open ports on the server. Run ON the server as the normal user:
#
#   bash ~/quote-yard/deploy/install-site-tunnel.sh
#
# Once, before this (set up on 2026-11-14):
#   ~/.local/bin/cloudflared tunnel login                 # pick quoteyard.in
#   ~/.local/bin/cloudflared tunnel create quote-yard
#   ~/.local/bin/cloudflared tunnel route dns quote-yard quoteyard.in
#   ~/.local/bin/cloudflared tunnel route dns quote-yard www.quoteyard.in
#
# The tunnel's settings are in ~/.cloudflared/quote-yard.yml, not config.yml,
# so other cloudflared commands do not pick them up by accident.
set -euo pipefail

UNIT=quote-yard-tunnel.service
BIN="$HOME/.local/bin/cloudflared"
CONFIG="$HOME/.cloudflared/quote-yard.yml"

[[ -x "$BIN" ]] || { echo "Install cloudflared at $BIN first." >&2; exit 1; }
if [[ ! -f "$CONFIG" ]]; then
    ID="$("$BIN" tunnel list -n quote-yard -o json | python3 -c 'import sys,json; print(json.load(sys.stdin)[0]["id"])')"
    cat > "$CONFIG" <<CONF
tunnel: $ID
credentials-file: $HOME/.cloudflared/$ID.json
no-autoupdate: true
ingress:
  - hostname: quoteyard.in
    service: http://127.0.0.1:8000
  - hostname: www.quoteyard.in
    service: http://127.0.0.1:8000
  - service: http_status:404
CONF
    chmod 600 "$CONFIG"
fi
"$BIN" --config "$CONFIG" tunnel ingress validate

mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/$UNIT" <<EOF2
[Unit]
Description=Quote Yard site link quoteyard.in (Cloudflare named tunnel)
After=network-online.target quote-yard-api.service
Wants=network-online.target

[Service]
ExecStart=$BIN --config $CONFIG tunnel run quote-yard
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF2
systemctl --user daemon-reload
systemctl --user enable --now "$UNIT" >/dev/null
sleep 5
systemctl --user is-active "$UNIT"
