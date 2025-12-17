"""Unit tests for database utilities."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import close_db, get_db, init_db


class TestGetDb:
    """Tests for get_db dependency function."""

    async def test_get_db_yields_session(self):
        """Test that get_db yields a database session."""
        # Mock the AsyncSessionLocal
        with patch("app.database.AsyncSessionLocal") as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.commit = AsyncMock()
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()

            # Make AsyncSessionLocal() return a context manager
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None

            # Call get_db
            gen = get_db()
            session = await gen.__anext__()

            assert session == mock_session

            # Clean up the generator
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

    async def test_get_db_commits_on_success(self):
        """Test that get_db commits the session on success."""
        with patch("app.database.AsyncSessionLocal") as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.commit = AsyncMock()
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()

            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None

            # Use get_db as context manager
            gen = get_db()
            await gen.__anext__()

            # Simulate successful completion
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

            # Should have called commit
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    async def test_get_db_rolls_back_on_exception(self):
        """Test that get_db rolls back the session on exception."""
        with patch("app.database.AsyncSessionLocal") as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.commit = AsyncMock(side_effect=Exception("DB Error"))
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()

            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None

            gen = get_db()
            await gen.__anext__()

            # Simulate exception during commit
            with pytest.raises(Exception, match="DB Error"):
                try:
                    await gen.__anext__()
                except StopAsyncIteration:
                    pass

            # Should have called rollback
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()


class TestInitDb:
    """Tests for init_db function."""

    async def test_init_db_creates_tables(self):
        """Test that init_db creates all tables."""
        with patch("app.database.engine") as mock_engine:
            mock_conn = AsyncMock()
            mock_conn.run_sync = AsyncMock()

            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_engine.begin.return_value.__aexit__.return_value = None

            await init_db()

            # Should call run_sync to create tables
            mock_conn.run_sync.assert_called_once()

    async def test_init_db_imports_models(self):
        """Test that init_db imports Base from models."""
        # This test verifies that the import happens
        with patch("app.database.engine") as mock_engine:
            mock_conn = AsyncMock()
            mock_conn.run_sync = AsyncMock()

            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_engine.begin.return_value.__aexit__.return_value = None

            # Should not raise ImportError
            await init_db()


class TestCloseDb:
    """Tests for close_db function."""

    async def test_close_db_disposes_engine(self):
        """Test that close_db disposes the engine."""
        with patch("app.database.engine") as mock_engine:
            mock_engine.dispose = AsyncMock()

            await close_db()

            mock_engine.dispose.assert_called_once()


class TestDatabaseConfiguration:
    """Tests for database configuration."""

    def test_engine_is_created(self):
        """Test that database engine is created on module import."""
        from app.database import engine

        assert engine is not None

    def test_async_session_local_is_created(self):
        """Test that AsyncSessionLocal is created on module import."""
        from app.database import AsyncSessionLocal

        assert AsyncSessionLocal is not None

    def test_engine_configuration(self):
        """Test that engine is configured with correct settings."""
        from app.database import engine

        # Check that engine has expected attributes
        assert hasattr(engine, "url")
        assert hasattr(engine, "pool")

    def test_async_session_local_configuration(self):
        """Test that AsyncSessionLocal is configured correctly."""
        from app.database import AsyncSessionLocal

        # Check that it's callable (factory)
        assert callable(AsyncSessionLocal)
