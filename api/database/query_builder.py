"""
Safe query builder for standardized database operations.

Enforces parameterized queries and prevents SQL injection vulnerabilities.
All database queries should use this module instead of raw SQL.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class QueryBuilder:
    """
    Safe query builder for database operations.

    Enforces parameterized queries and prevents SQL injection.
    """

    @staticmethod
    def select_by_id(session: Session, model: Any, id_value: Any) -> Optional[Any]:
        """
        Select a record by ID using parameterized query.

        Args:
            session: Database session (sync only)
            model: SQLAlchemy model class
            id_value: ID value to search for

        Returns:
            Model instance or None
        """
        try:
            query = select(model).where(model.id == id_value)
            result = session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Query failed: %s", e)
            raise

    @staticmethod
    def select_by_filter(session: Session, model: Any, filters: Dict[str, Any]) -> List[Any]:
        """
        Select records using parameterized filters.

        Args:
            session: Database session (sync only)
            model: SQLAlchemy model class
            filters: Dictionary of column:value pairs

        Returns:
            List of model instances
        """
        try:
            conditions = []
            for column_name, value in filters.items():
                if hasattr(model, column_name):
                    conditions.append(getattr(model, column_name) == value)

            if not conditions:
                raise ValueError("No valid filters provided")

            query = select(model).where(and_(*conditions))
            result = session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Query failed: %s", e)
            raise

    @staticmethod
    def insert_record(session: Session, model: Any, data: Dict[str, Any]) -> Any:
        """
        Insert a record using parameterized query.

        Args:
            session: Database session (sync only)
            model: SQLAlchemy model class
            data: Dictionary of column:value pairs

        Returns:
            Inserted model instance
        """
        try:
            stmt = insert(model).values(**data)
            result = session.execute(stmt)
            session.commit()

            # Retrieve the inserted record
            inserted_id = (
                result.inserted_primary_key[0] if hasattr(result, "inserted_primary_key") else None
            )
            if inserted_id:
                return QueryBuilder.select_by_id(session, model, inserted_id)
            return None
        except Exception as e:
            session.rollback()
            logger.error("Insert failed: %s", e)
            raise

    @staticmethod
    def update_record(
        session: Session, model: Any, id_value: Any, data: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Update a record using parameterized query.

        Args:
            session: Database session (sync only)
            model: SQLAlchemy model class
            id_value: ID of record to update
            data: Dictionary of column:value pairs to update

        Returns:
            Updated model instance or None
        """
        try:
            stmt = update(model).where(model.id == id_value).values(**data)
            session.execute(stmt)
            session.commit()

            return QueryBuilder.select_by_id(session, model, id_value)
        except Exception as e:
            session.rollback()
            logger.error("Update failed: %s", e)
            raise

    @staticmethod
    def delete_record(session: Session, model: Any, id_value: Any) -> bool:
        """
        Delete a record using parameterized query.

        Args:
            session: Database session (sync only)
            model: SQLAlchemy model class
            id_value: ID of record to delete

        Returns:
            True if record was deleted
        """
        try:
            stmt = delete(model).where(model.id == id_value)
            result = session.execute(stmt)
            session.commit()

            return result.rowcount > 0 if hasattr(result, "rowcount") else False
        except Exception as e:
            session.rollback()
            logger.error("Delete failed: %s", e)
            raise

    @staticmethod
    def health_check(session: Session) -> bool:
        """
        Perform a safe health check query.

        Args:
            session: Database session (sync only)

        Returns:
            True if database is healthy
        """
        try:
            # Use literal_column for safe constant queries
            from sqlalchemy import literal_column

            query: Any = select(literal_column("1"))
            result = session.execute(query)
            return result.scalar() == 1
        except Exception as e:
            logger.error("Health check failed: %s", e)
            return False

    @staticmethod
    def execute_safe_raw_sql(
        session: Session, sql: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute raw SQL with parameterized values.

        IMPORTANT: Only use this when SQLAlchemy ORM cannot express the query.
        Always use named parameters (:param_name) in the SQL string.

        Args:
            session: Database session (sync only)
            sql: SQL query with named parameters
            params: Dictionary of parameter values

        Returns:
            Query result

        Example:
            result = execute_safe_raw_sql(
                session,
                "SELECT * FROM users WHERE email = :email",
                {"email": "user@example.com"}
            )
        """
        try:
            if params is None:
                params = {}

            query = text(sql)
            result = session.execute(query, params)
            return result
        except Exception as e:
            logger.error("Raw SQL execution failed: %s", e)
            raise


class AsyncQueryBuilder:
    """
    Async version of QueryBuilder for use with AsyncSession.
    """

    @staticmethod
    async def select_by_id(session: AsyncSession, model: Any, id_value: Any) -> Optional[Any]:
        """
        Async select a record by ID.

        Args:
            session: Async database session
            model: SQLAlchemy model class
            id_value: ID value to search for

        Returns:
            Model instance or None
        """
        try:
            query = select(model).where(model.id == id_value)
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Async query failed: %s", e)
            raise

    @staticmethod
    async def select_by_filter(
        session: AsyncSession, model: Any, filters: Dict[str, Any]
    ) -> List[Any]:
        """
        Async select records using parameterized filters.

        Args:
            session: Async database session
            model: SQLAlchemy model class
            filters: Dictionary of column:value pairs

        Returns:
            List of model instances
        """
        try:
            conditions = []
            for column_name, value in filters.items():
                if hasattr(model, column_name):
                    conditions.append(getattr(model, column_name) == value)

            if not conditions:
                raise ValueError("No valid filters provided")

            query = select(model).where(and_(*conditions))
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Async query failed: %s", e)
            raise

    @staticmethod
    async def health_check(session: AsyncSession) -> bool:
        """
        Perform a safe async health check query.

        Args:
            session: Async database session

        Returns:
            True if database is healthy
        """
        try:
            from sqlalchemy import literal_column

            query: Any = select(literal_column("1"))
            result = await session.execute(query)
            return result.scalar() == 1
        except Exception as e:
            logger.error("Async health check failed: %s", e)
            return False
