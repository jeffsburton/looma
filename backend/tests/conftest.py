import os
# Ensure email sending is emulated during tests before the app (and settings) are imported
os.environ.setdefault("EMAIL_BACKEND", "memory")

import asyncio
import pytest
import pytest_asyncio
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from main import app
from app.db import Base
from app.db.session import get_db


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db_url(tmp_path_factory) -> str:
    db_dir: Path = tmp_path_factory.mktemp("data")
    return f"sqlite+aiosqlite:///{db_dir / 'test.db'}"


@pytest_asyncio.fixture(scope="session")
async def engine(db_url: str) -> AsyncEngine:
    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest.fixture(scope="session")
def async_session_maker(engine: AsyncEngine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session(async_session_maker) -> AsyncSession:
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture(autouse=True, scope="session")
def override_dependency(async_session_maker):
    async def override_get_db():
        async with async_session_maker() as session:
            try:
                yield session
            finally:
                await session.rollback()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac