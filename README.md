# Email Inbox Dashboard

A FastAPI application that receives Cloudflare Worker email webhooks, stores them in PostgreSQL, and displays them in an inbox-style admin dashboard.

## Features

- `POST /webhook/email` accepts valid email JSON directly
- PostgreSQL persistence using SQLAlchemy ORM
- Inbox dashboard with search, read/unread filter, unread badge, pagination, and empty state
- Email detail page with formatted headers, raw email viewer, copy button, and read tracking
- Delete and mark read/unread actions
- Seed-free startup with automatic PostgreSQL bootstrap
- Plain Python config in `app/config.py` with no `.env`
- Local PostgreSQL runs in Docker for development

## Project Structure

```text
app/
  main.py
  config.py
  db.py
  migrate.py
  models.py
  schemas.py
  utils.py
  routes/
  static/
  templates/
scripts/
requirements.txt
README.md
```

## Setup

1. Create and activate a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Start or restart the app with the project script.

```bash
./scripts/restart.sh
```

This script will:
- install missing Python dependencies
- run `python -m app.migrate`
- stop any old uvicorn process
- start `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

3. Open `http://127.0.0.1:8000/` for the dashboard.

## Webhook Payload

Expected JSON payload:

```json
{
  "from": "sender@example.com",
  "to": "receiver@mydomain.com",
  "size": 12345,
  "headers": {
    "subject": "Hello",
    "date": "Mon, 01 Jan 2026 10:00:00 +0000",
    "message-id": "<abc@example.com>"
  },
  "raw_email": "full raw EML content here"
}
```

Example request:

```bash
curl -X POST http://127.0.0.1:8000/webhook/email \
  -H "Content-Type: application/json" \
  -d '{
    "from": "sender@example.com",
    "to": "receiver@mydomain.com",
    "size": 12345,
    "headers": {
      "subject": "Hello",
      "date": "Mon, 01 Jan 2026 10:00:00 +0000",
      "message-id": "<abc@example.com>"
    },
    "raw_email": "Subject: Hello\n\nExample raw content"
  }'
```

## Notes

- The application uses only local constants in `app/config.py`.
- PostgreSQL is bootstrapped through `python -m app.migrate` before server start.
- The default local database runs in a Docker container named `email-inbox-postgres`.
- Emails are sorted newest first by storage time.
- Viewing an email marks it as read automatically.
- Malformed webhook payloads return a controlled `422` response.
