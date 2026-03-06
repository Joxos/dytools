# Room ID Migration Scripts

This directory contains migration scripts to update room_id format in the dytools database.

## Background

In earlier versions of dytools, room_id was stored in a compound format:
```
SHORT_ID:REAL_ID  (e.g., "6657:6979222")
```

The new version uses only the real room ID:
```
REAL_ID  (e.g., "6979222")
```

This migration updates all existing records to use the new format.

## Files

- **migrate_room_id.py** - Core Python migration script
- **migrate_room_id.sh** - Interactive wrapper with safety checks
- **README.md** - This file

## Quick Start

### 1. Check What Will Change (Dry Run)

```bash
export DYTOOLS_DSN="postgresql://user:pass@localhost/db"
python scripts/migrate_room_id.py --dry-run
```

Example output:
```
📋 Migration Preview:
======================================================================
Old Format           New Format         Records
----------------------------------------------------------------------
6657:6979222         6979222          1,056,697
9999:9999            9999                   981
----------------------------------------------------------------------
TOTAL                                 1,057,678
======================================================================
```

### 2. Run Migration (Interactive)

The shell wrapper provides safety checks and confirmation prompts:

```bash
./scripts/migrate_room_id.sh
```

It will:
1. Run a dry-run preview
2. Ask for confirmation
3. Recommend creating a backup
4. Perform the migration with progress output
5. Verify the results

### 3. Run Migration (Direct)

If you prefer to run the Python script directly:

```bash
# Create backup first
pg_dump "$DYTOOLS_DSN" > backup_$(date +%Y%m%d_%H%M%S).sql

# Run migration
python scripts/migrate_room_id.py --verbose
```

## Options

### Python Script Options

```
python scripts/migrate_room_id.py [OPTIONS]

Options:
  --dsn DSN         PostgreSQL connection string (default: from DYTOOLS_DSN)
  --dry-run         Show what would be changed without modifying data
  -v, --verbose     Show detailed progress information
  -h, --help        Show help message
```

### Shell Wrapper

```bash
./scripts/migrate_room_id.sh
```

No options needed - it's interactive and will guide you through the process.

## Safety Features

### Dry Run Mode

Always previews changes before applying them:
```bash
python scripts/migrate_room_id.py --dry-run
```

### Backup Recommendation

The shell wrapper reminds you to create a backup:
```bash
pg_dump "$DYTOOLS_DSN" > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Verification

After migration, the script automatically verifies that no compound formats remain:
```
✅ Verification passed: No compound formats remaining
```

### Transaction Safety

All updates are performed in a single transaction - if anything fails, all changes are rolled back.

## Examples

### Example 1: Preview Only

```bash
export DYTOOLS_DSN="postgresql://douyu:douyu6657@localhost:5432/douyu_danmu"
python scripts/migrate_room_id.py --dry-run
```

Output:
```
🔍 Analyzing room_id formats in database...

📋 Migration Preview:
======================================================================
Old Format           New Format         Records
----------------------------------------------------------------------
6657:6979222         6979222          1,056,697
9999:9999            9999                   981
----------------------------------------------------------------------
TOTAL                                 1,057,678
======================================================================

🔒 DRY RUN - No changes made
Run without --dry-run to perform migration
```

### Example 2: Full Migration with Verbose Output

```bash
export DYTOOLS_DSN="postgresql://douyu:douyu6657@localhost:5432/douyu_danmu"

# Backup first
pg_dump "$DYTOOLS_DSN" > backup_$(date +%Y%m%d_%H%M%S).sql

# Run migration
python scripts/migrate_room_id.py --verbose
```

Output:
```
🔍 Analyzing room_id formats in database...

📋 Migration Preview:
======================================================================
Old Format           New Format         Records
----------------------------------------------------------------------
6657:6979222         6979222          1,056,697
9999:9999            9999                   981
----------------------------------------------------------------------
TOTAL                                 1,057,678
======================================================================

⚙️  Performing migration...
Migrating 6657:6979222 → 6979222... ✅ 1,056,697 records
Migrating 9999:9999 → 9999... ✅ 981 records

✅ Migration complete: 1,057,678 records updated

🔍 Verifying migration...
✅ Verification passed: No compound formats remaining
```

### Example 3: Interactive Shell Script

```bash
export DYTOOLS_DSN="postgresql://douyu:douyu6657@localhost:5432/douyu_danmu"
./scripts/migrate_room_id.sh
```

The script will interactively guide you through:
1. Showing the preview
2. Asking for confirmation
3. Reminding you to backup
4. Performing the migration
5. Showing the results

## Troubleshooting

### Error: DSN not provided

```
Error: DSN not provided. Use --dsn flag or set DYTOOLS_DSN environment variable.
```

**Solution**: Set the environment variable or use --dsn flag:
```bash
export DYTOOLS_DSN="postgresql://user:pass@localhost/db"
```

### Error: Failed to connect to database

```
Error: Failed to connect to database: connection to server failed
```

**Solution**: Check your DSN and ensure PostgreSQL is running:
```bash
psql "$DYTOOLS_DSN" -c "SELECT 1"
```

### Warning: Expected X but updated Y

```
WARNING: Expected 1,000 but updated 999
```

**Cause**: Data changed between the preview and migration (new records added/deleted).

**Solution**: This is usually harmless. Re-run the script to catch any remaining records.

## What If Something Goes Wrong?

### Restore from Backup

If you created a backup before migration:
```bash
# Drop and recreate database (CAUTION!)
dropdb douyu_danmu
createdb douyu_danmu

# Restore from backup
psql "$DYTOOLS_DSN" < backup_20260306_150000.sql
```

### Manual Rollback

If you need to rollback to compound format (not recommended):
```sql
-- Example: Convert 6979222 back to 6657:6979222
-- (You'll need to know the original short IDs)
UPDATE danmaku 
SET room_id = '6657:6979222' 
WHERE room_id = '6979222';
```

## After Migration

Once migration is complete:

1. ✅ New collector runs will use the real ID format automatically
2. ✅ All queries should work normally
3. ✅ Service management commands work with either format:
   ```bash
   dytools service create douyu:6657  # Still uses 6657 as input
   # But stores 6979222 internally after resolution
   ```

## Technical Details

### Algorithm

1. Query database for all unique room_id values and their counts
2. Identify compound format IDs using regex: `^\d+:\d+$`
3. Extract the real ID part (after the colon)
4. For each compound ID:
   ```sql
   UPDATE danmaku SET room_id = '<real_id>' WHERE room_id = '<short:real>';
   ```
5. Commit transaction
6. Verify no compound formats remain

### Performance

- Uses parameterized queries (safe from SQL injection)
- Single transaction (atomic - all or nothing)
- Bulk updates per unique room_id (efficient)
- Typical speed: ~100,000 records/second

### Idempotency

The script is idempotent - you can run it multiple times safely:
- Already migrated IDs are skipped automatically
- Only compound format IDs are touched
- If no compound formats exist, script exits cleanly

## See Also

- [dytools README](../README.md) - Main project documentation
- [AGENTS.md](../AGENTS.md) - Development guidelines
- [Commit dba4ed1](https://github.com/user/repo/commit/dba4ed1) - Original bug fix
