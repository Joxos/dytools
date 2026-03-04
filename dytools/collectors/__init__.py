"""Collectors package for Douyu danmu message collection.

This package provides two collector implementations:
- SyncCollector: Blocking, thread-based WebSocket collector
- AsyncCollector: Non-blocking, asyncio-based WebSocket collector

Both collectors handle login, room joining, heartbeat maintenance, and
message parsing with UTF-8 safety via MessageBuffer.

Example Usage (Sync):
    ```python
    from dytools.collectors import SyncCollector
    from dytools.storage import CSVStorage

    with CSVStorage('output.csv') as storage:
        collector = SyncCollector(room_id=6657, storage=storage)
        collector.connect()  # Blocks until connection closes
    ```

Example Usage (Async):
    ```python
    import asyncio
    from dytools.collectors import AsyncCollector
    from dytools.storage import CSVStorage

    async def main():
        with CSVStorage('output.csv') as storage:
            collector = AsyncCollector(room_id=6657, storage=storage)
            await collector.connect()  # Await until connection closes

    asyncio.run(main())
    ```
"""

from .async_ import AsyncCollector
from .sync import SyncCollector

__all__ = ["SyncCollector", "AsyncCollector"]
