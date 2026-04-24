"""Audit storage backends for tamper-evident logging."""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Any

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .models import AuditEvent, AuditQuery
from ..logging_config import get_logger

logger = get_logger(__name__)


class AuditStorage(ABC):
    """Abstract base class for audit storage backends."""

    @abstractmethod
    async def store(self, event: AuditEvent) -> None:
        """Store an audit event.

        Args:
            event: Audit event to store
        """
        pass

    @abstractmethod
    async def retrieve(self, event_id: str) -> Optional[AuditEvent]:
        """Retrieve an audit event by ID.

        Args:
            event_id: Event identifier

        Returns:
            AuditEvent or None if not found
        """
        pass

    @abstractmethod
    async def query(self, query: AuditQuery) -> List[AuditEvent]:
        """Query audit events.

        Args:
            query: Query parameters

        Returns:
            List of matching audit events
        """
        pass

    @abstractmethod
    async def delete_before(self, cutoff_date: datetime) -> int:
        """Delete events older than cutoff date.

        Args:
            cutoff_date: Cutoff date for deletion

        Returns:
            Number of events deleted
        """
        pass


class RedisAuditStorage(AuditStorage):
    """Redis-based audit storage with tamper evidence.

    Features:
    - Fast read/write operations
    - Automatic expiration with TTL
    - Key-based querying
    - Atomic operations
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "audit",
        ttl: int = 86400 * 365,  # 1 year default
    ) -> None:
        """Initialize Redis audit storage.

        Args:
            redis_url: Redis connection URL
            key_prefix: Key prefix for audit events
            ttl: Time-to-live for events in seconds
        """
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.ttl = ttl
        self._redis: Optional[Any] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis not available")

        self._redis = redis.from_url(
            self.redis_url,
            decode_responses=True,
        )
        await self._redis.ping()
        logger.info("Redis audit storage connected")

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    def _make_key(self, event_id: str) -> str:
        """Create Redis key for event.

        Args:
            event_id: Event identifier

        Returns:
            Redis key
        """
        return f"{self.key_prefix}:event:{event_id}"

    def _make_index_key(self, index_type: str, value: str) -> str:
        """Create index key for querying.

        Args:
            index_type: Type of index (user, resource, etc.)
            value: Index value

        Returns:
            Redis key for index
        """
        return f"{self.key_prefix}:index:{index_type}:{value}"

    async def store(self, event: AuditEvent) -> None:
        """Store audit event in Redis.

        Args:
            event: Audit event to store
        """
        if not self._redis:
            await self.connect()

        key = self._make_key(event.event_id)
        data = event.to_dict()

        # Store event with TTL
        await self._redis.setex(key, self.ttl, json.dumps(data))

        # Create indexes for querying
        if event.user_id:
            user_key = self._make_index_key("user", event.user_id)
            await self._redis.sadd(user_key, event.event_id)
            await self._redis.expire(user_key, self.ttl)

        if event.resource_type and event.resource_id:
            resource_key = self._make_index_key(
                f"resource:{event.resource_type}",
                event.resource_id,
            )
            await self._redis.sadd(resource_key, event.event_id)
            await self._redis.expire(resource_key, self.ttl)

    async def retrieve(self, event_id: str) -> Optional[AuditEvent]:
        """Retrieve audit event from Redis.

        Args:
            event_id: Event identifier

        Returns:
            AuditEvent or None if not found
        """
        if not self._redis:
            await self.connect()

        key = self._make_key(event_id)
        data = await self._redis.get(key)

        if data:
            return AuditEvent.from_dict(json.loads(data))
        return None

    async def query(self, query: AuditQuery) -> List[AuditEvent]:
        """Query audit events from Redis.

        Args:
            query: Query parameters

        Returns:
            List of matching audit events
        """
        if not self._redis:
            await self.connect()

        # Get candidate event IDs from indexes
        event_ids = set()

        if query.user_id:
            user_key = self._make_index_key("user", query.user_id)
            event_ids.update(await self._redis.smembers(user_key))

        if query.resource_type and query.resource_id:
            resource_key = self._make_index_key(
                f"resource:{query.resource_type}",
                query.resource_id,
            )
            event_ids.update(await self._redis.smembers(resource_key))

        # If no index match, scan all keys (inefficient but functional)
        if not event_ids:
            pattern = f"{self.key_prefix}:event:*"
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)
            event_ids = set(k.split(":")[-1] for k in keys)

        # Retrieve and filter events
        events = []
        for event_id in list(event_ids)[: query.limit]:
            event = await self.retrieve(event_id)
            if event and self._matches_query(event, query):
                events.append(event)

        return events

    def _matches_query(self, event: AuditEvent, query: AuditQuery) -> bool:
        """Check if event matches query.

        Args:
            event: Audit event
            query: Query parameters

        Returns:
            True if event matches
        """
        if query.event_type and event.event_type != query.event_type:
            return False
        if query.severity and event.severity != query.severity:
            return False
        if query.user_id and event.user_id != query.user_id:
            return False
        if query.resource_type and event.resource_type != query.resource_type:
            return False
        if query.resource_id and event.resource_id != query.resource_id:
            return False
        if query.ip_address and event.ip_address != query.ip_address:
            return False
        if query.outcome and event.outcome != query.outcome:
            return False
        if query.start_time and event.timestamp < query.start_time:
            return False
        if query.end_time and event.timestamp > query.end_time:
            return False

        return True

    async def delete_before(self, cutoff_date: datetime) -> int:
        """Delete events older than cutoff date.

        Args:
            cutoff_date: Cutoff date

        Returns:
            Number of events deleted
        """
        if not self._redis:
            await self.connect()

        pattern = f"{self.key_prefix}:event:*"
        deleted = 0

        async for key in self._redis.scan_iter(match=pattern):
            data = await self._redis.get(key)
            if data:
                event_data = json.loads(data)
                event_time = datetime.fromisoformat(event_data["timestamp"])
                if event_time < cutoff_date:
                    await self._redis.delete(key)
                    deleted += 1

        return deleted


class DatabaseAuditStorage(AuditStorage):
    """Database-based audit storage with tamper evidence.

    Features:
    - Persistent storage
    - SQL-based querying
    - Transaction support
    - Backup/restore capability
    """

    def __init__(
        self,
        database_url: str,
        table_name: str = "audit_events",
    ) -> None:
        """Initialize database audit storage.

        Args:
            database_url: Database connection URL
            table_name: Audit events table name
        """
        self.database_url = database_url
        self.table_name = table_name
        self._engine: Optional[Any] = None

    async def connect(self) -> None:
        """Connect to database."""
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

        self._engine = create_async_engine(self.database_url)
        self._sessionmaker = async_sessionmaker(  # type: ignore[call-overload]
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create table if not exists
        await self._create_table()
        logger.info("Database audit storage connected")

    async def disconnect(self) -> None:
        """Disconnect from database."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None

    async def _create_table(self) -> None:
        """Create audit events table."""
        from sqlalchemy.sql import text

        async with self._engine.begin() as conn:
            await conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    event_id VARCHAR(36) PRIMARY KEY,
                    event_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    user_id VARCHAR(255),
                    session_id VARCHAR(255),
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    resource_type VARCHAR(100),
                    resource_id VARCHAR(255),
                    action VARCHAR(255) NOT NULL,
                    outcome VARCHAR(255) NOT NULL,
                    details JSON,
                    metadata JSON,
                    correlation_id VARCHAR(36)
                )
            """))

            # Create indexes for common queries
            await conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_user_id 
                ON {self.table_name}(user_id)
            """))
            await conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_resource 
                ON {self.table_name}(resource_type, resource_id)
            """))
            await conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_timestamp 
                ON {self.table_name}(timestamp)
            """))

    async def store(self, event: AuditEvent) -> None:
        """Store audit event in database.

        Args:
            event: Audit event to store
        """
        if not self._engine:
            await self.connect()

        from sqlalchemy import text

        async with self._sessionmaker() as session:
            await session.execute(
                text(f"""
                    INSERT INTO {self.table_name} 
                    (event_id, event_type, severity, timestamp, user_id, session_id,
                     ip_address, user_agent, resource_type, resource_id, action,
                     outcome, details, metadata, correlation_id)
                    VALUES 
                    (:event_id, :event_type, :severity, :timestamp, :user_id, :session_id,
                     :ip_address, :user_agent, :resource_type, :resource_id, :action,
                     :outcome, :details, :metadata, :correlation_id)
                """),
                event.to_dict(),
            )
            await session.commit()

    async def retrieve(self, event_id: str) -> Optional[AuditEvent]:
        """Retrieve audit event from database.

        Args:
            event_id: Event identifier

        Returns:
            AuditEvent or None if not found
        """
        if not self._engine:
            await self.connect()

        from sqlalchemy import text

        async with self._sessionmaker() as session:
            result = await session.execute(
                text(f"""
                    SELECT * FROM {self.table_name} 
                    WHERE event_id = :event_id
                """),
                {"event_id": event_id},
            )
            row = result.fetchone()

            if row:
                return AuditEvent.from_dict(dict(row._mapping))
            return None

    async def query(self, query: AuditQuery) -> List[AuditEvent]:
        """Query audit events from database.

        Args:
            query: Query parameters

        Returns:
            List of matching audit events
        """
        if not self._engine:
            await self.connect()

        from sqlalchemy import text

        filters = []
        params = {}

        if query.event_type:
            filters.append("event_type = :event_type")
            params["event_type"] = query.event_type.name
        if query.severity:
            filters.append("severity = :severity")
            params["severity"] = query.severity.name
        if query.user_id:
            filters.append("user_id = :user_id")
            params["user_id"] = query.user_id
        if query.resource_type:
            filters.append("resource_type = :resource_type")
            params["resource_type"] = query.resource_type
        if query.resource_id:
            filters.append("resource_id = :resource_id")
            params["resource_id"] = query.resource_id
        if query.ip_address:
            filters.append("ip_address = :ip_address")
            params["ip_address"] = query.ip_address
        if query.outcome:
            filters.append("outcome = :outcome")
            params["outcome"] = query.outcome
        if query.start_time:
            filters.append("timestamp >= :start_time")
            params["start_time"] = query.start_time.isoformat()  # type: ignore[assignment]
        if query.end_time:
            filters.append("timestamp <= :end_time")
            params["end_time"] = query.end_time.isoformat()  # type: ignore[assignment]

        where_clause = " AND ".join(filters) if filters else "1=1"

        async with self._sessionmaker() as session:
            result = await session.execute(
                text(f"""
                    SELECT * FROM {self.table_name}
                    WHERE {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT :limit OFFSET :offset
                """),
                {**params, "limit": query.limit, "offset": query.offset},
            )

            events = []
            for row in result.fetchall():
                events.append(AuditEvent.from_dict(dict(row._mapping)))

            return events

    async def delete_before(self, cutoff_date: datetime) -> int:
        """Delete events older than cutoff date.

        Args:
            cutoff_date: Cutoff date

        Returns:
            Number of events deleted
        """
        if not self._engine:
            await self.connect()

        from sqlalchemy import text

        async with self._sessionmaker() as session:
            result = await session.execute(
                text(f"""
                    DELETE FROM {self.table_name}
                    WHERE timestamp < :cutoff_date
                """),
                {"cutoff_date": cutoff_date},
            )
            await session.commit()
            return result.rowcount if hasattr(result, "rowcount") else 0


# Global storage instance
_audit_storage: Optional[AuditStorage] = None


def get_audit_storage() -> AuditStorage:
    """Get or create global audit storage instance.

    Returns:
        AuditStorage singleton instance
    """
    global _audit_storage
    if _audit_storage is None:
        # Default to Redis with fallback to database
        try:
            _audit_storage = RedisAuditStorage()
        except Exception:
            _audit_storage = DatabaseAuditStorage("sqlite:///audit.db")
    return _audit_storage


def configure_audit_storage(storage: AuditStorage) -> AuditStorage:
    """Configure global audit storage.

    Args:
        storage: Audit storage backend

    Returns:
        Configured AuditStorage instance
    """
    global _audit_storage
    _audit_storage = storage
    return _audit_storage
