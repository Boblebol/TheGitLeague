# 🛠️ Development Guide

This guide helps you set up a local development environment for **The Git League**.

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Environment Variables](#environment-variables)
- [Database Management](#database-management)
- [Running Tests](#running-tests)
- [Debugging](#debugging)
- [Common Tasks](#common-tasks)
- [Performance Profiling](#performance-profiling)
- [Troubleshooting](#troubleshooting)

---

## ✅ Prerequisites

### Required

- **Docker** ≥ 24.0
- **Docker Compose** ≥ 2.20
- **Node.js** ≥ 20.x (for local frontend dev)
- **Python** ≥ 3.11 (for local backend dev)
- **Git** ≥ 2.30
- **pnpm** or **npm** (pnpm recommended)

### Optional (for advanced development)

- **PostgreSQL client** (`psql`) for database inspection
- **Redis client** (`redis-cli`) for queue debugging
- **Rust** ≥ 1.70 (if building high-performance ingestion worker)

### Installation (macOS)

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install docker docker-compose node@20 python@3.11 git postgresql redis
brew install pnpm

# Install Rust (optional)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Installation (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install pnpm
npm install -g pnpm

# Install PostgreSQL client
sudo apt install -y postgresql-client

# Install Redis client
sudo apt install -y redis-tools
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Boblebol/TheGitLeague.git
cd TheGitLeague
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env
```

**Minimal `.env` for development:**

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=thegitleague_dev
POSTGRES_USER=gitleague
POSTGRES_PASSWORD=dev_password_change_in_prod

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Backend
SECRET_KEY=your-secret-key-min-32-chars-change-in-production
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Email (magic links) — use Mailhog for development
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=noreply@thegitleague.local

# Auth
ACCESS_TOKEN_EXPIRE_MINUTES=15
MAGIC_LINK_EXPIRE_MINUTES=15

# Workers
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### 3. Start Infrastructure (Docker Compose)

**Option A: Full stack (recommended for quick start)**

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Backend API (port 8000)
- Frontend (port 3000)
- Celery worker
- Mailhog (email testing, port 8025)

Access:
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- Mailhog: http://localhost:8025

**Option B: Infrastructure only (for local development)**

```bash
docker-compose up -d postgres redis mailhog
```

Then run frontend/backend locally (see below).

### 4. Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Optional: Seed demo data
docker-compose exec backend python scripts/seed_demo_data.py
```

### 5. Verify Installation

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000
```

---

## 📁 Project Structure

```
TheGitLeague/
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # App Router pages
│   │   │   ├── layout.tsx     # Root layout
│   │   │   ├── page.tsx       # Home page
│   │   │   ├── leaderboard/   # Leaderboard pages
│   │   │   ├── players/       # Player profile pages
│   │   │   ├── fantasy/       # Fantasy league pages
│   │   │   └── settings/      # Commissioner settings
│   │   ├── components/        # React components
│   │   │   ├── ui/           # shadcn/ui components
│   │   │   ├── leaderboard/  # Leaderboard components
│   │   │   ├── player/       # Player components
│   │   │   └── layout/       # Layout components
│   │   ├── lib/              # Utilities
│   │   │   ├── api/          # API client
│   │   │   ├── hooks/        # Custom hooks
│   │   │   └── utils/        # Helper functions
│   │   └── types/            # TypeScript types
│   ├── public/               # Static assets
│   ├── package.json
│   └── tsconfig.json
│
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   │   ├── v1/           # API v1 endpoints
│   │   │   │   ├── auth.py
│   │   │   │   ├── players.py
│   │   │   │   ├── seasons.py
│   │   │   │   ├── repos.py
│   │   │   │   └── fantasy.py
│   │   │   └── deps.py       # Dependencies (DB session, auth)
│   │   ├── core/              # Core business logic
│   │   │   ├── config.py     # Configuration
│   │   │   ├── security.py   # Auth & tokens
│   │   │   ├── league_engine.py  # Stats calculation
│   │   │   └── scoring.py    # NBA metrics
│   │   ├── models/            # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── commit.py
│   │   │   ├── season.py
│   │   │   └── fantasy.py
│   │   ├── schemas/           # Pydantic schemas (API DTOs)
│   │   │   ├── user.py
│   │   │   ├── player.py
│   │   │   ├── season.py
│   │   │   └── fantasy.py
│   │   ├── services/          # Business logic services
│   │   │   ├── user_service.py
│   │   │   ├── stats_service.py
│   │   │   ├── awards_service.py
│   │   │   └── fantasy_service.py
│   │   ├── workers/           # Celery tasks
│   │   │   ├── git_ingestion.py
│   │   │   ├── stats_recompute.py
│   │   │   └── awards.py
│   │   ├── db/                # Database utilities
│   │   │   ├── base.py       # SQLAlchemy base
│   │   │   └── session.py    # Session management
│   │   └── main.py            # FastAPI app entry point
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Backend tests
│   ├── scripts/               # Utility scripts
│   ├── requirements.txt
│   └── pyproject.toml
│
├── docker/                     # Docker configurations
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── Dockerfile.worker
│
├── docs/                       # Additional documentation
├── scripts/                    # Development scripts
│   ├── seed_demo_data.py
│   └── reset_db.sh
│
├── docker-compose.yml          # Development stack
├── docker-compose.prod.yml     # Production stack
├── docker-compose.test.yml     # Test stack
├── .env.example                # Environment template
├── .gitignore
├── LICENSE
├── README.md
├── CONTRIBUTING.md
├── DEVELOPMENT.md              # This file
├── ARCHITECTURE.md
└── API_SPEC.md
```

---

## 🔄 Development Workflow

### Frontend Development (Local)

```bash
cd frontend

# Install dependencies
pnpm install

# Start dev server (hot reload)
pnpm dev

# Access at http://localhost:3000
```

**Available commands:**

```bash
pnpm dev          # Start dev server
pnpm build        # Build for production
pnpm start        # Start production build
pnpm lint         # Run ESLint
pnpm type-check   # Run TypeScript check
pnpm test         # Run tests
pnpm test:watch   # Run tests in watch mode
pnpm format       # Format with Prettier
```

### Backend Development (Local)

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dev dependencies

# Start backend (hot reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access API docs at http://localhost:8000/docs
```

**Available commands:**

```bash
# Development
uvicorn app.main:app --reload

# Run linting
ruff check .
ruff format .

# Type checking
mypy app/

# Tests
pytest                      # All tests
pytest -v                   # Verbose
pytest tests/api/           # Specific directory
pytest -k "test_name"       # Specific test
pytest --cov=app            # With coverage

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
alembic history
```

### Worker Development

```bash
cd backend

# Start Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# With auto-reload (development)
watchmedo auto-restart --directory=./app --pattern=*.py --recursive -- \
  celery -A app.workers.celery_app worker --loglevel=info

# Monitor tasks (Flower)
celery -A app.workers.celery_app flower
# Access at http://localhost:5555
```

---

## 🔐 Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_DB` | Database name | `thegitleague_dev` |
| `POSTGRES_USER` | Database user | `gitleague` |
| `POSTGRES_PASSWORD` | Database password | `secure_password` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `SECRET_KEY` | JWT secret key | `min-32-chars-random` |
| `NEXT_PUBLIC_API_URL` | API base URL | `http://localhost:8000/api/v1` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3000"]` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiration | `15` |
| `MAGIC_LINK_EXPIRE_MINUTES` | Magic link expiration | `15` |

### Generating Secrets

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or use OpenSSL
openssl rand -base64 32
```

---

## 🗄️ Database Management

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "add_fantasy_tables"

# Review generated migration in alembic/versions/
# Edit if needed

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1

# View migration history
alembic history

# Show current version
alembic current
```

### Database Access

```bash
# Connect to PostgreSQL (Docker)
docker-compose exec postgres psql -U gitleague -d thegitleague_dev

# Connect to PostgreSQL (local)
psql -h localhost -U gitleague -d thegitleague_dev

# Common queries
\dt                    # List tables
\d+ users             # Describe table
SELECT * FROM users;  # Query data
```

### Reset Database

```bash
# Drop and recreate database
docker-compose down -v
docker-compose up -d postgres
docker-compose exec backend alembic upgrade head
docker-compose exec backend python scripts/seed_demo_data.py
```

### Backup & Restore

```bash
# Backup
docker-compose exec postgres pg_dump -U gitleague thegitleague_dev > backup.sql

# Restore
docker-compose exec -T postgres psql -U gitleague thegitleague_dev < backup.sql
```

---

## 🧪 Running Tests

### Frontend Tests

```bash
cd frontend

# Run all tests
pnpm test

# Watch mode
pnpm test:watch

# Coverage
pnpm test:coverage

# Specific test file
pnpm test PlayerCard.test.tsx
```

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Verbose output
pytest -v

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/api/test_players.py

# Specific test
pytest tests/api/test_players.py::test_get_player_stats

# Run in parallel (faster)
pytest -n auto
```

### Integration Tests

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Or manually
docker-compose -f docker-compose.test.yml up -d
docker-compose -f docker-compose.test.yml exec backend pytest
docker-compose -f docker-compose.test.yml down
```

### End-to-End Tests (Future)

```bash
# Install Playwright (when implemented)
cd frontend
pnpm exec playwright install

# Run E2E tests
pnpm test:e2e
```

---

## 🐛 Debugging

### Backend Debugging (VS Code)

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": false,
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      }
    }
  ]
}
```

### Frontend Debugging (VS Code)

```json
{
  "name": "Next.js",
  "type": "node",
  "request": "launch",
  "runtimeExecutable": "pnpm",
  "runtimeArgs": ["dev"],
  "cwd": "${workspaceFolder}/frontend",
  "port": 9229
}
```

### Logs

```bash
# Backend logs
docker-compose logs -f backend

# Worker logs
docker-compose logs -f worker

# All logs
docker-compose logs -f

# PostgreSQL logs
docker-compose logs -f postgres
```

### Redis Debugging

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Monitor commands
MONITOR

# View queue
LRANGE celery 0 -1

# Clear queue (development only!)
FLUSHDB
```

---

## 🔧 Common Tasks

### Add a New API Endpoint

1. **Define schema** in `backend/app/schemas/`
2. **Create service** in `backend/app/services/`
3. **Add route** in `backend/app/api/v1/`
4. **Write tests** in `backend/tests/api/`
5. **Update API_SPEC.md**

**Example:**

```python
# schemas/award.py
from pydantic import BaseModel

class AwardResponse(BaseModel):
    id: str
    type: str
    player_id: str
    season_id: str
    score: float

# api/v1/awards.py
from fastapi import APIRouter, Depends
from app.api.deps import get_db
from app.services import awards_service

router = APIRouter()

@router.get("/awards", response_model=list[AwardResponse])
async def list_awards(season_id: str, db = Depends(get_db)):
    return await awards_service.get_awards(db, season_id)

# Register in api/v1/__init__.py
from app.api.v1 import awards
api_router.include_router(awards.router, prefix="/awards", tags=["awards"])
```

### Add a New UI Component

1. **Create component** in `frontend/src/components/`
2. **Add types** in `frontend/src/types/`
3. **Write tests** in `__tests__/`
4. **Use in page** in `frontend/src/app/`

**Example:**

```tsx
// components/awards/AwardCard.tsx
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import type { Award } from '@/types/award';

interface AwardCardProps {
  award: Award;
}

export function AwardCard({ award }: AwardCardProps) {
  return (
    <Card>
      <CardHeader>{award.type}</CardHeader>
      <CardContent>
        <p>Score: {award.score}</p>
      </CardContent>
    </Card>
  );
}
```

### Add a Database Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "add_award_type_column"

# Edit migration if needed
nano alembic/versions/YYYY_MM_DD_HHMM_add_award_type_column.py

# Apply
alembic upgrade head
```

### Run a One-Off Task

```bash
# Via Celery
docker-compose exec worker python -c "
from app.workers.git_ingestion import sync_repo_task
sync_repo_task.apply_async(args=['repo-id-123'])
"

# Or directly
docker-compose exec backend python scripts/manual_sync.py --repo-id repo-id-123
```

---

## 📊 Performance Profiling

### Backend Profiling

```bash
# Install profiler
pip install py-spy

# Profile running process
py-spy record -o profile.svg -- python -m uvicorn app.main:app

# Profile specific endpoint
py-spy top --pid $(pgrep -f uvicorn)
```

### Database Query Analysis

```sql
-- Enable query logging
ALTER DATABASE thegitleague_dev SET log_statement = 'all';

-- View slow queries (> 1s)
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY total_time DESC
LIMIT 10;
```

### Frontend Performance

```bash
# Lighthouse CI
pnpm exec lighthouse http://localhost:3000 --view

# Bundle analysis
pnpm build
pnpm exec next-bundle-analyzer
```

---

## 🔧 Troubleshooting

### Frontend won't start

```bash
# Clear Next.js cache
rm -rf frontend/.next

# Reinstall dependencies
cd frontend
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

### Database connection errors

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
docker-compose exec postgres psql -U gitleague -d thegitleague_dev -c "SELECT 1;"

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

### Redis connection errors

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli PING
# Should return: PONG
```

### Port already in use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
API_PORT=8001 docker-compose up
```

### Worker not processing tasks

```bash
# Check worker logs
docker-compose logs -f worker

# Restart worker
docker-compose restart worker

# Check Redis queue
docker-compose exec redis redis-cli LLEN celery
```

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [TanStack Query](https://tanstack.com/query/latest)

---

## 💡 Tips

- Use `docker-compose logs -f <service>` to tail logs
- Run `alembic upgrade head` after pulling database changes
- Use `pnpm` instead of `npm` for faster installs
- Enable hot reload for rapid development
- Write tests as you code, not after
- Profile before optimizing

---

**Happy coding!** 🏀
