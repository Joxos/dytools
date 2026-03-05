#!/usr/bin/env zsh
# trim_whitespace.zsh — Remove leading/trailing whitespace from database content fields
# Usage: DYTOOLS_DSN="postgresql://..." zsh scripts/trim_whitespace.zsh
# WARNING: This script is idempotent and safe to run multiple times.

set -euo pipefail

DSN=${DYTOOLS_DSN:?"Please set DYTOOLS_DSN environment variable"}

echo "=== Trimming whitespace from content field ==="
RESULT=$(psql "$DSN" -c "UPDATE danmaku SET content = TRIM(content) WHERE content IS NOT NULL AND content != TRIM(content);" 2>&1)
echo "$RESULT"

echo "=== Trimming whitespace from username field ==="
RESULT=$(psql "$DSN" -c "UPDATE danmaku SET username = TRIM(username) WHERE username IS NOT NULL AND username != TRIM(username);" 2>&1)
echo "$RESULT"

echo "=== Whitespace trimming complete ==="
