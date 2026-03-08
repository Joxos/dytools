"""Storage handler base class and implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import DanmuMessage


class StorageHandler(ABC):
    """Abstract base class for danmu storage backends.

    All storage implementations must inherit from this class and implement
    the required async methods.

    Example:
        class MyStorage(StorageHandler):
            async def save(self, message: DanmuMessage) -> None:
                ...

            async def close(self) -> None:
                ...
    """

    @abstractmethod
    async def save(self, message: DanmuMessage) -> None:
        """Persist a single danmu message.

        Args:
            message: The danmu message to persist.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close and cleanup storage resources."""
        ...

    async def __aenter__(self) -> StorageHandler:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        await self.close()
