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

## Authentication API

All authentication routes use the `/api/v1/auth` prefix. Successful registration, login, and
password change set an opaque HTTP-only `leadflow_session` cookie; the raw session value is never
returned in JSON or stored in PostgreSQL.

| Method | Route | Purpose |
| --- | --- | --- |
| POST | `/register` | Create a workspace and its first Manager. |
| POST | `/login` | Start a browser session. |
| POST | `/logout` | Revoke the current browser session. |
| GET | `/me` | Read the authenticated user and workspace. |
| POST | `/forgot-password` | Send a one-use reset link without exposing account existence. |
| POST | `/reset-password` | Reset a password and revoke every old session. |
| POST | `/verify-email` | Consume an email-verification token. |
| POST | `/change-password` | Change a known password and rotate the session. |

Set `RESEND_API_KEY` and `EMAIL_FROM` before production deployment. Development intentionally logs
email-link URLs for local testing; production refuses to start without email delivery and secure
session cookies.
