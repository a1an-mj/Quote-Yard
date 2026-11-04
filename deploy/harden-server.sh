#!/usr/bin/env bash
# Locks the server down before launch. Run ON the VivoBook, once, with sudo:
#
#   sudo bash ~/quote-yard/deploy/harden-server.sh
#
# Safe to run again. Each step says what it does and checks itself before
# it applies anything that could lock you out.
#
#  1. The website gets its own database login (quote_yard_web): it can read
#     everything but write only account, saved, alert and shop tables. Its
#     password is made here and written to ~/quote-yard/.env; it is never shown.
#     A migration that adds a table the website must WRITE needs a GRANT for
#     quote_yard_web (new tables are readable automatically).
#  2. SSH: keys only, no passwords, no root login.
#  3. Firewall: SSH and the site only from the home network, SSH over
#     Tailscale (how the laptop reaches it from another house), nothing else in.
#  4. Security updates may restart the machine at 04:30 when they need to.
#  5. Battery charge capped at 80% (the laptop is always plugged in).
#  6. Proves last night's backup restores, in a throwaway database.
set -euo pipefail

HOME_NET="192.168.1.0/24"
SITE_PORT=8000
CHARGE_LIMIT=80
WEB_ROLE="quote_yard_web"
DB="quote_yard"
WRITE_TABLES="users email_codes user_sessions saved_products price_alerts vendors vendor_tokens vendor_sessions vendor_offers vendor_audit_log"

[[ $EUID -eq 0 ]] || { echo "Run with sudo: sudo bash $0" >&2; exit 1; }
OWNER="${SUDO_USER:?run through sudo from the normal account}"
OWNER_HOME="$(getent passwd "$OWNER" | cut -d: -f6)"
ENV_FILE="$OWNER_HOME/quote-yard/.env"
BACKUPS="$OWNER_HOME/quote-yard-backups"
step() { printf '\n== %s\n' "$*"; }
psql_q() { sudo -u postgres psql -v ON_ERROR_STOP=1 -qAt "$@"; }

# ---------------------------------------------------------------- 1. database login
step "1/6 Website database login ($WEB_ROLE)"
PASS="$(openssl rand -hex 24)"
psql_q -d "$DB" <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$WEB_ROLE') THEN
    CREATE ROLE $WEB_ROLE LOGIN;
  END IF;
END \$\$;
ALTER ROLE $WEB_ROLE WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD '$PASS';
GRANT CONNECT ON DATABASE $DB TO $WEB_ROLE;
GRANT USAGE ON SCHEMA public TO $WEB_ROLE;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM $WEB_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO $WEB_ROLE;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO $WEB_ROLE;
ALTER DEFAULT PRIVILEGES FOR ROLE "$OWNER" IN SCHEMA public GRANT SELECT ON TABLES TO $WEB_ROLE;
ALTER DEFAULT PRIVILEGES FOR ROLE "$OWNER" IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO $WEB_ROLE;
SQL
for t in $WRITE_TABLES; do psql_q -d "$DB" -c "GRANT INSERT, UPDATE, DELETE ON $t TO $WEB_ROLE;"; done

URL="postgresql+psycopg://$WEB_ROLE:$PASS@127.0.0.1/$DB"
# Prove it works and cannot touch prices, before the website uses it.
PGPASSWORD="$PASS" psql -h 127.0.0.1 -U "$WEB_ROLE" -d "$DB" -qAtc "SELECT count(*) FROM listings" >/dev/null \
  || { echo "The new login cannot connect; .env left unchanged." >&2; exit 1; }
if PGPASSWORD="$PASS" psql -h 127.0.0.1 -U "$WEB_ROLE" -d "$DB" -qAtc \
     "BEGIN; UPDATE listings SET current_price = current_price WHERE false; ROLLBACK;" >/dev/null 2>&1; then
  echo "The new login can change prices; stopping." >&2; exit 1
fi
touch "$ENV_FILE"
grep -v '^QUOTE_YARD_API_DATABASE_URL=' "$ENV_FILE" > "$ENV_FILE.new" || true
printf 'QUOTE_YARD_API_DATABASE_URL=%s\n' "$URL" >> "$ENV_FILE.new"
chown "$OWNER": "$ENV_FILE.new"; chmod 600 "$ENV_FILE.new"; mv "$ENV_FILE.new" "$ENV_FILE"
unset PASS URL
echo "Done. It can read prices but not change them. Written to .env (not shown)."

