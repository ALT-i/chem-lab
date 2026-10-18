#!/bin/sh
# Backs up the CHM Virtual Lab database, media files and settings. Keeps 14 days.
# Schedule nightly with cron:  0 2 * * * /opt/chemlab/backup.sh >> /opt/chemlab/backups/backup.log 2>&1
set -e
# Everything written here is sensitive: the dump holds every student record
# and the Moodle token, .env holds the database password and secret key.
# Default umask would leave them world-readable on most hosts.
umask 077

CHEMLAB_DIR=${CHEMLAB_DIR:-/opt/chemlab}
BACKUP_DIR="$CHEMLAB_DIR/backups"
STAMP=$(date +%Y-%m-%d_%H%M)

cd "$CHEMLAB_DIR"
DB_NAME=$(grep '^DB_NAME=' .env | cut -d= -f2)
DB_USER=$(grep '^DB_USER=' .env | cut -d= -f2)

mkdir -p -m 700 "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"   # in case it already existed with looser permissions
docker compose exec -T db pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/db_$STAMP.dump"
tar -czf "$BACKUP_DIR/media_$STAMP.tar.gz" media
install -m 600 .env "$BACKUP_DIR/env_$STAMP"
find "$BACKUP_DIR" -type f -name "*_20*" -mtime +14 -delete

echo "Backup $STAMP done"
