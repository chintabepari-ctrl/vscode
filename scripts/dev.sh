#!/usr/bin/env bash
set -e

pip install -r requirements.txt
python -m app.migrate

pkill -f "uvicorn app.main:app" || true

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
