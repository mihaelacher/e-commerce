import os

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

DEFAULT_TEST_HOST = os.getenv("POSTGRES_HOST", "localhost")
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    (
        f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
        f"@{DEFAULT_TEST_HOST}:{settings.postgres_port}/ecommerce_test"
    ),
)
TEST_ASYNC_DATABASE_URL = TEST_DATABASE_URL.replace(
    "postgresql://",
    "postgresql+asyncpg://",
)


def ensure_test_database() -> None:
    test_url = make_url(TEST_DATABASE_URL)
    database_name = test_url.database

    if not database_name:
        raise ValueError("TEST_DATABASE_URL must include a database name")

    maintenance_url = test_url.set(database="postgres")
    maintenance_engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT")

    try:
        with maintenance_engine.connect() as connection:
            database_exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": database_name},
            ).scalar()

            if not database_exists:
                connection.exec_driver_sql(f'CREATE DATABASE "{database_name}"')
    finally:
        maintenance_engine.dispose()

    test_engine = create_engine(TEST_DATABASE_URL, isolation_level="AUTOCOMMIT")
    try:
        with test_engine.connect() as connection:
            connection.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
    finally:
        test_engine.dispose()


ensure_test_database()

engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(autouse=True)
def test_db():
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    def override_get_db():
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def db(test_db):
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def testing_session_factory():
    return TestingSessionLocal


async_engine = create_async_engine(
    TEST_ASYNC_DATABASE_URL,
    pool_pre_ping=True,
)

AsyncTestingSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture
async def async_db(test_db):
    async with AsyncTestingSessionLocal() as db:
        yield db
