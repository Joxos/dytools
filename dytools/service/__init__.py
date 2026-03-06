"""Service management for dytools systemd --user integration.

This package provides service management functionality for running dytools
collectors as systemd user services. It includes service creation, template
management, and systemd unit file generation.

Classes:
    ServiceManager: Manage systemd user services for danmu collection.
"""

from __future__ import annotations

from .manager import ServiceManager

__all__ = [
    "ServiceManager",
]
