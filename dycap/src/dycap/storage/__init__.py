"""Storage handlers for dycap."""

from __future__ import annotations

from .base import StorageHandler
from .console import ConsoleStorage
from .csv import CSVStorage
from .postgres import PostgreSQLStorage, PostgreSQLStorageFromDSN

__all__ = [
    "StorageHandler",
    "PostgreSQLStorage",
    "PostgreSQLStorageFromDSN",
    "CSVStorage",
    "ConsoleStorage",
]
