# Lab Management System

A web-based lab session tracking system for university computer labs. Built as a rapid prototype to prove the core workflow: **Student → Activity → Session → PC → Software → Duration**.

## Architecture

```text
                    ┌─────────────────────┐
                    │   Raspberry Pi 5    │
                    │                     │
                    │ Nginx               │
                    │ FastAPI             │
                    │ PostgreSQL          │
                    │ Web UI (HTMX)       │
                    └──────────┬──────────┘
                               │
                         Gigabit LAN
                               │
          ┌────────────────────┼────────────────────┐
          ↓                    ↓                    ↓
       PC-01                 PC-02                PC-40
       Browser              Browser              Browser
```

- **Backend**: FastAPI + SQLAlchemy (async) + PostgreSQL
- **Frontend**: Jinja2 + HTMX
- **Auth**: JWT-based (Student / Faculty / Admin roles)
- **Deployment**: Docker Compose + Nginx

## Quick Start

```bash
# Clone
git clone https://github.com/VishwatejaPalli/lab-management.git
cd lab-management

# Start PostgreSQL
docker compose up -d

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create tables and seed data
python3 -m app.seed

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open **http://localhost:8000**

## Default Credentials

| Role    | Username      | Password     |
|---------|---------------|--------------|
| Admin   | `admin`       | `admin123`   |
| Faculty | `faculty01`   | `faculty123` |
| Student | `22EC001`-`005` | `student123` |

## Session Workflow

```text
Login → Select PC → Select Activity → Select Experiment/Project/Research → START
                                                                            ↓
                                                              Session Timer Running
                                                                            ↓
                                                    Select Software Used → STOP
```

## Database Schema

```text
Users ──────┐
             ├── Sessions ──── SessionSoftware ──── Software
Computers ──┤
             ├── ActivityTypes
Courses ────┤
             ├── Experiments
Projects ───┘
Research
```

## Project Structure

```
lab-management/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py             # Settings (from .env)
│   ├── database.py           # SQLAlchemy async engine
│   ├── seed.py               # Database seeder
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic schemas
│   ├── routers/              # API route handlers
│   ├── services/             # Business logic
│   ├── templates/            # Jinja2 HTML templates
│   └── static/               # CSS + JS
├── docker-compose.yml        # PostgreSQL
├── nginx/                    # Nginx reverse proxy config
├── requirements.txt
└── .env
```

## License

MIT
