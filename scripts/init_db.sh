#!/bin/bash
# Initialize database with Alembic migrations

set -e

echo "🏀 Initializing The Git League database..."

# Wait for database to be ready
echo "⏳ Waiting for PostgreSQL..."
until docker-compose exec -T postgres pg_isready -U gitleague > /dev/null 2>&1; do
  sleep 1
done

echo "✅ PostgreSQL is ready"

# Run migrations
echo "🔄 Running Alembic migrations..."
docker-compose exec backend alembic upgrade head

echo "✅ Database initialized successfully!"
