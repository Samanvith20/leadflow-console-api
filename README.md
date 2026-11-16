# Leadflow backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

From the repository root, start PostgreSQL:

```bash
docker compose up -d postgres
```

Then, from `backend/`, apply migrations and start the API:

```bash
.venv/bin/alembic upgrade head
.venv/bin/fastapi dev app/main.py
```

Health check: [http://localhost:8000/health](http://localhost:8000/health)
