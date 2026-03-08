# dystat

Douyu Statistics Tools - analyze danmu data with rank, cluster, search, and prune.

## Installation

```bash
pip install dystat
```

## Quick Start

```bash
# Set DSN
export DYKIT_DSN="postgresql://user:pass@localhost:5432/douyu"

# Rank users by message count
dystat rank -r 6657 --top 10

# Rank content (repeated messages)
dystat rank -r 6657 --by content --top 10

# Cluster similar messages
dystat cluster -r 6657 --threshold 0.5

# Search messages
dystat search -r 6657 --content "hello"
dystat search -r 6657 --user "username"

# Remove duplicates
dystat prune -r 6657
```

## Commands

### rank

Rank users or content by frequency.

```bash
dystat rank -r 6657 --top 10                    # Top users (default)
dystat rank -r 6657 --by content --top 10      # Repeated content
dystat rank -r 6657 --type dgb --top 5         # Gift messages
dystat rank -r 6657 --days 7                   # Last 7 days
```

Options:
- `-r, --room ROOM` - Room ID (required)
- `--top N` - Number of results (default: 10)
- `--by user|content` - Rank mode (default: user)
- `--type TYPE` - Message type (default: chatmsg)
- `--days N` - Limit to recent N days

### cluster

Cluster similar messages using fuzzy text matching.

```bash
dystat cluster -r 6657 --threshold 0.5         # Default threshold
dystat cluster -r 6657 --limit 100             # More source messages
```

Options:
- `-r, --room ROOM` - Room ID (required)
- `--threshold FLOAT` - Similarity threshold 0-1 (default: 0.5)
- `--limit N` - Source message limit (default: 50)
- `--type TYPE` - Message type (default: chatmsg)

### search

Search messages with filters.

```bash
dystat search -r 6657 --content "hello"        # ILIKE search
dystat search -r 6657 --user "username"        # By username
dystat search -r 6657 --type dgb               # By message type
```

Options:
- `-r, --room ROOM` - Room ID (required)
- `--content TEXT` - Content filter (ILIKE)
- `--user USERNAME` - Username exact match
- `--user-id UID` - User ID exact match
- `--type TYPE` - Message type
- `--limit N` - Result limit (default: 100)
- `--from TIME` - From timestamp (ISO format)
- `--to TIME` - To timestamp (ISO format)

### prune

Remove duplicate messages.

```bash
dystat prune -r 6657
```

Options:
- `-r, --room ROOM` - Room ID (required)

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DYKIT_DSN` | PostgreSQL connection string |
| `DYSTAT_DSN` | Alias for DYKIT_DSN |

## License

MIT
