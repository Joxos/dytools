#!/usr/bin/env zsh
# trim_whitespace.zsh — Remove leading/trailing Unicode whitespace from database fields
# Usage: DYTOOLS_DSN="postgresql://..." zsh scripts/trim_whitespace.zsh
# WARNING: This script is idempotent and safe to run multiple times.

set -euo pipefail

DSN=${DYTOOLS_DSN:?"Please set DYTOOLS_DSN environment variable"}

echo "=== Trimming all Unicode whitespace from content field ==="
RESULT=$(psql "$DSN" -c "UPDATE danmaku SET content = REGEXP_REPLACE(content, '^\\s+|\\s+$', '', 'g') WHERE content IS NOT NULL AND content != REGEXP_REPLACE(content, '^\\s+|\\s+$', '', 'g');" 2>&1)
echo "$RESULT"

echo "=== Trimming all Unicode whitespace from username field ==="
RESULT=$(psql "$DSN" -c "UPDATE danmaku SET username = REGEXP_REPLACE(username, '^\\s+|\\s+$', '', 'g') WHERE username IS NOT NULL AND username != REGEXP_REPLACE(username, '^\\s+|\\s+$', '', 'g');" 2>&1)
echo "$RESULT"

echo "=== Whitespace trimming complete ==="
