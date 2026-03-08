#!/usr/bin/env zsh
# backup_database.zsh — Create a compressed backup of the PostgreSQL database
# Usage: DYKIT_DSN="postgresql://..." zsh scripts/backup_database.zsh

set -euo pipefail

DSN=${DYKIT_DSN:?"Please set DYKIT_DSN environment variable"}

# Check if pg_dump is available.
if ! command -v pg_dump &> /dev/null; then
    echo "Error: pg_dump not found. Please install PostgreSQL client tools." >&2
    exit 1
fi

# Create backups directory if it doesn't exist.
mkdir -p ./backups

# Generate timestamped filename.
timestamp=$(date +%Y%m%d_%H%M%S)
backup_file="./backups/backup_${timestamp}.sql.gz"

echo "Starting backup..."
echo "DSN: $DSN"
echo "Output: $backup_file"

# Create the backup using pg_dump with plain SQL format and pipe through gzip.
# --format=plain produces human-readable SQL text.
# --no-owner avoids ownership issues on restore.
# --no-privileges avoids permission issues on restore.
if pg_dump --format=plain --no-owner --no-privileges "$DSN" | gzip > "$backup_file"; then
    file_size=$(ls -lh "$backup_file" | awk '{print $5}')
    echo "✓ Backup completed successfully"
    echo "File: $backup_file"
    echo "Size: $file_size"
else
    echo "Error: Backup failed. Check your DSN and database connectivity." >&2
    exit 1
fi