# ---------------------------------------------------------------- 2. ssh
step "2/6 SSH: keys only"
if [[ ! -s "$OWNER_HOME/.ssh/authorized_keys" ]]; then
  echo "No SSH key in $OWNER_HOME/.ssh/authorized_keys; leaving passwords on so you are not locked out."
else
  cat > /etc/ssh/sshd_config.d/10-quote-yard.conf <<EOF
# Set by quote-yard deploy/harden-server.sh. The first value read wins, so this file beats 50-cloud-init.conf.
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
EOF
  sshd -t || { rm -f /etc/ssh/sshd_config.d/10-quote-yard.conf; echo "SSH settings did not check out; undone." >&2; exit 1; }
  systemctl reload ssh
  sshd -T | grep -E '^(passwordauthentication|permitrootlogin) '
  echo "Done. Your open session stays connected; new logins need the key."
fi

# ---------------------------------------------------------------- 3. firewall
step "3/6 Firewall"
echo "Current rules:"; ufw status numbered || true
read -r -p "Replace them with: SSH and port $SITE_PORT from $HOME_NET, SSH over Tailscale, nothing else in? [y/N] " ok
if [[ "$ok" == [yY] ]]; then
  ufw --force reset >/dev/null
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow from "$HOME_NET" to any port 22 proto tcp comment 'ssh, home network'
  ufw allow from "$HOME_NET" to any port "$SITE_PORT" proto tcp comment 'quote yard, home network'
  # Kept so a re-run cannot lock out remote access once the server lives elsewhere.
  ufw allow in on tailscale0 to any port 22 proto tcp comment 'ssh over tailscale'
  ufw --force enable
  ufw status verbose
else
  echo "Skipped."
fi

# ---------------------------------------------------------------- 4. updates
step "4/6 Security updates may restart at 04:30"
cat > /etc/apt/apt.conf.d/52quote-yard-reboot <<'EOF'
// Set by quote-yard deploy/harden-server.sh. Only when an update needs it; after the 03:30 backup.
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-WithUsers "true";
Unattended-Upgrade::Automatic-Reboot-Time "04:30";
EOF
systemctl is-enabled unattended-upgrades
echo "Done."

# ---------------------------------------------------------------- 5. battery
step "5/6 Battery charge limit ${CHARGE_LIMIT}%"
LIMIT_FILE="$(ls /sys/class/power_supply/BAT*/charge_control_end_threshold 2>/dev/null | head -1 || true)"
if [[ -z "$LIMIT_FILE" ]]; then
  echo "This battery has no charge limit control; skipped."
else
  # The firmware forgets the limit on every boot, so a small service sets it again.
  cat > /etc/systemd/system/battery-charge-limit.service <<EOF
[Unit]
Description=Cap battery charge at ${CHARGE_LIMIT}% (always-plugged-in server)
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo ${CHARGE_LIMIT} > ${LIMIT_FILE}'

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable --now battery-charge-limit.service
  echo "Limit now: $(cat "$LIMIT_FILE")%"
fi

# ---------------------------------------------------------------- 6. backup restore test
step "6/6 Restoring last night's backup into a throwaway database"
DUMP="$(ls -1t "$BACKUPS"/quote_yard-*.dump 2>/dev/null | head -1 || true)"
if [[ -z "$DUMP" ]]; then
  echo "No backup found in $BACKUPS."
else
  TEST_DB="quote_yard_restore_test"
  sudo -u postgres dropdb --if-exists "$TEST_DB"
  sudo -u postgres createdb "$TEST_DB"
  sudo -u postgres pg_restore --no-owner --no-privileges -d "$TEST_DB" < "$DUMP"
  for t in listings price_history users canonical_products; do
    printf '  %-20s backup %8s   live %8s\n' "$t" \
      "$(psql_q -d "$TEST_DB" -c "SELECT count(*) FROM $t")" "$(psql_q -d "$DB" -c "SELECT count(*) FROM $t")"
  done
  sudo -u postgres dropdb "$TEST_DB"
  echo "Done: $(basename "$DUMP") restores. (Live counts can be a little higher: the backup is from last night.)"
fi

printf '\nAll steps finished. Tell Claude, who will restart the website on its new login and check it.\n'
