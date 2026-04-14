# AGENTS.md

## Project
This is a FastAPI email inbox dashboard project.

## Agent responsibilities
The agent must handle the local development workflow automatically without asking the user to do routine steps manually.

The agent should:
- install missing dependencies
- run database migration/bootstrap
- start the FastAPI app
- stop the old app process before starting a new one
- restart the app after code changes
- run tests
- verify the main routes
- inspect logs and fix errors

## Configuration rules
- Keep configuration in `app/config.py`
- Do not use `.env`
- Do not use `os.getenv`
- Do not use `python-dotenv`
- Do not add Authorization or webhook token logic unless explicitly requested

## Database rules
- Use PostgreSQL
- Database URL is stored in `app/config.py`
- Before starting the app, always ensure database bootstrap/migration has been run
- Missing tables must be created automatically
- Prefer simple bootstrap logic for missing tables
- If schema changes become more complex later, the agent may introduce Alembic only if explicitly requested

## Install
If dependencies are missing, run:
pip install -r requirements.txt

## Migration/bootstrap
Before starting the server, run:
python -m app.migrate

This must create any missing tables safely.

## Run
Default dev server command:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

## Stop/restart behavior
Before starting a new server:
1. detect whether uvicorn is already running on port 8000
2. stop the previous process cleanly
3. start the app again

## Verification
After start/restart:
1. verify GET / returns 200
2. verify POST /webhook/email works
3. verify database insert succeeds
4. run tests if present

## Typical verification commands
curl http://127.0.0.1:8000/
curl -X POST http://127.0.0.1:8000/webhook/email -H "Content-Type: application/json" -d '{"from":"sender@example.com","to":"receiver@example.com","size":123,"headers":{"subject":"Test"},"raw_email":"hello"}'
pytest -q

## Completion criteria
A task is only complete when:
- dependencies are installed
- migration/bootstrap ran successfully
- server is running
- routes respond correctly
- tests pass if present

## Editing rules
- prefer minimal and correct fixes
- keep code modular
- keep DB config in config.py
- keep migration/bootstrap simple and reliable
