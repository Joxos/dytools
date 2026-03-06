"""Service manager for systemd --user service operations."""

from __future__ import annotations

import glob
import os
import re
import shutil
import subprocess
import sys

import click

from .templates import UNIT_FILE_TEMPLATE


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
                f"Invalid service name format: {spec}. Expected NAME:ROOM (e.g., douyu:6657)"
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
            ["systemctl", "--user"] + args, capture_output=True, text=True, check=False
        )

    def create(self, spec: str, dsn: str | None = None) -> None:
        """Create and start a new systemd user service.

        Args:
            spec: Service specification in NAME:ROOM format (e.g., "douyu:6657").
            dsn: PostgreSQL DSN. If None, reads from DYTOOLS_DSN env var.

        Raises:
            ValueError: If DSN not provided or spec format invalid.
            RuntimeError: If systemctl commands fail.
        """
        # Parse name
        service_name, room_id = self.parse_service_name(spec)

        # Get DSN
        dsn = dsn or os.environ.get("DYTOOLS_DSN")
        if not dsn:
            raise ValueError(
                "DSN not provided. Use --dsn flag or set DYTOOLS_DSN environment variable."
            )

        # Determine dytools path
        dytools_path = shutil.which("dytools")
        if not dytools_path:
            dytools_path = f"{sys.executable} -m dytools"

        # Prepare paths
        service_dir = os.path.expanduser("~/.config/systemd/user/")
        os.makedirs(service_dir, exist_ok=True)
        unit_file_path = os.path.join(service_dir, f"{service_name}.service")

        # Render template
        content = UNIT_FILE_TEMPLATE.format(
            description=f"Douyu danmu collector for room {room_id}",
            room_id=room_id,
            dytools_path=dytools_path,
            dsn=dsn,
        )

        # Write unit file
        with open(unit_file_path, "w") as f:
            f.write(content)

        # daemon-reload
        result = self._systemctl(["daemon-reload"])
        if result.returncode != 0:
            raise RuntimeError(f"daemon-reload failed: {result.stderr}")

        # enable
        result = self._systemctl(["enable", f"{service_name}.service"])
        if result.returncode != 0:
            raise RuntimeError(f"enable failed: {result.stderr}")

        # start
        result = self._systemctl(["start", f"{service_name}.service"])
        if result.returncode != 0:
            raise RuntimeError(f"start failed: {result.stderr}")

        click.echo(f"✓ Service {service_name} created and started")
        click.echo(f"  Unit file: {unit_file_path}")
        click.echo("  Warning: Service will stop when you log out.", err=True)
        click.echo("           Run 'loginctl enable-linger' for persistence.", err=True)

    def list(self) -> list[dict[str, str]]:
        """List all dytools-managed systemd user services.

        Returns:
            List of dicts with keys 'name', 'status', 'room_id'.
            Status can be 'active', 'inactive', or 'unknown'.
            Returns empty list if service directory doesn't exist.
        """
        service_dir = os.path.expanduser("~/.config/systemd/user/")

        # Return empty if directory doesn't exist
        if not os.path.exists(service_dir):
            return []

        # Find all service files
        pattern = os.path.join(service_dir, "*.service")
        service_files = glob.glob(pattern)

        services = []
        for path in service_files:
            # Read file and check if it's a dytools service
            try:
                with open(path, "r") as f:
                    content = f.read()
                    if "dytools collect" not in content:
                        continue  # skip non-dytools services
            except OSError:
                continue  # skip unreadable files

            # Extract service name
            service_name = os.path.basename(path).removesuffix(".service")

            # Get status
            result = self._systemctl(["is-active", f"{service_name}.service"])
            if result.returncode == 0:
                status = "active"
            elif result.returncode == 3:
                status = "inactive"
            else:
                status = "unknown"

            # Extract room_id from name (last part after final hyphen)
            parts = service_name.split("-")
            room_id = parts[-1] if parts and parts[-1].isdigit() else "unknown"

            services.append({"name": service_name, "status": status, "room_id": room_id})

        return services

    def remove(self, service_name: str) -> None:
        """Remove a systemd user service.

        Stops the service if running, disables it, deletes the unit file,
        and runs daemon-reload to update systemd state.

        Args:
            service_name: Name of the service to remove (without .service suffix).

        Raises:
            FileNotFoundError: If service unit file doesn't exist.
            RuntimeError: If daemon-reload fails.
        """
        # Build path to unit file
        service_dir = os.path.expanduser("~/.config/systemd/user/")
        unit_file_path = os.path.join(service_dir, f"{service_name}.service")

        # Check if unit file exists
        if not os.path.exists(unit_file_path):
            raise FileNotFoundError(
                f"Service '{service_name}' not found. Expected unit file at {unit_file_path}"
            )

        # Stop service (ignore errors - may already be stopped)
        self._systemctl(["stop", f"{service_name}.service"])

        # Disable service (ignore errors - may not be enabled)
        self._systemctl(["disable", f"{service_name}.service"])

        # Delete unit file
        os.remove(unit_file_path)

        # daemon-reload to update systemd state
        result = self._systemctl(["daemon-reload"])
        if result.returncode != 0:
            raise RuntimeError(f"daemon-reload failed: {result.stderr}")

        click.echo(f"✓ Service {service_name} removed")
