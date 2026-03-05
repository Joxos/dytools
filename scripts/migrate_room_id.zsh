#!/usr/bin/env zsh
# migrate_room_id.zsh — Manual migration for room_id format and content whitespace
# Usage: DYTOOLS_DSN="postgresql://..." zsh scripts/migrate_room_id.zsh
# WARNING: Run this ONLY after verifying the new collector works correctly.

set -euo pipefail

DSN=${DYTOOLS_DSN:?"Please set DYTOOLS_DSN environment variable"}

echo "=== Step 1: Strip whitespace from chatmsg content ==="
psql "$DSN" -c "UPDATE danmaku SET content = TRIM(content) WHERE msg_type = 'chatmsg' AND content IS NOT NULL AND content != TRIM(content);"

echo "=== Step 2: Migrate room_id format ==="
echo "Add room mappings below (short_id:real_id):"
# Example: Room 6657 maps to real ID 6979222
psql "$DSN" -c "UPDATE danmaku SET room_id = '6657:6979222' WHERE room_id IN ('6657', '6979222');"
# Add more room mappings as needed:
# psql "$DSN" -c "UPDATE danmaku SET room_id = 'SHORT:REAL' WHERE room_id IN ('SHORT', 'REAL');"

echo "=== Step 3: Add raw_data column if not exists ==="
psql "$DSN" -c "ALTER TABLE danmaku ADD COLUMN IF NOT EXISTS raw_data JSONB;"

echo "=== Migration complete ==="
echo "Verify: psql \"$DSN\" -c \"SELECT DISTINCT room_id FROM danmaku LIMIT 10;\""
