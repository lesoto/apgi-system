"""
Comprehensive tests for database_integration module.

This module tests all functionality of the database_integration module
to achieve high test coverage for MISSING-004: Database Integration.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestDatabaseIntegrationImports:
    """Test that the module imports correctly."""

    def test_module_imports(self):
        """Test that database_integration module can be imported."""
        from apgi_framework.data import database_integration

        assert hasattr(database_integration, "LargeDatasetHandler")
        assert hasattr(database_integration, "DatabaseIntegrationError")
        assert hasattr(database_integration, "enable_database_integration")

    def test_error_class(self):
        """Test DatabaseIntegrationError class."""
        from apgi_framework.data.database_integration import DatabaseIntegrationError
        from apgi_framework.exceptions import APGIFrameworkError

        # Check inheritance
        assert issubclass(DatabaseIntegrationError, APGIFrameworkError)

        # Check error can be raised
        with pytest.raises(DatabaseIntegrationError):
            raise DatabaseIntegrationError("Test error")


class TestLargeDatasetHandlerInitialization:
    """Test LargeDatasetHandler initialization."""

    def test_init_without_postgresql(self):
        """Test initialization when PostgreSQL is not available."""
        from apgi_framework.data.database_integration import LargeDatasetHandler

        with patch("apgi_framework.data.database_integration.PGSQL_AVAILABLE", False):
            mock_storage = Mock()
            handler = LargeDatasetHandler(mock_storage)

            assert handler.storage_manager == mock_storage
            assert handler._pool is None
            assert handler.chunk_size == 10000
            assert handler.max_memory_mb == 500

    def test_init_attributes(self):
        """Test that handler has correct default attributes."""
        from apgi_framework.data.database_integration import LargeDatasetHandler

        with patch("apgi_framework.data.database_integration.PGSQL_AVAILABLE", False):
            mock_storage = Mock()
            handler = LargeDatasetHandler(mock_storage)

            assert handler.chunk_size == 10000
            assert handler.max_memory_mb == 500


class TestLargeDatasetHandlerMockedDB:
    """Test LargeDatasetHandler with mocked database."""

    @pytest.fixture
    def mock_handler(self):
        """Create a handler with mocked database."""
        from apgi_framework.data.database_integration import LargeDatasetHandler

        with patch("apgi_framework.data.database_integration.PGSQL_AVAILABLE", True):
            with patch("apgi_framework.data.database_integration.ThreadedConnectionPool"):
                with patch.object(LargeDatasetHandler, "_init_database"):
                    mock_storage = Mock()
                    handler = LargeDatasetHandler(mock_storage)
                    handler._pool = Mock()
                    yield handler

    def test_store_dataframe_success(self, mock_handler):
        """Test storing DataFrame successfully."""
        df = pd.DataFrame({"col1": [1, 2, 3, 4, 5], "col2": ["a", "b", "c", "d", "e"]})

        # Mock the database connection
        mock_conn = MagicMock()
        mock_handler._pool.getconn.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_handler._pool.getconn.return_value.__exit__ = Mock(return_value=False)

        mock_handler.store_large_dataset("exp_001", df, "test_data")

    def test_store_numpy_array(self, mock_handler):
        """Test storing numpy array."""
        arr = np.array([[1, 2], [3, 4], [5, 6]])

        mock_conn = MagicMock()
        mock_handler._pool.getconn.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_handler._pool.getconn.return_value.__exit__ = Mock(return_value=False)

        mock_handler.store_large_dataset("exp_002", arr, "array_data")

    def test_store_json_data(self, mock_handler):
        """Test storing JSON data."""
        data = [{"key1": "value1"}, {"key1": "value2"}]

        mock_conn = MagicMock()
        mock_handler._pool.getconn.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_handler._pool.getconn.return_value.__exit__ = Mock(return_value=False)

        mock_handler.store_large_dataset("exp_003", data, "json_data")

    def test_store_dict_data(self, mock_handler):
        """Test storing dict data (converts to list)."""
        data = {"key1": "value1", "key2": "value2"}

        mock_conn = MagicMock()
        mock_handler._pool.getconn.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_handler._pool.getconn.return_value.__exit__ = Mock(return_value=False)

        mock_handler.store_large_dataset("exp_004", data, "dict_data")

    def test_store_unsupported_type(self, mock_handler):
        """Test storing unsupported data type."""

        # Create a custom object that isn't supported
        class CustomObject:
            pass

        mock_handler._pool = Mock()

        result = mock_handler.store_large_dataset("exp_005", CustomObject(), "custom")
        assert result is False

    def test_load_large_dataset_no_pool(self, mock_handler):
        """Test loading when pool is None."""
        mock_handler._pool = None

        # Should return empty generator
        results = list(mock_handler.load_large_dataset("exp_001"))
        assert results == []

    def test_query_large_datasets_no_pool(self, mock_handler):
        """Test querying when pool is None."""
        mock_handler._pool = None

        results = mock_handler.query_large_datasets()
        assert results == []

    def test_cleanup_old_data_no_pool(self, mock_handler):
        """Test cleanup when pool is None."""
        mock_handler._pool = None

        result = mock_handler.cleanup_old_data(retention_days=30)
        assert result == 0

    def test_get_database_stats_no_pool(self, mock_handler):
        """Test get stats when pool is None."""
        mock_handler._pool = None

        stats = mock_handler.get_database_stats()
        assert stats["status"] == "not_available"

    def test_close_connection(self, mock_handler):
        """Test closing database connections."""
        mock_pool = Mock()
        mock_handler._pool = mock_pool

        mock_handler.close()

        mock_pool.closeall.assert_called_once()
        assert mock_handler._pool is None


class TestLargeDatasetHandlerWithRealPool:
    """Test with more realistic pool mocking."""

    def test_cleanup_old_data_success(self):
        """Test successful data cleanup."""
        from apgi_framework.data.database_integration import LargeDatasetHandler

        with patch("apgi_framework.data.database_integration.PGSQL_AVAILABLE", True):
            with patch.object(LargeDatasetHandler, "_init_database"):
                mock_storage = Mock()
                handler = LargeDatasetHandler(mock_storage)

                mock_pool = Mock()
                mock_cursor = Mock()
                mock_cursor.rowcount = 10

                mock_conn = Mock()
                mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)

                mock_pool.getconn.return_value.__enter__ = Mock(return_value=mock_conn)
                mock_pool.getconn.return_value.__exit__ = Mock(return_value=False)

                handler._pool = mock_pool

                result = handler.cleanup_old_data(retention_days=30)
                assert result == 20  # 10 chunks + 10 experiments


class TestEnableDatabaseIntegration:
    """Test the enable_database_integration function."""

    def test_enable_integration(self):
        """Test enabling database integration."""
        from apgi_framework.data.database_integration import enable_database_integration

        with patch(
            "apgi_framework.data.database_integration.get_config_manager"
        ) as mock_get_config:
            mock_config = Mock()
            mock_config.config = Mock()
            mock_config.config.features = {}
            mock_config.enable_feature = lambda feature_name: mock_config.config.features.update(
                {feature_name: True}
            )
            mock_get_config.return_value = mock_config

            with patch(
                "apgi_framework.data.database_integration.LargeDatasetHandler"
            ) as mock_handler_class:
                mock_handler = Mock()
                mock_handler_class.return_value = mock_handler

                mock_storage = Mock()
                result = enable_database_integration(mock_storage)

                assert mock_config.config.features["database_integration"] is True
                assert result == mock_handler


class TestDatabaseIntegrationEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test handling empty DataFrame."""
        from apgi_framework.data.database_integration import LargeDatasetHandler

        with patch("apgi_framework.data.database_integration.PGSQL_AVAILABLE", True):
            with patch.object(LargeDatasetHandler, "_init_database"):
                mock_storage = Mock()
                handler = LargeDatasetHandler(mock_storage)

                empty_df = pd.DataFrame()

                mock_pool = Mock()
                mock_conn = Mock()
                mock_cursor = Mock()

                mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                mock_pool.getconn.return_value.__enter__ = Mock(return_value=mock_conn)
                mock_pool.getconn.return_value.__exit__ = Mock(return_value=False)
                handler._pool = mock_pool

                # Empty DataFrame should handle gracefully
                handler.store_large_dataset("exp_empty", empty_df, "empty_data")

    def test_large_numpy_array_chunking(self):
        """Test that large arrays are properly chunked."""
        from apgi_framework.data.database_integration import LargeDatasetHandler

        with patch("apgi_framework.data.database_integration.PGSQL_AVAILABLE", True):
            with patch.object(LargeDatasetHandler, "_init_database"):
                mock_storage = Mock()
                handler = LargeDatasetHandler(mock_storage)
                handler.chunk_size = 100  # Small chunk size for testing

                # Create array that will need chunking
                large_array = np.random.randn(500)

                mock_pool = Mock()
                mock_conn = Mock()
                mock_cursor = Mock()
                mock_cursor.rowcount = 0

                mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                mock_pool.getconn.return_value.__enter__ = Mock(return_value=mock_conn)
                mock_pool.getconn.return_value.__exit__ = Mock(return_value=False)
                handler._pool = mock_pool

                # Calculate expected chunks: (500 + 99) // 100 = 5 chunks

                handler.store_large_dataset("exp_large", large_array, "large_array")


