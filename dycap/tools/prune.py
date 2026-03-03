"""Tool for merging and deduplicating CSV capture files.

This tool provides functionality to:
- Scan current directory for CSV files with pattern YYYYMMDD_HHMMSS_ROOMID.csv
- Merge CSV files by room_id (auto-detected from filename or data)
- Deduplicate messages based on (timestamp, username, content, user_id)
- Sort by timestamp ascending
- Output to {room_id}_pruned.csv files

Usage:
    python -m dycap prune                    # Auto-scan and group by room_id
    python -m dycap prune file1.csv file2.csv  # Merge specific files
    python -m dycap prune *.csv --output out.csv  # Custom output path
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

from dycap.log import logger


def run_prune(args) -> None:
    """Main entry point for prune command.

    Args:
        args: Argparse namespace with:
            - files: list of CSV file paths (or empty for auto-scan)
            - output: optional custom output path (single room_id mode only)
    """
    files = args.files or []

    # Auto-scan mode: no files specified
    if not files:
        logger.info("No files specified, scanning current directory...")
        files_to_process = _auto_scan_files()
        if not files_to_process:
            logger.warning("No CSV files found matching pattern YYYYMMDD_HHMMSS_ROOMID.csv")
            return

        # Group by room_id extracted from filename
        groups = _group_by_room_id_from_filename(files_to_process)

        # Process each group
        for room_id, file_list in groups.items():
            output_path = Path(f"{room_id}_pruned.csv")
            logger.info(f"Processing {len(file_list)} files for room_id={room_id}")
            merge_csvs(file_list, output_path)
            logger.info(f"Output: {output_path}")

        return

    # Manual file list mode
    file_paths = [Path(f) for f in files]

    # Validate all files exist
    for fp in file_paths:
        if not fp.exists():
            logger.error(f"File not found: {fp}")
            sys.exit(1)

    # Detect room_ids from CSV data (column 5)
    room_id_map = {}
    for fp in file_paths:
        room_id = _detect_room_id_from_data(fp)
        if room_id:
            room_id_map[fp] = room_id

    # Check if all files have same room_id
    unique_room_ids = set(room_id_map.values())

    if len(unique_room_ids) == 0:
        logger.error("Could not detect room_id from any CSV files")
        sys.exit(1)
    elif len(unique_room_ids) == 1:
        # Single room_id: merge directly
        room_id = unique_room_ids.pop()
        output_path = Path(args.output) if args.output else Path(f"{room_id}_pruned.csv")
        logger.info(f"Merging {len(file_paths)} files for room_id={room_id}")
        merge_csvs(file_paths, output_path)
        logger.info(f"Output: {output_path}")
    else:
        # Mixed room_ids: prompt user
        logger.warning("WARNING: Mixed room IDs detected:")
        for fp, rid in room_id_map.items():
            logger.warning(f"  {fp.name} → {rid}")

        choice = input("How to proceed? [y=merge all / a=auto-group / N=abort]: ").strip().lower()

        if choice == "y":
            # Merge all into single file
            output_path = Path(args.output) if args.output else Path("merged_pruned.csv")
            logger.info(f"Merging {len(file_paths)} files (mixed room_ids)")
            merge_csvs(file_paths, output_path)
            logger.info(f"Output: {output_path}")
        elif choice == "a":
            # Auto-group by room_id
            groups: dict[str, list[Path]] = {}
            for fp, rid in room_id_map.items():
                groups.setdefault(rid, []).append(fp)

            for room_id, file_list in groups.items():
                output_path = Path(f"{room_id}_pruned.csv")
                logger.info(f"Processing {len(file_list)} files for room_id={room_id}")
                merge_csvs(file_list, output_path)
                logger.info(f"Output: {output_path}")
        else:
            logger.info("Aborted.")
            sys.exit(0)


def merge_csvs(files: list[Path], output_path: Path) -> None:
    """Merge and deduplicate CSV files.

    Supports both old (6 columns) and new (7 columns with msg_type) formats.
    Deduplication key: (timestamp, username, content, user_id) - columns 0, 1, 2, 4
    This key is identical for both formats, ensuring proper deduplication across mixed files.
    Rows with fewer than 6 columns are skipped as invalid.
    Sort by: timestamp ascending (column 0)

    Args:
        files: List of CSV file paths to merge (can mix old 6-col and new 7-col formats)
        output_path: Output file path
    """
    seen = set()
    rows = []
    header = None

    # Read all files
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            file_header = next(reader, None)

            if file_header is None:
                logger.warning(f"Empty file: {filepath}")
                continue

            # Store first header
            if header is None:
                header = file_header

            # Read data rows
            for row in reader:
                if len(row) < 6:
                    continue  # Skip invalid rows

                # Dedup key: (timestamp, username, content, user_id)
                key = (row[0], row[1], row[2], row[4])

                if key not in seen:
                    seen.add(key)
                    rows.append(row)

    # Sort by timestamp ascending
    rows.sort(key=lambda r: r[0])

    # Write output
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if header:
            writer.writerow(header)
        writer.writerows(rows)

    logger.info(f"Merged {len(rows)} unique messages from {len(files)} files")


def _auto_scan_files() -> list[Path]:
    """Scan current directory for CSV files matching pattern YYYYMMDD_HHMMSS_ROOMID.csv.

    Returns:
        List of Path objects matching the pattern.
    """
    pattern = re.compile(r"^\d{8}_\d{6}_(\d+)\.csv$")
    cwd = Path.cwd()
    matching_files = []

    for filepath in cwd.glob("*.csv"):
        # Skip already-pruned files
        if filepath.name.endswith("_pruned.csv"):
            continue

        if pattern.match(filepath.name):
            matching_files.append(filepath)

    return matching_files


def _group_by_room_id_from_filename(files: list[Path]) -> dict[str, list[Path]]:
    """Group files by room_id extracted from filename pattern.

    Args:
        files: List of Path objects

    Returns:
        Dict mapping room_id → list of file paths
    """
    pattern = re.compile(r"^\d{8}_\d{6}_(\d+)\.csv$")
    groups: dict[str, list[Path]] = {}

    for filepath in files:
        match = pattern.match(filepath.name)
        if match:
            room_id = match.group(1)
            groups.setdefault(room_id, []).append(filepath)

    return groups


def _detect_room_id_from_data(filepath: Path) -> str | None:
    """Read CSV and extract room_id from first data row (column 5).

    Args:
        filepath: Path to CSV file

    Returns:
        room_id as string, or None if not found
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            first_row = next(reader, None)
            if first_row and len(first_row) >= 6:
                return first_row[5]  # room_id is column index 5
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")

    return None
