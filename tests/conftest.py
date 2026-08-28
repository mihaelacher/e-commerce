import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_server}/ecommerce_test",
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