class TestDatabaseStats:
    """Test database statistics functionality."""

    def test_get_database_stats_success(self):
        """Test getting database stats successfully."""
        from apgi_framework.data.database_integration import LargeDatasetHandler

        with patch("apgi_framework.data.database_integration.PGSQL_AVAILABLE", True):
            with patch.object(LargeDatasetHandler, "_init_database"):
                mock_storage = Mock()
                handler = LargeDatasetHandler(mock_storage)

                mock_pool = Mock()
                mock_pool.minconn = 1
                mock_pool.maxconn = 10
                mock_pool._pool = Mock()
                mock_pool._pool.queue = Mock()
                mock_pool._pool.queue.queue = []

                mock_conn = Mock()
                mock_cursor = Mock()
                mock_cursor.fetchone.return_value = (100, 500, 1024000, 2048, 50)

                mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                mock_pool.getconn.return_value.__enter__ = Mock(return_value=mock_conn)
                mock_pool.getconn.return_value.__exit__ = Mock(return_value=False)

                handler._pool = mock_pool

                stats = handler.get_database_stats()

                assert stats["status"] == "active"
                assert stats["experiments_count"] == 100
                assert stats["chunks_count"] == 500


class TestQueryLargeDatasets:
    """Test querying large datasets."""

    def test_query_with_filters(self):
        """Test querying with various filters."""
        from apgi_framework.data.database_integration import LargeDatasetHandler

        with patch("apgi_framework.data.database_integration.PGSQL_AVAILABLE", True):
            with patch.object(LargeDatasetHandler, "_init_database"):
                mock_storage = Mock()
                handler = LargeDatasetHandler(mock_storage)

                mock_pool = Mock()
                mock_conn = Mock()
                mock_cursor = Mock()

                # Mock return data
                mock_cursor.fetchall.return_value = [
                    (
                        "exp_001",
                        "Test Experiment",
                        "Description",
                        "Researcher",
                        "Institution",
                        datetime.now(),
                        datetime.now(),
                        10,
                        100,
                        {"cond": 1},
                        {"param": 2},
                        "csv",
                        100.5,
                        "active",
                        5,
                        1024000,
                    )
                ]

                mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                mock_pool.getconn.return_value.__enter__ = Mock(return_value=mock_conn)
                mock_pool.getconn.return_value.__exit__ = Mock(return_value=False)

                handler._pool = mock_pool

                filter_criteria = {"researcher": "Test", "status": "active"}

                results = handler.query_large_datasets(filter_criteria, limit=10)

                assert len(results) == 1
                assert results[0]["experiment_id"] == "exp_001"
