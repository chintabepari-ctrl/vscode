import sys
from importlib import import_module
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def client():
    for module_name in [name for name in list(sys.modules) if name == "app" or name.startswith("app.")]:
        sys.modules.pop(module_name)

    import app.config as config
    config.DATABASE_URL = config.TEST_DATABASE_URL
    from app.migrate import ensure_database_exists, ensure_postgres_container

    ensure_postgres_container()
    ensure_database_exists(config.POSTGRES_TEST_DATABASE)

    admin_dsn = (
        f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}"
        f"@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_TEST_DATABASE}"
    )

    import_module("app.db")
    main = import_module("app.main")

    with TestClient(main.app) as test_client:
        with psycopg.connect(admin_dsn, autocommit=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE emails RESTART IDENTITY")
        yield test_client


def _payload(subject: str = "Hello", from_email: str = "sender@example.com"):
    return {
        "from": from_email,
        "to": "receiver@mydomain.com",
        "size": 12345,
        "headers": {
            "subject": subject,
            "date": "Mon, 01 Jan 2026 10:00:00 +0000",
            "message-id": "<abc@example.com>",
        },
        "raw_email": "Subject: Hello\n\nBody",
    }


def test_webhook_accepts_valid_payload(client):
    response = client.post("/webhook/email", json=_payload())

    assert response.status_code == 201
    assert response.json()["status"] == "stored"


def test_webhook_rejects_malformed_payload(client):
    response = client.post("/webhook/email", json={"from": "sender@example.com"})

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid request payload"


def test_inbox_empty_state(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "No emails yet" in response.text


def test_search_and_filters(client):
    client.post("/webhook/email", json=_payload(subject="Alpha"))
    client.post(
        "/webhook/email",
        json=_payload(subject="Bravo", from_email="other@example.com"),
    )

    response = client.get("/?q=bravo")
    assert "Bravo" in response.text
    assert "Alpha" not in response.text

    detail_response = client.get("/emails/1?return_to=/")
    assert detail_response.status_code == 200

    unread_response = client.get("/?status=unread")
    assert "Bravo" in unread_response.text
    assert "Alpha" not in unread_response.text

    read_response = client.get("/?status=read")
    assert "Alpha" in read_response.text


def test_detail_marks_email_as_read(client):
    client.post("/webhook/email", json=_payload())

    response = client.get("/emails/1?return_to=/")

    assert response.status_code == 200
    assert "Read" in response.text


def test_toggle_read_endpoint(client):
    client.post("/webhook/email", json=_payload())

    response = client.post("/emails/1/toggle-read", data={"next_url": "/"}, follow_redirects=False)

    assert response.status_code == 303
    inbox = client.get("/?status=read")
    assert "Hello" in inbox.text


def test_delete_endpoint(client):
    client.post("/webhook/email", json=_payload())

    response = client.post("/emails/1/delete", data={"next_url": "/"}, follow_redirects=False)

    assert response.status_code == 303
    inbox = client.get("/")
    assert "No emails yet" in inbox.text


def test_pagination(client):
    for index in range(12):
        client.post("/webhook/email", json=_payload(subject=f"Email {index}"))

    page_one = client.get("/?page=1&per_page=10")
    page_two = client.get("/?page=2&per_page=10")

    assert "Email 11" in page_one.text
    assert "Email 0" not in page_one.text
    assert "Email 0" in page_two.text
