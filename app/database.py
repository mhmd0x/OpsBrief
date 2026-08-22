import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


load_dotenv()


def resolve_database_url(
    environment: str,
    database_url: str | None,
) -> str:
    supported_environments = {"local", "test", "production"}
    normalized_environment = environment.strip().lower()

    if normalized_environment not in supported_environments:
        raise RuntimeError(
            "APP_ENV must be one of: local, test, production"
        )

    if normalized_environment == "production":
        if not database_url or not database_url.strip():
            raise RuntimeError(
                "DATABASE_URL is required when APP_ENV=production"
            )
        if database_url.lower().startswith("sqlite"):
            raise RuntimeError(
                "DATABASE_URL must not use SQLite when APP_ENV=production"
            )

    return database_url or "sqlite:///./opsbrief.db"


APP_ENV = os.getenv("APP_ENV", "local")
DATABASE_URL = resolve_database_url(
    APP_ENV,
    os.getenv("DATABASE_URL"),
)

connect_args = (
    {"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    database = SessionLocal()

    try:
        yield database
    finally:
        database.close()