# 🚀 Deployment Guide — The Git League

This guide covers deploying The Git League to various cloud platforms and on-premises environments.

**Table of Contents:**
- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Cloud Platforms](#cloud-platforms)
- [Database Setup](#database-setup)
- [Environment Configuration](#environment-configuration)
- [Security Checklist](#security-checklist)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)

---

## Prerequisites

### Required
- Docker & Docker Compose (recommended)
- Git repository access
- Domain name (for production)
- Email provider credentials (SMTP)

### System Requirements
- **CPU:** 2+ cores
- **RAM:** 4GB minimum (8GB recommended)
- **Storage:** 20GB+ (depends on commit history)
- **Database:** PostgreSQL 13+

---

## Local Development

### Quick Start

```bash
# Clone repository
git clone https://github.com/Boblebol/TheGitLeague.git
cd TheGitLeague

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Initialize database (first time only)
docker-compose exec backend alembic upgrade head

# Access application
open http://localhost:3000
```

### Verify Setup

```bash
# Check all services running
docker-compose ps

# View logs
docker-compose logs -f backend

# Test API
curl http://localhost:8000/api/v1/health
```

---

## Docker Deployment

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $DB_USER"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    image: ${REGISTRY}/thegitleague-backend:${VERSION}
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_URL: redis://redis:6379
      ENVIRONMENT: production
      SECRET_KEY: ${SECRET_KEY}
      FERNET_KEY: ${FERNET_KEY}
      CORS_ORIGINS: ${CORS_ORIGINS}
      EMAIL_FROM: ${EMAIL_FROM}
      SMTP_HOST: ${SMTP_HOST}
      SMTP_PORT: ${SMTP_PORT}
      SMTP_USER: ${SMTP_USER}
      SMTP_PASSWORD: ${SMTP_PASSWORD}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker:
    image: ${REGISTRY}/thegitleague-backend:${VERSION}
    command: celery -A app.core.celery_app worker -l info
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_URL: redis://redis:6379
      ENVIRONMENT: production
      SECRET_KEY: ${SECRET_KEY}
      FERNET_KEY: ${FERNET_KEY}
    depends_on:
      - postgres
      - redis
    restart: always

  beat:
    image: ${REGISTRY}/thegitleague-backend:${VERSION}
    command: celery -A app.core.celery_app beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_URL: redis://redis:6379
      ENVIRONMENT: production
      SECRET_KEY: ${SECRET_KEY}
      FERNET_KEY: ${FERNET_KEY}
    depends_on:
      - postgres
      - redis
    restart: always

  frontend:
    image: ${REGISTRY}/thegitleague-frontend:${VERSION}
    environment:
      NEXT_PUBLIC_API_URL: ${API_URL}
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
    restart: always

volumes:
  postgres_data:
  redis_data:
```

### Production Environment File

Create `.env.production`:

```bash
# Database
DB_NAME=thegitleague
DB_USER=postgres
DB_PASSWORD=YOUR_SECURE_PASSWORD
DATABASE_URL=postgresql://postgres:PASSWORD@postgres:5432/thegitleague

# Redis
REDIS_URL=redis://redis:6379

# App Settings
ENVIRONMENT=production
SECRET_KEY=YOUR_GENERATED_SECRET_KEY
FERNET_KEY=YOUR_GENERATED_FERNET_KEY

# CORS
CORS_ORIGINS=https://yourdomain.com

# Email
EMAIL_FROM=noreply@yourdomain.com
SMTP_HOST=your-email-provider.com
SMTP_PORT=587
SMTP_USER=your-email@domain.com
SMTP_PASSWORD=your-app-password

# API
API_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com

# Docker Registry
REGISTRY=your-registry.com/yournamespace
VERSION=1.0.0
```

### Generate Secure Keys

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate FERNET_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate database password
openssl rand -base64 32
```

### Deploy with Docker

```bash
# Build images
docker build -f docker/Dockerfile.backend -t your-registry/thegitleague-backend:1.0.0 .
docker build -f docker/Dockerfile.frontend -t your-registry/thegitleague-frontend:1.0.0 .

# Push to registry
docker push your-registry/thegitleague-backend:1.0.0
docker push your-registry/thegitleague-frontend:1.0.0

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

---

## Cloud Platforms

### Vercel (Frontend Only)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy frontend
cd frontend
vercel --prod

# Set environment variables in Vercel dashboard
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Fly.io (Recommended)

#### Fly App Configuration

Create `fly.toml`:

```toml
app = "thegitleague"
kill_signal = "SIGINT"
kill_timeout = 5

[build]
  builder = "dockerfile"
  dockerfile = "docker/Dockerfile.backend"

[[services]]
  protocol = "tcp"
  internal_port = 8000
  processes = ["app"]

  [[services.ports]]
    port = 80
    handlers = ["http"]
  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

[env]
  ENVIRONMENT = "production"

[[vm]]
  cpu_kind = "shared"
  cpus = 2
  memory_mb = 1024
```

#### Deploy to Fly.io

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Create app
flyctl launch

# Set secrets
flyctl secrets set SECRET_KEY=your-secret-key
flyctl secrets set FERNET_KEY=your-fernet-key
flyctl secrets set DATABASE_URL=postgresql://user:pass@host/db

# Deploy
flyctl deploy

# View logs
flyctl logs
```

### Railway (One-Click)

1. Connect GitHub repo to Railway
2. Add PostgreSQL and Redis from Railway marketplace
3. Set environment variables in Railway dashboard:
   ```
   DATABASE_URL: (auto-generated)
   REDIS_URL: (auto-generated)
   SECRET_KEY: your-secret
   FERNET_KEY: your-fernet-key
   ```
4. Deploy automatically on git push

### DigitalOcean App Platform

1. Create new app from repository
2. Set build command: `docker build -f docker/Dockerfile.backend .`
3. Set run command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add managed PostgreSQL and Redis
5. Configure environment variables
6. Deploy

### AWS (ECS + RDS + ElastiCache)

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name thegitleague

# Create RDS PostgreSQL
aws rds create-db-instance \
  --db-instance-identifier thegitleague-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --allocated-storage 20

# Create ElastiCache Redis
aws elasticache create-cache-cluster \
  --cache-cluster-id thegitleague-redis \
  --engine redis \
  --cache-node-type cache.t3.micro

# Push Docker image to ECR
aws ecr create-repository --repository-name thegitleague
docker tag thegitleague:latest ACCOUNT.dkr.ecr.REGION.amazonaws.com/thegitleague:latest
docker push ACCOUNT.dkr.ecr.REGION.amazonaws.com/thegitleague:latest

# Create ECS task definition and service
# (See AWS ECS documentation for detailed steps)
```

### Google Cloud Run

```bash
# Build image
gcloud builds submit --tag gcr.io/PROJECT_ID/thegitleague

# Deploy
gcloud run deploy thegitleague \
  --image gcr.io/PROJECT_ID/thegitleague \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=postgresql://... \
  --set-env-vars REDIS_URL=redis://...
```

### Dokploy (Self-Hosted)

```bash
# Install Dokploy
docker run -d --name dokploy \
  -p 3000:3000 \
  dokploy/dokploy:latest

# Visit Dokploy UI on :3000
# Connect GitHub repo
# Configure environment
# Deploy
```

---

## Database Setup

### PostgreSQL Initialization

```bash
# Connect to PostgreSQL
psql -h localhost -U postgres

# Create database
CREATE DATABASE thegitleague;

# Create user with permissions
CREATE USER thegitleague WITH PASSWORD 'secure_password';
ALTER ROLE thegitleague SET client_encoding TO 'utf8';
ALTER ROLE thegitleague SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE thegitleague TO thegitleague;
```

### Run Migrations

```bash
# From Docker
docker-compose exec backend alembic upgrade head

# From local environment
cd backend
alembic upgrade head
```

### Backup Database

```bash
# Backup
pg_dump -h localhost -U postgres thegitleague > backup.sql

# Restore
psql -h localhost -U postgres thegitleague < backup.sql

# Docker backup
docker-compose exec postgres pg_dump -U postgres thegitleague > backup.sql
```

---

## Environment Configuration

### Essential Variables

```bash
# Core
ENVIRONMENT=production
SECRET_KEY=your-generated-secret-key
FERNET_KEY=your-generated-fernet-key

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379

# API
API_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Email (SMTP)
EMAIL_FROM=noreply@yourdomain.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Optional
LOG_LEVEL=info
MAX_WORKERS=4
CELERY_BEAT_ENABLED=true
```

### Sensitive Variables

**Never commit these:**
- `SECRET_KEY`
- `FERNET_KEY`
- `DB_PASSWORD`
- `SMTP_PASSWORD`
- Database credentials

**Use:**
- `.env.local` for local development
- Secret manager for production (Vault, AWS Secrets Manager, etc.)
- Environment variables on deployment platform

---

## SSL/TLS Setup

### Let's Encrypt with nginx

```bash
# Install Certbot
apt-get install certbot python3-certbot-nginx

# Generate certificate
certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Configure nginx
sudo nano /etc/nginx/sites-available/default
```

### Nginx Configuration

```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Security Checklist

- [ ] All secrets in environment variables (not in code)
- [ ] Database backups configured
- [ ] HTTPS/SSL enabled
- [ ] Firewall rules configured
- [ ] Database access restricted to app server
- [ ] Redis access restricted to app server
- [ ] Regular security patches applied
- [ ] Rate limiting enabled
- [ ] CORS configured correctly
- [ ] Monitoring and logging enabled
- [ ] Automated backups scheduled
- [ ] Disaster recovery plan in place

---

## Monitoring & Troubleshooting

### Health Checks

```bash
# API health
curl https://yourdomain.com/api/v1/health

# Database connection
curl https://yourdomain.com/api/v1/health/db

# Redis connection
curl https://yourdomain.com/api/v1/health/redis
```

### Common Issues

**503 Service Unavailable**
```bash
# Check services
docker-compose ps

# View logs
docker-compose logs backend

# Restart service
docker-compose restart backend
```

**Database Connection Error**
```bash
# Verify environment variable
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Run migrations
docker-compose exec backend alembic upgrade head
```

**Redis Connection Error**
```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# View Redis logs
docker-compose logs redis
```

**High Memory Usage**
```bash
# Check Docker stats
docker stats

# Increase resources in docker-compose.yml
# Under backend service:
# deploy:
#   resources:
#     limits:
#       memory: 2G
```

### Logging

```bash
# View recent logs
docker-compose logs -f --tail 100 backend

# Export logs
docker-compose logs backend > logs.txt

# Configure log level
# Set LOG_LEVEL=debug for verbose logging
```

### Performance Monitoring

```bash
# Database query performance
SELECT query, calls, mean_time FROM pg_stat_statements
ORDER BY mean_time DESC LIMIT 10;

# Redis memory
redis-cli INFO memory

# System resources
docker stats
```

---

## Updating

### Rolling Update

```bash
# Build new image
docker build -f docker/Dockerfile.backend -t your-registry/thegitleague:2.0.0 .

# Push
docker push your-registry/thegitleague:2.0.0

# Update docker-compose.yml with new VERSION
# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Run migrations (if needed)
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Zero-Downtime Update

Use Docker Swarm or Kubernetes with rolling update strategy:

```yaml
# Kubernetes deployment
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

---

## Support

For deployment issues:
- Check logs: `docker-compose logs backend`
- Review this guide
- Open GitHub issue: https://github.com/Boblebol/TheGitLeague/issues
- Start discussion: https://github.com/Boblebol/TheGitLeague/discussions

---

**Last Updated:** January 2026
**Version:** 1.0.0
