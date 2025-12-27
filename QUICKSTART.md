# 🚀 Quick Start Guide

Get The Git League running in under 5 minutes!

## Prerequisites

- Docker & Docker Compose
- Git

## Installation

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/Boblebol/TheGitLeague.git
cd TheGitLeague

# Copy environment file
cp .env.example .env
```

### 2. Generate Secrets

```bash
# Generate SECRET_KEY
python3 scripts/generate_secret_key.py

# Generate FERNET_KEY
python3 scripts/generate_fernet_key.py

# Add these to your .env file
```

### 3. Start the Stack

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Initialize Database

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head

# Or use the script
./scripts/init_db.sh
```

## Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Mailhog (emails):** http://localhost:8025

## Development

### Backend Development

```bash
# Enter backend container
docker-compose exec backend bash

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Run tests
pytest

# Lint
ruff check .
```

### Frontend Development

```bash
# Enter frontend container
docker-compose exec frontend sh

# Install dependencies
npm install

# Run tests
npm test

# Lint
npm run lint

# Type check
npm run type-check
```

### Local Development (without Docker)

**Backend:**
```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

## Troubleshooting

### Port already in use

```bash
# Find and kill process using port 8000
lsof -i :8000
kill -9 <PID>

# Or change port in .env
API_PORT=8001
```

### Database connection errors

```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
docker-compose exec backend alembic upgrade head
```

### Frontend won't start

```bash
# Clear cache
cd frontend
rm -rf .next node_modules
npm install
```

## Next Steps

1. Read [DEVELOPMENT.md](./DEVELOPMENT.md) for detailed development guide
2. Check [FEATURES_SUMMARY.md](./FEATURES_SUMMARY.md) for feature implementation details
3. Follow [ROADMAP.md](./ROADMAP.md) for development timeline

## Common Commands

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (reset everything)
docker-compose down -v

# Rebuild images
docker-compose build

# View backend logs
docker-compose logs -f backend

# View frontend logs
docker-compose logs -f frontend

# Run a command in backend
docker-compose exec backend <command>

# Access PostgreSQL
docker-compose exec postgres psql -U gitleague -d thegitleague_dev

# Access Redis
docker-compose exec redis redis-cli
```

## Environment Variables

Key environment variables (see `.env.example` for all):

```bash
# Database
POSTGRES_DB=thegitleague_dev
POSTGRES_USER=gitleague
POSTGRES_PASSWORD=<your-password>

# Security
SECRET_KEY=<generated-secret-key>
FERNET_KEY=<generated-fernet-key>

# API
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

**Happy coding!** 🏀

For questions, check [CONTRIBUTING.md](./CONTRIBUTING.md) or open an issue.
