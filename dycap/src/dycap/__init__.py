"""dycap - Douyu Live Stream Collector.

A modular, async library for collecting chat messages from Douyu live streams.

Quick Start:
    # CLI
    dycap collect -r 6657

    # Python API
    from dycap import Collector, PostgreSQLStorage

    async with PostgreSQLStorage.create(room_id="6657", dsn="...") as storage:
        collector = Collector(storage)
        await collector.connect()
"""

from __future__ import annotations

from .collector import AsyncCollector
from .storage import CSVStorage, ConsoleStorage, PostgreSQLStorage, StorageHandler
from .types import DanmuMessage, MessageType

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # Collector
    "AsyncCollector",
    # Storage
    "StorageHandler",
    "PostgreSQLStorage",
    "CSVStorage",
    "ConsoleStorage",
    # Types
    "DanmuMessage",
    "MessageType",
]
