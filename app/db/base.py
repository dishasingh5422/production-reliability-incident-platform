from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import Settings, get_settings


class Base(DeclarativeBase):
    pass


def build_engine(settings: Settings | None = None) -> Engine:
    resolved = settings or get_settings()
    connect_args = (
        {"check_same_thread": False} if resolved.database_url.startswith("sqlite") else {}
    )
    return create_engine(
        resolved.database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )


engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
