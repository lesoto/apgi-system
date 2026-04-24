"""
Batch Database Operations

Utility functions for efficient bulk database operations including
bulk inserts, updates, and deletes with proper error handling and transaction management.
"""

import logging
from typing import Any, Dict, List, Optional, Sequence, Type, TypeVar

from sqlalchemy import insert, select, update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.database.models import Base

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Base)


class BatchOperationError(Exception):
    """Base exception for batch operation errors."""

    pass


class BatchInsertError(BatchOperationError):
    """Exception raised when batch insert fails."""

    pass


class BatchUpdateError(BatchOperationError):
    """Exception raised when batch update fails."""

    pass


class BatchDeleteError(BatchOperationError):
    """Exception raised when batch delete fails."""

    pass


async def bulk_insert(
    session: AsyncSession,
    model: Type[T],
    records: List[Dict[str, Any]],
    batch_size: int = 1000,
    on_conflict: Optional[str] = None,
) -> int:
    """
    Perform bulk insert of records with optional conflict handling.

    Args:
        session: Async database session
        model: SQLAlchemy model class
        records: List of dictionaries representing records to insert
        batch_size: Number of records to insert per batch
        on_conflict: Conflict resolution strategy (PostgreSQL-specific)
                     Options: 'do_nothing', 'do_update', 'ignore'

    Returns:
        Number of records inserted

    Raises:
        BatchInsertError: If insert operation fails
    """
    if not records:
        logger.warning("bulk_insert called with empty records list")
        return 0

    total_inserted = 0

    try:
        # Process in batches to avoid memory issues
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]

            if on_conflict == "do_nothing" or on_conflict == "ignore":
                # Use PostgreSQL ON CONFLICT DO NOTHING
                insert_stmt = pg_insert(model).values(batch).on_conflict_do_nothing()
            elif on_conflict == "do_update":
                # Use PostgreSQL ON CONFLICT DO UPDATE
                insert_stmt = (
                    pg_insert(model)
                    .values(batch)
                    .on_conflict_do_update(
                        index_elements=[model.__table__.primary_key.columns.values()[0].name],
                        set_={k: k for k in batch[0].keys()},
                    )
                )
            else:
                # Standard bulk insert
                insert_stmt = insert(model).values(batch)  # type: ignore[assignment]

            result = await session.execute(insert_stmt)
            total_inserted += result.rowcount  # type: ignore[attr-defined]

            logger.debug(f"Inserted batch {i // batch_size + 1}: {len(batch)} records")

        await session.commit()
        logger.info(f"Bulk insert completed: {total_inserted} records inserted")
        return total_inserted

    except Exception as e:
        await session.rollback()
        logger.error(f"Bulk insert failed: {e}")
        raise BatchInsertError(f"Bulk insert failed for {model.__name__}: {e}") from e


async def bulk_update(
    session: AsyncSession,
    model: Type[T],
    filter_column: str,
    filter_values: Sequence[Any],
    update_data: Dict[str, Any],
    batch_size: int = 1000,
) -> int:
    """
    Perform bulk update of records matching filter criteria.

    Args:
        session: Async database session
        model: SQLAlchemy model class
        filter_column: Column name to filter on
        filter_values: Values to match in filter_column
        update_data: Dictionary of column names and values to update
        batch_size: Number of records to update per batch

    Returns:
        Number of records updated

    Raises:
        BatchUpdateError: If update operation fails
    """
    if not filter_values:
        logger.warning("bulk_update called with empty filter_values")
        return 0

    total_updated = 0

    try:
        # Process in batches
        for i in range(0, len(filter_values), batch_size):
            batch_values = filter_values[i : i + batch_size]

            stmt = (
                update(model)
                .where(getattr(model, filter_column).in_(batch_values))
                .values(**update_data)
            )

            result = await session.execute(stmt)
            total_updated += result.rowcount  # type: ignore[attr-defined]

            logger.debug(f"Updated batch {i // batch_size + 1}: {len(batch_values)} records")

        await session.commit()
        logger.info(f"Bulk update completed: {total_updated} records updated")
        return total_updated

    except Exception as e:
        await session.rollback()
        logger.error(f"Bulk update failed: {e}")
        raise BatchUpdateError(f"Bulk update failed for {model.__name__}: {e}") from e


async def bulk_delete(
    session: AsyncSession,
    model: Type[T],
    filter_column: str,
    filter_values: Sequence[Any],
    batch_size: int = 1000,
    cascade: bool = False,
) -> int:
    """
    Perform bulk delete of records matching filter criteria.

    Args:
        session: Async database session
        model: SQLAlchemy model class
        filter_column: Column name to filter on
        filter_values: Values to match in filter_column
        batch_size: Number of records to delete per batch
        cascade: Whether to cascade delete related records

    Returns:
        Number of records deleted

    Raises:
        BatchDeleteError: If delete operation fails
    """
    if not filter_values:
        logger.warning("bulk_delete called with empty filter_values")
        return 0

    total_deleted = 0

    try:
        # Process in batches
        for i in range(0, len(filter_values), batch_size):
            batch_values = filter_values[i : i + batch_size]

            stmt = delete(model).where(getattr(model, filter_column).in_(batch_values))

            result = await session.execute(stmt)
            total_deleted += result.rowcount  # type: ignore[attr-defined]

            logger.debug(f"Deleted batch {i // batch_size + 1}: {len(batch_values)} records")

        await session.commit()
        logger.info(f"Bulk delete completed: {total_deleted} records deleted")
        return total_deleted

    except Exception as e:
        await session.rollback()
        logger.error(f"Bulk delete failed: {e}")
        raise BatchDeleteError(f"Bulk delete failed for {model.__name__}: {e}") from e


