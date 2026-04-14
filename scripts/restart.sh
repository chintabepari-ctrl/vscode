#!/usr/bin/env bash
set -e

pip install -r requirements.txt
pkill -f "uvicorn app.main:app" || true
python -m app.migrate
setsid uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > server.log 2>&1 < /dev/null &
