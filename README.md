# OpsBrief

OpsBrief is a maintenance decision-support API that turns asset and work-order data into operational briefs, risk signals, and recurring-issue insights.

## Problem

Maintenance supervisors often depend on fragmented information from CMMS records, spreadsheets, emails, messages, and shift handovers.

OpsBrief is being developed to surface what requires attention instead of only displaying raw maintenance data.

## Current Features

- Create, list, retrieve, update, and delete assets
- Validate incoming asset data
- Store assets in PostgreSQL
- Prevent duplicate asset tags
- Return clear `404 Not Found` and `409 Conflict` responses
- Manage database changes with Alembic migrations
- Run automated API tests using an isolated test database

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Check API health |
| `POST` | `/assets` | Create an asset |
| `GET` | `/assets` | List all assets |
| `GET` | `/assets/{asset_id}` | Retrieve an asset |
| `PATCH` | `/assets/{asset_id}` | Update an asset |
| `DELETE` | `/assets/{asset_id}` | Delete an asset |

Interactive API documentation is available at `/docs` while the application is running.

## Technology

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- Pytest
- Docker Compose

## Requirements

- Python 3.11 or newer
- Docker with Docker Compose
- Git

## Development Setup

Clone the repository and enter its directory:

```bash
git clone https://github.com/mhmd0x/OpsBrief.git
cd OpsBrief
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Linux or macOS:

```bash
source .venv/bin/activate
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the project and development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Create the local environment file:

```bash
cp .env.example .env
```

On Windows PowerShell, use:

```powershell
Copy-Item .env.example .env
```

Start PostgreSQL:

```bash
docker compose up -d
```

Confirm the database is healthy:

```bash
docker compose ps
```

Apply the database migrations:

```bash
python -m alembic upgrade head
```

Start the API:

```bash
python -m uvicorn app.main:app --reload
```

Open the interactive documentation at:

```text
http://127.0.0.1:8000/docs
```

## Running Tests

Run the complete test suite:

```bash
python -m pytest
```

The tests use a separate in-memory SQLite database and do not modify development data stored in PostgreSQL.

## Stopping the Development Database

Stop the PostgreSQL container:

```bash
docker compose down
```

Avoid using `docker compose down -v` unless you intentionally want to delete the local PostgreSQL data.

## Project Structure

```text
OpsBrief/
├── alembic/
│   └── versions/
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
├── tests/
│   ├── conftest.py
│   ├── test_assets.py
│   └── test_health.py
├── .env.example
├── .gitignore
├── alembic.ini
├── compose.yaml
├── LICENSE
├── pyproject.toml
└── README.md
```

## Planned Development

The next milestones are:

- Work-order management
- Overdue and due-today work-order detection
- High-attention work-order identification
- Recurring asset issue detection
- Daily Operations Brief API

## Status

Active early-stage development.