async def bulk_upsert(
    session: AsyncSession,
    model: Type[T],
    records: List[Dict[str, Any]],
    unique_columns: List[str],
    batch_size: int = 1000,
) -> int:
    """
    Perform bulk upsert (insert or update) of records.

    Args:
        session: Async database session
        model: SQLAlchemy model class
        records: List of dictionaries representing records to upsert
        unique_columns: Columns that define uniqueness for upsert
        batch_size: Number of records to upsert per batch

    Returns:
        Number of records upserted

    Raises:
        BatchInsertError: If upsert operation fails
    """
    if not records:
        logger.warning("bulk_upsert called with empty records list")
        return 0

    total_upserted = 0

    try:
        # Process in batches
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]

            # Use PostgreSQL ON CONFLICT DO UPDATE for upsert
            stmt = (
                pg_insert(model)
                .values(batch)
                .on_conflict_do_update(
                    index_elements=unique_columns,
                    set_={k: getattr(pg_insert(model).excluded, k) for k in batch[0].keys()},
                )
            )

            result = await session.execute(stmt)
            total_upserted += result.rowcount  # type: ignore[attr-defined]

            logger.debug(f"Upserted batch {i // batch_size + 1}: {len(batch)} records")

        await session.commit()
        logger.info(f"Bulk upsert completed: {total_upserted} records upserted")
        return total_upserted

    except Exception as e:
        await session.rollback()
        logger.error(f"Bulk upsert failed: {e}")
        raise BatchInsertError(f"Bulk upsert failed for {model.__name__}: {e}") from e


async def bulk_fetch(
    session: AsyncSession,
    model: Type[T],
    filter_column: str,
    filter_values: Sequence[Any],
    batch_size: int = 1000,
) -> List[T]:
    """
    Perform bulk fetch of records matching filter criteria.

    Args:
        session: Async database session
        model: SQLAlchemy model class
        filter_column: Column name to filter on
        filter_values: Values to match in filter_column
        batch_size: Number of records to fetch per batch

    Returns:
        List of fetched model instances

    Raises:
        BatchOperationError: If fetch operation fails
    """
    if not filter_values:
        logger.warning("bulk_fetch called with empty filter_values")
        return []

    all_records: List[T] = []

    try:
        # Process in batches
        for i in range(0, len(filter_values), batch_size):
            batch_values = filter_values[i : i + batch_size]

            stmt = select(model).where(getattr(model, filter_column).in_(batch_values))

            result = await session.execute(stmt)
            records = result.scalars().all()
            all_records.extend(records)

            logger.debug(f"Fetched batch {i // batch_size + 1}: {len(records)} records")

        logger.info(f"Bulk fetch completed: {len(all_records)} records fetched")
        return all_records

    except Exception as e:
        logger.error(f"Bulk fetch failed: {e}")
        raise BatchOperationError(f"Bulk fetch failed for {model.__name__}: {e}") from e


async def bulk_session_data_insert(
    session: AsyncSession,
    session_id: str,
    time_series_data: List[Dict[str, Any]],
    batch_size: int = 5000,
) -> int:
    """
    Optimized bulk insert for session time-series data.

    Args:
        session: Async database session
        session_id: Session identifier
        time_series_data: List of time-series data points
        batch_size: Number of records to insert per batch

    Returns:
        Number of records inserted

    Raises:
        BatchInsertError: If insert operation fails
    """
    if not time_series_data:
        logger.warning("bulk_session_data_insert called with empty data")
        return 0

    # Prepend session_id to all records
    records = [{"session_id": session_id, **data} for data in time_series_data]

    from api.database.models import SessionData

    return await bulk_insert(
        session=session,
        model=SessionData,
        records=records,
        batch_size=batch_size,
        on_conflict="ignore",
    )


async def bulk_task_update(
    session: AsyncSession,
    task_ids: Sequence[str],
    status: Optional[str] = None,
    progress: Optional[int] = None,
    result_data: Optional[Dict[str, Any]] = None,
    batch_size: int = 1000,
) -> int:
    """
    Bulk update task status and progress.

    Args:
        session: Async database session
        task_ids: List of task IDs to update
        status: New status value (optional)
        progress: New progress value (optional)
        result_data: Result data to update (optional)
        batch_size: Number of records to update per batch

    Returns:
        Number of records updated

    Raises:
        BatchUpdateError: If update operation fails
    """
    update_data: Dict[str, Any] = {}
    if status is not None:
        update_data["status"] = status
    if progress is not None:
        update_data["progress"] = progress
    if result_data is not None:
        update_data["result_data"] = result_data

    if not update_data:
        logger.warning("bulk_task_update called with no update data")
        return 0

    from api.database.models import Task

    return await bulk_update(
        session=session,
        model=Task,
        filter_column="task_id",
        filter_values=task_ids,
        update_data=update_data,
        batch_size=batch_size,
    )
