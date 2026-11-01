#!/usr/bin/env bash
# Copy the server's newest backup to this laptop, so a dead server loses nothing.
#
#   deploy/pull-backup.sh user@192.168.1.14
#
# Saved in ~/quote-yard-offsite-backups; the newest 7 are kept.
set -euo pipefail

TARGET="${1:?usage: deploy/pull-backup.sh user@host}"
KEY="${QUOTE_YARD_DEPLOY_KEY:-$HOME/.ssh/quote_yard_vivobook}"
DEST="${QUOTE_YARD_OFFSITE_DIR:-$HOME/quote-yard-offsite-backups}"
SSH=(ssh -i "$KEY" -o BatchMode=yes -o IdentitiesOnly=yes "$TARGET")

umask 077
mkdir -p "$DEST"
chmod 700 "$DEST"
LATEST="$("${SSH[@]}" 'cd ~/quote-yard-backups && ls -1 quote_yard-*.dump | sort | tail -1')"
STAMP="${LATEST#quote_yard-}"; STAMP="${STAMP%.dump}"
for file in "quote_yard-$STAMP.dump" "data-$STAMP.tar"; do
    "${SSH[@]}" "cat ~/quote-yard-backups/$file" > "$DEST/.$file.part"
    mv "$DEST/.$file.part" "$DEST/$file"
done
pg_restore --list "$DEST/quote_yard-$STAMP.dump" >/dev/null
cd "$DEST"
ls -1 quote_yard-*.dump | sort -r | tail -n +8 | while read -r old; do
    day="${old#quote_yard-}"; day="${day%.dump}"
    rm -f "$old" "data-$day.tar"
done
echo "Saved $STAMP in $DEST"
