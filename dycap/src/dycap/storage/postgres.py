"""PostgreSQL storage handler with batch write support."""

from __future__ import annotations

import asyncio
from typing import Any

import psycopg
from psycopg import AsyncConnection
from psycopg.types.json import Jsonb

from ..constants import DB_BATCH_FLUSH_INTERVAL_SECONDS, DB_BATCH_SIZE
from ..types import DanmuMessage
from .base import StorageHandler


class PostgreSQLStorage(StorageHandler):
    """Async PostgreSQL storage with batch write optimization.

    This storage handler buffers messages and writes them in batches
    to improve performance for high-frequency collection.

    The buffer is flushed when:
    - Buffer reaches DB_BATCH_SIZE (default 100)
    - DB_BATCH_FLUSH_INTERVAL_SECONDS (default 5) elapsed since last flush
    - Storage is closed

    Example:
        # Create with factory method
        storage = await PostgreSQLStorage.create(
            room_id="6657",
            host="localhost",
            port=5432,
            database="douyu",
            user="douyu",
            password="pass"
        )

        # Use as context manager
        async with storage:
            await storage.save(message1)
            await storage.save(message2)
        # Auto-flushes and closes
    """

    def __init__(
        self,
        room_id: str,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        batch_size: int = DB_BATCH_SIZE,
        flush_interval: float = DB_BATCH_FLUSH_INTERVAL_SECONDS,
    ) -> None:
        """Initialize PostgreSQL storage.

        Note: Use create() factory method instead of calling directly.

        Args:
            room_id: Room ID for this storage instance.
            host: PostgreSQL server hostname.
            port: PostgreSQL server port.
            database: Database name.
            user: Username.
            password: Password.
            batch_size: Number of messages to buffer before flushing.
            flush_interval: Maximum seconds between flushes.
        """
        self.room_id = room_id
        self._host = host
        self._port = port
        self._database = database
        self._user = user
        self._password = password
        self._batch_size = batch_size
        self._flush_interval = flush_interval

        self._connection: AsyncConnection[Any] | None = None
        self._buffer: list[DanmuMessage] = []
        self._flush_task: asyncio.Task[None] | None = None
        self._last_flush_time: float = 0
        self._closed = False

    @classmethod
    async def create(
        cls,
        room_id: str,
        host: str = "localhost",
        port: int = 5432,
        database: str = "douyu",
        user: str = "douyu",
        password: str = "",
        batch_size: int = DB_BATCH_SIZE,
        flush_interval: float = DB_BATCH_FLUSH_INTERVAL_SECONDS,
    ) -> PostgreSQLStorage:
        """Factory method to create and initialize PostgreSQL storage.

        Args:
            room_id: Room ID for this storage.
            host: PostgreSQL server hostname.
            port: PostgreSQL server port.
            database: Database name.
            user: Username.
            password: Password.
            batch_size: Number of messages to buffer before flushing.
            flush_interval: Maximum seconds between flushes.

        Returns:
            Initialized PostgreSQLStorage instance.
        """
        instance = cls(
            room_id=room_id,
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            batch_size=batch_size,
            flush_interval=flush_interval,
        )
        await instance._connect()
        return instance

    async def _connect(self) -> None:
        """Establish database connection and create schema."""
        self._connection = await AsyncConnection.connect(
            host=self._host,
            port=self._port,
            dbname=self._database,
            user=self._user,
            password=self._password,
        )
        await self._create_schema()
        self._last_flush_time = asyncio.get_running_loop().time()
        self._flush_task = asyncio.create_task(self._flush_loop())

    async def _create_schema(self) -> None:
        """Create danmaku table and indexes if not exists."""
        if self._connection is None:
            return

        async with self._connection.cursor() as cursor:
            schema_query = """
            CREATE TABLE IF NOT EXISTS danmaku (
                id          SERIAL PRIMARY KEY,
                timestamp   TIMESTAMP NOT NULL,
                room_id     TEXT NOT NULL,
                msg_type    TEXT NOT NULL,
                user_id     TEXT,
                username    TEXT,
                content     TEXT,
                user_level  INTEGER,
                gift_id     TEXT,
                gift_count  INTEGER,
                gift_name   TEXT,
                badge_level INTEGER,
                badge_name  TEXT,
                noble_level INTEGER,
                avatar_url  TEXT,
                raw_data    JSONB
            );
            CREATE INDEX IF NOT EXISTS idx_danmaku_room_time
                ON danmaku(room_id, timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_danmaku_user_id
                ON danmaku(user_id);
            CREATE INDEX IF NOT EXISTS idx_danmaku_msg_type
                ON danmaku(msg_type);
            """
            await cursor.execute(schema_query)
        await self._connection.commit()

    async def _flush_loop(self) -> None:
        """Background task to flush buffer periodically."""
        while not self._closed:
            await asyncio.sleep(self._flush_interval)
            if self._buffer and not self._closed:
                await self._flush()

    async def _flush(self) -> None:
        """Flush buffered messages to database."""
        if not self._buffer or self._connection is None:
            return

        messages = self._buffer.copy()
        self._buffer.clear()
        self._last_flush_time = asyncio.get_running_loop().time()

        try:
            async with self._connection.cursor() as cursor:
                # Batch insert using executemany
                insert_query = """
                INSERT INTO danmaku (
                    timestamp, room_id, msg_type, user_id, username, content,
                    user_level, gift_id, gift_count, gift_name,
                    badge_level, badge_name, noble_level, avatar_url, raw_data
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """

                values_list = [
                    (
                        msg.timestamp,
                        msg.room_id,
                        msg.msg_type.value,
                        msg.user_id,
                        msg.username,
                        msg.content,
                        msg.user_level,
                        msg.gift_id,
                        msg.gift_count,
                        msg.gift_name,
                        msg.badge_level,
                        msg.badge_name,
                        msg.noble_level,
                        msg.avatar_url,
                        Jsonb(msg.raw_data) if msg.raw_data else None,
                    )
                    for msg in messages
                ]

                await cursor.executemany(insert_query, values_list)
            await self._connection.commit()
        except Exception:
            await self._connection.rollback()
            # Re-add failed messages to buffer for retry
            self._buffer.extend(messages)
            raise

    async def save(self, message: DanmuMessage) -> None:
        """Add message to buffer (not immediately written).

        Message is buffered and written in batch when buffer is full
        or flush interval elapses.

        Args:
            message: Danmu message to save.
        """
        if self._closed:
            return

        self._buffer.append(message)

        if len(self._buffer) >= self._batch_size:
            await self._flush()

    async def close(self) -> None:
        """Close storage and flush remaining buffer."""
        if self._closed:
            return

        self._closed = True

        # Cancel flush task
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Final flush
        if self._buffer and self._connection:
            await self._flush()

        # Close connection
        if self._connection:
            await self._connection.close()
            self._connection = None


