"""Pytest fixtures for test configuration."""

import asyncio
from typing import AsyncGenerator, Generator
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.config import Settings, get_settings
from app.database import get_async_session
from app.main import app
from app.dependencies import get_current_tenant

# Test database URL (use SQLite for simplicity in tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Test tenant UUIDs
TENANT_A_ID = UUID("11111111-1111-1111-1111-111111111111")
TENANT_B_ID = UUID("22222222-2222-2222-2222-222222222222")

# Test API keys
TENANT_A_API_KEY = "tenant-a-test-key"
TENANT_B_API_KEY = "tenant-b-test-key"
INVALID_API_KEY = "invalid-key"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Override settings for testing."""
    return Settings(
        database_url=TEST_DATABASE_URL,
        redis_url="redis://localhost:6379",
        environment="test",
        debug=False,
    )


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_maker = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with overridden dependencies."""

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def tenant_a_headers() -> dict:
    """Headers for Tenant A requests."""
    return {"X-API-KEY": TENANT_A_API_KEY}


@pytest.fixture
def tenant_b_headers() -> dict:
    """Headers for Tenant B requests."""
    return {"X-API-KEY": TENANT_B_API_KEY}


@pytest.fixture
def invalid_headers() -> dict:
    """Headers with invalid API key."""
    return {"X-API-KEY": INVALID_API_KEY}
