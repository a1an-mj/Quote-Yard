#!/usr/bin/env bash
# A temporary public HTTPS link to the site, for showing testers before the
# domain is bought. Run ON the server as the normal user (no sudo):
#
#   bash ~/quote-yard/deploy/install-preview-tunnel.sh
#   bash ~/quote-yard/deploy/install-preview-tunnel.sh link     # print the current link
#
# Uses a Cloudflare "quick tunnel": free, no account, no open ports. The link
# (https://<random words>.trycloudflare.com) CHANGES whenever the tunnel or
# the machine restarts. Replace with a named tunnel once the domain exists,
# then: systemctl --user disable --now quote-yard-preview-tunnel.service
set -euo pipefail

UNIT=quote-yard-preview-tunnel.service
BIN="$HOME/.local/bin/cloudflared"

link() {
    journalctl --user -u "$UNIT" --since "$(systemctl --user show -p ActiveEnterTimestamp --value "$UNIT")" \
        --no-pager -o cat 2>/dev/null | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | tail -1
}

if [[ "${1:-}" == "link" ]]; then
    link || echo "No link yet; is the tunnel running? systemctl --user status $UNIT"
    exit 0
fi

[[ -x "$BIN" ]] || { echo "Install cloudflared at $BIN first." >&2; exit 1; }
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/$UNIT" <<EOF
[Unit]
Description=Quote Yard preview link (Cloudflare quick tunnel)
After=network-online.target quote-yard-api.service
Wants=network-online.target

[Service]
ExecStart=$BIN tunnel --no-autoupdate --url http://127.0.0.1:8000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable "$UNIT" >/dev/null
systemctl --user restart "$UNIT"
for _ in $(seq 30); do
    url="$(link || true)"
    [[ -n "$url" ]] && { echo "Preview link: $url"; exit 0; }
    sleep 1
done
echo "Tunnel started but no link yet; check: journalctl --user -u $UNIT" >&2
exit 1
