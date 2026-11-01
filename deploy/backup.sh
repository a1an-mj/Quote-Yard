#!/usr/bin/env bash
# Back up the database and raw data. Run nightly by deploy/install-backup.sh.
#
# Keeps the newest 14 daily backups and the newest 6 from the 1st of a month.
# A dump is checked before it replaces anything. It holds user emails and
# password hashes, so the folder is private to this user.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR="${QUOTE_YARD_BACKUP_DIR:-$HOME/quote-yard-backups}"
DB="${QUOTE_YARD_BACKUP_DB:-quote_yard}"
DATA="${QUOTE_YARD_BACKUP_DATA:-$REPO/data}"
DAILY=14
MONTHLY=6

umask 077
mkdir -p "$DIR"
chmod 700 "$DIR"
STAMP="$(date +%Y-%m-%d)"
TMP="$(mktemp -d "$DIR/.tmp.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

pg_dump -Fc -f "$TMP/db.dump" "$DB"
# A readable table of contents with the tables we can't lose, or the backup failed.
TOC="$(pg_restore --list "$TMP/db.dump")"
for table in listings price_history users; do
    grep -q "TABLE DATA public $table " <<<"$TOC" || { echo "Backup has no $table data" >&2; exit 1; }
done
tar -C "$(dirname "$DATA")" -cf "$TMP/data.tar" "$(basename "$DATA")"

mv "$TMP/db.dump" "$DIR/quote_yard-$STAMP.dump"
mv "$TMP/data.tar" "$DIR/data-$STAMP.tar"

prune() { # prefix extension
    local files keep
    files="$(ls -1 "$DIR" | grep -E "^$1-[0-9]{4}-[0-9]{2}-[0-9]{2}\.$2$" | sort -r)"
    keep="$( { head -n "$DAILY" <<<"$files"; grep -E -- '-01\.' <<<"$files" | head -n "$MONTHLY" || true; } | sort -u)"
    grep -vxF -f <(printf '%s\n' "$keep") <<<"$files" | while read -r old; do
        [ -n "$old" ] && rm -f "$DIR/$old"
    done || true
}
prune quote_yard dump
prune data tar

echo "Backed up to $DIR: $(du -h "$DIR/quote_yard-$STAMP.dump" | cut -f1) database, $(du -h "$DIR/data-$STAMP.tar" | cut -f1) data, $(ls "$DIR" | grep -c '\.dump$') dumps kept"
