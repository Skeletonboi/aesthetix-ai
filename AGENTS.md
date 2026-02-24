# AGENTS.md

## Cursor Cloud specific instructions

### Services overview

| Service | Port | How to start |
|---------|------|-------------|
| PostgreSQL | 5432 | `sudo service postgresql start` |
| Redis | 6379 | `sudo service redis-server start` |
| API (FastAPI) | 8000 | `cd backend && fastapi dev src/main.py --port 8000 --host 0.0.0.0` |

The ML service (port 8001) requires an NVIDIA GPU and is **not** runnable in this environment. It is optional; the core API works without it.

### Running the API

Start PostgreSQL and Redis first, then launch the API dev server from `backend/`:

```
sudo service postgresql start && sudo service redis-server start
cd backend && fastapi dev src/main.py --port 8000 --host 0.0.0.0
```

The app creates tables on startup via `BaseModel.metadata.create_all` and loads seed data from `src/tests/seed_data.json`.

### Running tests

```
cd backend && python3 -m pytest src/tests/ -v
```

All 22 tests pass. Tests use ASGI transport (not HTTP), so the dev server does **not** need to be running for tests to pass. However, PostgreSQL and Redis **must** be running.

### Key gotchas discovered during setup

- **`SESSION_SECRET_KEY`**: `main.py` references `Config.SESSION_SECRET_KEY` but the field was missing from the `Settings` class in `config.py`. It was added as a required `str` field.
- **`exercise_tags` table default**: The `exercise_tags` association table had `server_default="sa.text."` on the `eid` column, which is invalid for UUID type. This was removed since it's a foreign key column.
- **Seed data `account_creation_type`**: The `UserCreate` schema requires `account_creation_type` but the seed data JSON was missing it. It was added as `"CUSTOM"`.
- **pytest-asyncio compatibility**: The pinned `pytest-asyncio==0.21.1` is incompatible with `pytest==8.3.5`. Upgrade to `pytest-asyncio>=0.23`. A `pytest.ini` was added with `asyncio_mode = auto` and `asyncio_default_test_loop_scope = session` to prevent event loop lifecycle issues with the module-level SQLAlchemy async engine.
- **Environment file**: The API requires `backend/.env` with all settings from `src/config.py`. Placeholder values work for API-only development (LLM/Exa/YT keys are only needed by the ML service).

### Database

PostgreSQL with user `aesthetix` / password `aesthetix123`, database `aesthetix_db`. Connection string in `.env`:
```
DATABASE_URL=postgresql+asyncpg://aesthetix:aesthetix123@localhost:5432/aesthetix_db
```

### No linter configured

The codebase does not include a linter configuration (no ruff, flake8, pylint, or mypy config). Static analysis is not part of the current workflow.