# Also support DSN-based creation
class PostgreSQLStorageFromDSN(PostgreSQLStorage):
    """PostgreSQL storage with DSN support.

    Example:
        storage = await PostgreSQLStorageFromDSN.create(
            room_id="6657",
            dsn="postgresql://user:pass@localhost:5432/douyu"
        )
    """

    @classmethod
    async def create(
        cls,
        room_id: str,
        dsn: str,
        batch_size: int = DB_BATCH_SIZE,
        flush_interval: float = DB_BATCH_FLUSH_INTERVAL_SECONDS,
    ) -> PostgreSQLStorage:
        """Create storage from DSN.

        Args:
            room_id: Room ID.
            dsn: PostgreSQL connection string.
            batch_size: Buffer size.
            flush_interval: Flush interval.
        """
        instance = cls(
            room_id=room_id,
            host="localhost",
            port=5432,
            database="douyu",
            user="douyu",
            password="",
            batch_size=batch_size,
            flush_interval=flush_interval,
        )

        # Connect with full DSN string so query options (e.g., search_path) are preserved.
        instance._connection = await AsyncConnection.connect(dsn)
        await instance._create_schema()
        instance._last_flush_time = asyncio.get_running_loop().time()
        instance._flush_task = asyncio.create_task(instance._flush_loop())
        return instance
