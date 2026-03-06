"""Service manager for systemd --user service operations."""

from __future__ import annotations

import re
import subprocess


class ServiceManager:
    """Manage systemd user services for danmu collection."""

    @staticmethod
    def parse_service_name(spec: str) -> tuple[str, str]:
        """Parse service name specification into service name and room ID.

        Args:
            spec: Service name in NAME:ROOM format (e.g., "douyu:6657").

        Returns:
            Tuple of (service_name, room_id) where service_name has colons
            replaced with hyphens.

        Raises:
            ValueError: If spec format is invalid.
        """
        pattern = r"^([a-zA-Z0-9:_.@-]+):(\d+)$"
        match = re.match(pattern, spec)
        if not match:
            raise ValueError(
                f"Invalid service name format: {spec}. "
                "Expected NAME:ROOM (e.g., douyu:6657)"
            )
        name, room_id = match.groups()
        service_name = name.replace(":", "-") + "-" + room_id
        return (service_name, room_id)

    def _systemctl(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        """Execute systemctl --user command with given arguments.

        Args:
            args: List of arguments to pass to systemctl --user.

        Returns:
            CompletedProcess object with returncode, stdout, stderr.
            Does not raise on non-zero exit code - caller handles errors.
        """
        return subprocess.run(
            ['systemctl', '--user'] + args,
            capture_output=True,
            text=True,
            check=False
        )
