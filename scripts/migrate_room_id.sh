#!/bin/bash
# migrate_room_id.sh - Wrapper script for room_id migration
#
# This script wraps the Python migration script with safety checks and
# interactive confirmation.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATION_SCRIPT="${SCRIPT_DIR}/migrate_room_id.py"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python script exists
if [[ ! -f "$MIGRATION_SCRIPT" ]]; then
    echo -e "${RED}Error: Migration script not found at ${MIGRATION_SCRIPT}${NC}"
    exit 1
fi

# Check if DYTOOLS_DSN is set
if [[ -z "${DYTOOLS_DSN:-}" ]]; then
    echo -e "${RED}Error: DYTOOLS_DSN environment variable not set${NC}"
    echo "Please set it first:"
    echo "  export DYTOOLS_DSN='postgresql://user:pass@localhost/db'"
    exit 1
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Room ID Migration Tool${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}⚠️  WARNING: This will modify your database${NC}"
echo ""
echo "This script will:"
echo "  • Change room_id from compound format (e.g., 6657:6979222)"
echo "  • To real ID only (e.g., 6979222)"
echo ""

# Run dry-run first
echo -e "${BLUE}Step 1: Running analysis (dry-run)...${NC}"
echo ""

if ! uv run python "$MIGRATION_SCRIPT" --dry-run; then
    echo -e "${RED}Error: Dry-run failed${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Step 2: Confirm migration${NC}"
echo ""
echo "The above changes will be applied to your database."
read -p "Do you want to proceed? (yes/no): " confirm

if [[ "$confirm" != "yes" ]]; then
    echo -e "${YELLOW}Migration cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}Step 3: Creating backup recommendation...${NC}"
echo ""
echo -e "${YELLOW}💡 RECOMMENDATION: Backup your database first${NC}"
echo ""
echo "Suggested backup command:"
echo -e "${GREEN}pg_dump \"${DYTOOLS_DSN}\" > backup_\$(date +%Y%m%d_%H%M%S).sql${NC}"
echo ""
read -p "Have you created a backup? (yes/skip): " backup_confirm

if [[ "$backup_confirm" == "skip" ]]; then
    echo -e "${YELLOW}⚠️  Proceeding without backup${NC}"
elif [[ "$backup_confirm" != "yes" ]]; then
    echo -e "${YELLOW}Migration cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}Step 4: Performing migration...${NC}"
echo ""

if uv run python "$MIGRATION_SCRIPT" --verbose; then
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Migration completed successfully${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
else
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ Migration failed${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
fi
