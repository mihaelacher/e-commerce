from collections.abc import AsyncGenerator, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.connection_url,
    pool_pre_ping=True,
    connect_args={
        "options": f"-c statement_timeout={settings.database_statement_timeout_ms}",
    },
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


async_engine = create_async_engine(
    settings.async_connection_url,
    pool_pre_ping=True,
    connect_args={
        "server_settings": {
            "statement_timeout": str(
                settings.database_statement_timeout_ms
            ),
        },
    },
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        yield db      


@contextmanager
def transaction(db: Session) -> Generator[Session, None, None]:
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise