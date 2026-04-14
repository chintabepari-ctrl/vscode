import subprocess
import time

import psycopg
from sqlalchemy import create_engine

from app import models  # noqa: F401
from app.config import (
    DATABASE_URL,
    POSTGRES_ADMIN_DATABASE,
    POSTGRES_CONTAINER_NAME,
    POSTGRES_DATABASE,
    POSTGRES_HOST,
    POSTGRES_IMAGE,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
    POSTGRES_VOLUME_NAME,
)
from app.db import Base


def _run_command(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=check, text=True, capture_output=True)


def ensure_postgres_container() -> None:
    inspect = _run_command(["docker", "inspect", POSTGRES_CONTAINER_NAME], check=False)
    if inspect.returncode != 0:
        _run_command(
            [
                "docker",
                "run",
                "--detach",
                "--name",
                POSTGRES_CONTAINER_NAME,
                "--publish",
                f"{POSTGRES_PORT}:5432",
                "--env",
                f"POSTGRES_USER={POSTGRES_USER}",
                "--env",
                f"POSTGRES_PASSWORD={POSTGRES_PASSWORD}",
                "--env",
                f"POSTGRES_DB={POSTGRES_ADMIN_DATABASE}",
                "--volume",
                f"{POSTGRES_VOLUME_NAME}:/var/lib/postgresql/data",
                POSTGRES_IMAGE,
            ]
        )
    else:
        is_running = _run_command(
            ["docker", "inspect", "-f", "{{.State.Running}}", POSTGRES_CONTAINER_NAME]
        ).stdout.strip()
        if is_running != "true":
            _run_command(["docker", "start", POSTGRES_CONTAINER_NAME])

    for _ in range(30):
        ready = _run_command(
            [
                "docker",
                "exec",
                POSTGRES_CONTAINER_NAME,
                "pg_isready",
                "-U",
                POSTGRES_USER,
                "-d",
                POSTGRES_ADMIN_DATABASE,
            ],
            check=False,
        )
        if ready.returncode == 0:
            return
        time.sleep(1)

    raise RuntimeError("PostgreSQL container did not become ready in time.")


def ensure_database_exists(database_name: str) -> None:
    admin_dsn = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_ADMIN_DATABASE}"
    )
    with psycopg.connect(admin_dsn, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
            exists = cursor.fetchone() is not None
            if not exists:
                cursor.execute(f'CREATE DATABASE "{database_name}"')


def run_migrations() -> None:
    ensure_postgres_container()
    ensure_database_exists(POSTGRES_DATABASE)

    engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
    Base.metadata.create_all(bind=engine)
    engine.dispose()


if __name__ == "__main__":
    run_migrations()
    print("Database bootstrap completed successfully.")
