#!/usr/bin/env bash
set -e

pip install -r requirements.txt
python -m app.migrate
pytest -q
