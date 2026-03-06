"""Templates for systemd service unit files."""

from __future__ import annotations

UNIT_FILE_TEMPLATE = """
[Unit]
Description={description}
After=network-online.target

[Service]
Type=simple
Environment="DYTOOLS_DSN={dsn}"
ExecStart={dytools_path} collect --room {room_id}
Restart=on-failure

[Install]
WantedBy=default.target
"""
