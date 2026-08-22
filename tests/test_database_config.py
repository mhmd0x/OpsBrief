import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.database import resolve_database_url


def run_fresh_database_import(
    environment: str,
    database_url: str | None = None,
) -> subprocess.CompletedProcess[str]:
    environment_variables = os.environ.copy()
    environment_variables["APP_ENV"] = environment
    environment_variables["PYTHON_DOTENV_DISABLED"] = "true"
    environment_variables["PYTHONPATH"] = str(
        Path(__file__).parents[1]
    )

    if database_url is None:
        environment_variables.pop("DATABASE_URL", None)
    else:
        environment_variables["DATABASE_URL"] = database_url

    return subprocess.run(
        [sys.executable, "-c", "import app.database"],
        capture_output=True,
        text=True,
        env=environment_variables,
        check=False,
    )


def test_local_environment_uses_sqlite_fallback() -> None:
    assert (
        resolve_database_url("local", None)
        == "sqlite:///./opsbrief.db"
    )


def test_test_environment_uses_sqlite_fallback() -> None:
    assert (
        resolve_database_url("test", None)
        == "sqlite:///./opsbrief.db"
    )


def test_local_environment_accepts_explicit_database_url() -> None:
    database_url = "postgresql+psycopg://user:password@localhost/db"

    assert resolve_database_url("local", database_url) == database_url


def test_production_requires_database_url() -> None:
    with pytest.raises(
        RuntimeError,
        match="DATABASE_URL is required when APP_ENV=production",
    ):
        resolve_database_url("production", None)


def test_production_rejects_sqlite_database_url() -> None:
    with pytest.raises(
        RuntimeError,
        match="DATABASE_URL must not use SQLite when APP_ENV=production",
    ):
        resolve_database_url("production", "sqlite:///./opsbrief.db")


def test_production_startup_fails_without_database_url() -> None:
    result = run_fresh_database_import("production")

    assert result.returncode != 0
    assert (
        "DATABASE_URL is required when APP_ENV=production"
        in result.stderr
    )


def test_production_startup_fails_with_sqlite_database_url() -> None:
    result = run_fresh_database_import(
        "production",
        "sqlite:///./opsbrief.db",
    )

    assert result.returncode != 0
    assert (
        "DATABASE_URL must not use SQLite when APP_ENV=production"
        in result.stderr
    )


def test_production_accepts_non_sqlite_database_url() -> None:
    database_url = "postgresql+psycopg://user:password@database/db"

    assert (
        resolve_database_url("production", database_url)
        == database_url
    )


def test_unknown_environment_is_rejected() -> None:
    with pytest.raises(
        RuntimeError,
        match="APP_ENV must be one of: local, test, production",
    ):
        resolve_database_url("staging", None)
