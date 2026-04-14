from pathlib import Path

APP_NAME = "Email Inbox Dashboard"
DEBUG = True

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

POSTGRES_HOST = "127.0.0.1"
POSTGRES_PORT = 5432
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
POSTGRES_DATABASE = "email_inbox"
POSTGRES_ADMIN_DATABASE = "postgres"
POSTGRES_TEST_DATABASE = "email_inbox_test"

POSTGRES_IMAGE = "postgres:16-alpine"
POSTGRES_CONTAINER_NAME = "email-inbox-postgres"
POSTGRES_VOLUME_NAME = "email-inbox-postgres-data"


def build_database_url(database_name: str) -> str:
    return (
        f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{database_name}"
    )


DATABASE_URL = build_database_url(POSTGRES_DATABASE)
TEST_DATABASE_URL = build_database_url(POSTGRES_TEST_DATABASE)
