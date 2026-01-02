# 🏗️ Architecture Documentation

This document describes the technical architecture of **The Git League**.

---

## 📋 Table of Contents

- [System Overview](#system-overview)
- [Architecture Diagram](#architecture-diagram)
- [Technology Stack](#technology-stack)
- [Data Models](#data-models)
- [API Design](#api-design)
- [Git Ingestion Pipeline](#git-ingestion-pipeline)
- [Scoring Engine](#scoring-engine)
- [Authentication & Authorization](#authentication--authorization)
- [Deployment Architecture](#deployment-architecture)
- [Security Considerations](#security-considerations)
- [Performance Optimizations](#performance-optimizations)
- [Scaling Strategy](#scaling-strategy)

---

## 🔍 System Overview

The Git League is a **self-hosted web application** that transforms Git commit history into an NBA-style competitive league. The architecture follows a **three-tier pattern**:

1. **Frontend** — Next.js web application (presentation layer)
2. **Backend** — FastAPI REST API (business logic + data access)
3. **Workers** — Celery background jobs (async processing)

**Design Principles:**
- **Privacy-first** — No source code stored, only metadata
- **Explainability** — All metrics are transparent and configurable
- **Self-contained** — No external SaaS dependencies
- **Scalable** — Designed to handle millions of commits
- **Maintainable** — Clear separation of concerns

---

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      FRONTEND (Next.js)                         │
│  - Server-side rendering (SSR)                                  │
│  - Client-side navigation (SPA)                                 │
│  - TanStack Query (caching)                                     │
│  - shadcn/ui components                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API (JSON)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    BACKEND API (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ API Layer (Routes + Validation)                          │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ Service Layer (Business Logic)                           │  │
│  │  - User Service                                           │  │
│  │  - Stats Service (League Engine)                         │  │
│  │  - Awards Service                                         │  │
│  │  - Fantasy Service                                        │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ Data Access Layer (SQLAlchemy ORM)                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────┬────────────────────────────────────┬──────────────────┘
          │                                    │
          │                                    │ Enqueue tasks
          │                                    │
          ▼                                    ▼
┌──────────────────────┐         ┌───────────────────────────────┐
│   PostgreSQL DB      │         │   WORKERS (Celery)            │
│                      │         │  - Git ingestion              │
│ ┌──────────────────┐ │         │  - Stats recompute            │
│ │ Users & Auth     │ │         │  - Awards calculation         │
│ │ Projects & Repos │ │         │  - Scheduled sync             │
│ │ Commits (raw)    │ │         └──────────┬────────────────────┘
│ │ Aggregates       │ │                    │
│ │ Seasons & Awards │ │                    │ Read/Write
│ │ Fantasy          │ │◄───────────────────┘
│ └──────────────────┘ │
└──────────┬───────────┘
           │
           │ Caching + Queue
           ▼
┌──────────────────────┐
│      Redis           │
│  - Job queue         │
│  - Rate limiting     │
│  - Session cache     │
└──────────────────────┘

          External Git Repos
               │
               │ SSH / HTTPS / Local
               ▼
┌──────────────────────────────┐
│   Bare Git Repos (local)     │
│   - Cloned for ingestion     │
│   - Periodic fetch updates   │
└──────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Frontend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | **Next.js 14** (App Router) | React framework with SSR/SSG |
| Language | **TypeScript** | Type safety |
| Styling | **Tailwind CSS** | Utility-first CSS |
| UI Components | **shadcn/ui** | Accessible component library |
| Icons | **Lucide React** | Icon library |
| Data Fetching | **TanStack Query** | Server state management + caching |
| Forms | **React Hook Form** + **Zod** | Form handling + validation |
| Charts | **Recharts** | Data visualization |
| HTTP Client | **Fetch API** (native) | API requests |

### Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | **FastAPI** | High-performance Python API framework |
| Language | **Python 3.11+** | Backend language |
| ORM | **SQLAlchemy 2.x** | Database ORM |
| Migrations | **Alembic** | Schema migrations |
| Validation | **Pydantic v2** | Request/response validation |
| Auth | **python-jose** (JWT) | Token-based authentication |
| Password Hashing | **passlib[argon2]** | Secure password storage |
| ASGI Server | **Uvicorn** | Production server |
| Testing | **pytest** + **httpx** | Unit + integration tests |

### Workers & Queue

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Task Queue | **Celery** or **RQ** | Async job processing |
| Message Broker | **Redis** | Task queue + caching |
| Scheduler | **Celery Beat** | Periodic tasks (sync, awards) |
| Git Library | **GitPython** (or **libgit2**) | Git operations |

### Data Storage

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Database | **PostgreSQL 15+** | Primary data store |
| Cache | **Redis 7+** | Session + rate limiting + queue |
| File Storage | **Local filesystem** | Bare Git repositories |

### Deployment

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Containerization | **Docker** + **Docker Compose** | Local + production deployment |
| Orchestration | **Dokploy** (optional) | Enterprise deployment |
| CI/CD | **GitHub Actions** | Automated testing + builds |

---

## 🗄️ Data Models

### Entity Relationship Diagram

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Users     │         │   Projects   │         │   Seasons   │
├─────────────┤         ├──────────────┤         ├─────────────┤
│ id          │         │ id           │         │ id          │
│ email       │         │ name         │         │ project_id  │◄─┐
│ role        │         │ slug         │◄────────│ name        │  │
│ status      │         │ created_at   │         │ start_at    │  │
│ created_at  │         └──────────────┘         │ end_at      │  │
└──────┬──────┘                │                 │ status      │  │
       │                       │                 └─────────────┘  │
       │                       │                       │          │
       │                       │                       │          │
       │                       ▼                       │          │
       │              ┌──────────────┐                 │          │
       │              │     Repos    │                 │          │
       │              ├──────────────┤                 │          │
       │              │ id           │                 │          │
       │              │ project_id   │                 │          │
       │              │ name         │                 │          │
       │              │ remote_url   │                 │          │
       │              │ branch       │                 │          │
       │              │ last_sync_at │                 │          │
       │              │ status       │                 │          │
       │              └──────┬───────┘                 │          │
       │                     │                         │          │
       │                     │                         │          │
       ▼                     ▼                         ▼          │
┌──────────────┐    ┌──────────────┐         ┌─────────────────┐ │
│GitIdentities │    │   Commits    │         │    Absences     │ │
├──────────────┤    ├──────────────┤         ├─────────────────┤ │
│ id           │    │ sha          │         │ id              │ │
│ user_id      │    │ repo_id      │         │ user_id         │ │
│ git_name     │    │ author_email │         │ season_id       │─┘
│ git_email    │    │ commit_date  │         │ start_at        │
└──────────────┘    │ message      │         │ end_at          │
                    │ additions    │         │ reason          │
                    │ deletions    │         └─────────────────┘
                    │ is_merge     │
                    └──────────────┘
                           │
                           │ Aggregated into
                           ▼
                  ┌────────────────────┐
                  │ PlayerPeriodStats  │
                  ├────────────────────┤
                  │ user_id            │
                  │ season_id          │
                  │ period_type        │ (day/week/month/season/all_time)
                  │ period_start       │
                  │ commits            │
                  │ additions          │
                  │ deletions          │
                  │ pts (points)       │
                  │ reb (rebounds)     │
                  │ ast (assists)      │
                  │ blk (blocks)       │
                  │ stl (steals)       │
                  │ tov (turnovers)    │
                  │ impact_score       │
                  └────────────────────┘
                           │
                           │ Used for
                           ▼
                  ┌────────────────────┐         ┌─────────────────┐
                  │      Awards        │         │  PlayOfTheDay   │
                  ├────────────────────┤         ├─────────────────┤
                  │ id                 │         │ id              │
                  │ season_id          │         │ date            │
                  │ period_type        │         │ commit_sha      │
                  │ period_start       │         │ user_id         │
                  │ award_type         │         │ score           │
                  │ user_id            │         │ metadata_json   │
                  │ score              │         └─────────────────┘
                  │ metadata_json      │
                  └────────────────────┘

         ┌─────────────────┐
         │ FantasyLeagues  │
         ├─────────────────┤
         │ id              │
         │ season_id       │
         │ name            │
         │ roster_min      │
         │ roster_max      │
         │ lock_at         │
         └────────┬────────┘
                  │
                  ▼
         ┌──────────────────────┐
         │FantasyParticipants   │
         ├──────────────────────┤
         │ league_id            │
         │ user_id              │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   FantasyRosters     │
         ├──────────────────────┤
         │ id                   │
         │ league_id            │
         │ user_id              │
         │ locked_at            │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ FantasyRosterPicks   │
         ├──────────────────────┤
         │ roster_id            │
         │ picked_user_id       │
         │ position (1-5)       │
         └──────────────────────┘
```

### Core Tables

#### `users`
```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL, -- 'commissioner', 'player', 'spectator'
    status VARCHAR(20) NOT NULL, -- 'approved', 'pending', 'retired'
    display_name VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### `git_identities`
```sql
CREATE TABLE git_identities (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    git_name VARCHAR(255),
    git_email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, git_email)
);

CREATE INDEX idx_git_identities_email ON git_identities(git_email);
```

#### `projects`
```sql
CREATE TABLE projects (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    created_by VARCHAR(36) REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### `repos`
```sql
CREATE TABLE repos (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    remote_url TEXT,
    remote_type VARCHAR(20), -- 'local', 'ssh', 'https'
    branch VARCHAR(255) NOT NULL DEFAULT 'main',
    sync_frequency VARCHAR(50), -- cron-like: '0 */6 * * *'
    last_sync_at TIMESTAMP,
    last_ingested_sha VARCHAR(40),
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'healthy', 'syncing', 'error'
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, name)
);

CREATE INDEX idx_repos_project ON repos(project_id);
CREATE INDEX idx_repos_status ON repos(status);
```

#### `commits`
```sql
CREATE TABLE commits (
    sha VARCHAR(40) PRIMARY KEY,
    repo_id VARCHAR(36) NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
    author_name VARCHAR(255),
    author_email VARCHAR(255) NOT NULL,
    committer_name VARCHAR(255),
    committer_email VARCHAR(255),
    commit_date TIMESTAMP NOT NULL,
    message_title VARCHAR(500),
    message_body TEXT,
    additions INTEGER NOT NULL DEFAULT 0,
    deletions INTEGER NOT NULL DEFAULT 0,
    files_changed INTEGER NOT NULL DEFAULT 0,
    is_merge BOOLEAN NOT NULL DEFAULT FALSE,
    parent_count INTEGER NOT NULL DEFAULT 1,
    ingested_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_commits_repo ON commits(repo_id);
CREATE INDEX idx_commits_date ON commits(commit_date);
CREATE INDEX idx_commits_author ON commits(author_email);
CREATE INDEX idx_commits_repo_date ON commits(repo_id, commit_date);
```

#### `seasons`
```sql
CREATE TABLE seasons (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    start_at TIMESTAMP NOT NULL,
    end_at TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft', -- 'draft', 'active', 'closed'
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, name),
    CHECK (end_at > start_at)
);

CREATE INDEX idx_seasons_project ON seasons(project_id);
CREATE INDEX idx_seasons_status ON seasons(status);
CREATE INDEX idx_seasons_dates ON seasons(start_at, end_at);
```

#### `player_period_stats`
```sql
CREATE TABLE player_period_stats (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    season_id VARCHAR(36) REFERENCES seasons(id) ON DELETE CASCADE,
    period_type VARCHAR(20) NOT NULL, -- 'day', 'week', 'month', 'season', 'all_time'
    period_start DATE NOT NULL,
    commits INTEGER NOT NULL DEFAULT 0,
    additions INTEGER NOT NULL DEFAULT 0,
    deletions INTEGER NOT NULL DEFAULT 0,
    net_lines INTEGER NOT NULL DEFAULT 0,
    pts INTEGER NOT NULL DEFAULT 0, -- NBA points
    reb INTEGER NOT NULL DEFAULT 0, -- rebounds
    ast INTEGER NOT NULL DEFAULT 0, -- assists
    blk INTEGER NOT NULL DEFAULT 0, -- blocks
    stl INTEGER NOT NULL DEFAULT 0, -- steals
    tov INTEGER NOT NULL DEFAULT 0, -- turnovers
    impact_score FLOAT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, season_id, period_type, period_start)
);

CREATE INDEX idx_stats_user_season ON player_period_stats(user_id, season_id);
CREATE INDEX idx_stats_period ON player_period_stats(period_type, period_start);
CREATE INDEX idx_stats_season_period ON player_period_stats(season_id, period_type, period_start);
```

#### `awards`
```sql
CREATE TABLE awards (
    id VARCHAR(36) PRIMARY KEY,
    season_id VARCHAR(36) NOT NULL REFERENCES seasons(id) ON DELETE CASCADE,
    period_type VARCHAR(20) NOT NULL, -- 'week', 'month', 'season'
    period_start DATE NOT NULL,
    award_type VARCHAR(50) NOT NULL, -- 'player_of_week', 'player_of_month', 'mvp', 'most_improved'
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score FLOAT NOT NULL,
    metadata_json JSONB, -- Breakdown details
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(season_id, period_type, period_start, award_type)
);

CREATE INDEX idx_awards_season ON awards(season_id);
CREATE INDEX idx_awards_user ON awards(user_id);
```

### Indexes Strategy

**Performance targets:**
- Leaderboard queries: < 300ms
- Player profile: < 200ms
- Commit ingestion: 100k commits < 5 min

**Critical indexes:**
- `commits(repo_id, commit_date)` — Ingestion queries
- `commits(author_email)` — Identity matching
- `player_period_stats(season_id, period_type, period_start)` — Leaderboards
- `player_period_stats(user_id, season_id)` — Player profiles

---

## 🔌 API Design

### REST Principles

- **Resource-oriented** — `/api/v1/players/{id}`, not `/api/v1/getPlayer`
- **HTTP methods** — GET (read), POST (create), PUT/PATCH (update), DELETE (delete)
- **Status codes** — 200 (OK), 201 (Created), 400 (Bad Request), 401 (Unauthorized), 404 (Not Found), 500 (Server Error)
- **Pagination** — `?page=1&limit=50` for lists
- **Filtering** — `?season_id=...&repo_id=...` for queries
- **Sorting** — `?sort_by=pts&order=desc`

### API Versioning

All endpoints are versioned: `/api/v1/...`

Breaking changes require a new version: `/api/v2/...`

### Authentication

**Token-based (JWT)**

```
Authorization: Bearer <jwt_token>
```

**Magic Link Flow:**
1. POST `/api/v1/auth/magic-link` (email)
2. User receives email with token
3. GET `/api/v1/auth/verify?token=...`
4. Returns JWT access token

See [API_SPEC.md](./API_SPEC.md) for full endpoint documentation.

---

## 🔄 Git Ingestion Pipeline

### Architecture

```
┌──────────────┐
│  Scheduler   │ (Celery Beat)
│ (cron jobs)  │
└──────┬───────┘
       │ Every N hours
       │
       ▼
┌──────────────────────┐
│  sync_repo_task()    │ (Celery task)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  1. Clone/Fetch repo (bare)          │
│     - First sync: clone --bare       │
│     - Incremental: git fetch         │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  2. Extract commits since last sync  │
│     - git log <last_sha>..HEAD       │
│     - git show --numstat <sha>       │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  3. Transform & normalize            │
│     - Parse author/committer         │
│     - Normalize emails (lowercase)   │
│     - Detect merge commits           │
│     - Extract stats                  │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  4. Load into database (batch)       │
│     - INSERT ... ON CONFLICT IGNORE  │
│     - Update last_ingested_sha       │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  5. Trigger stats recompute          │
│     - Enqueue recompute_stats_task() │
└──────────────────────────────────────┘
```

### Idempotency

- Commits table uses `sha` as primary key
- `ON CONFLICT DO NOTHING` prevents duplicates
- Safe to re-run sync for same time period

### Error Handling

- Transient errors (network) → Retry with exponential backoff
- Invalid repo → Mark status='error', store error_message
- Force-push / rewrite → Best effort (mark orphans, don't fail)

### Performance

**Batch processing:**
- Insert commits in batches of 1000
- Use COPY for PostgreSQL bulk inserts (future optimization)

**Concurrency:**
- One sync per repo at a time (lock via Celery)
- Multiple repos can sync in parallel

---

## 📊 Scoring Engine

### NBA Metrics Calculation

**V1 Heuristics (configurable per project):**

```python
# Coefficients (stored in project_config table)
ADDITIONS_WEIGHT = 1.0
DELETIONS_WEIGHT = 0.6
COMMIT_BASE = 10
MULTI_FILE_BONUS = 5
FIX_BONUS = 15
WIP_PENALTY = -10

# Caps (anti-spam)
MAX_ADDITIONS_PER_COMMIT = 1000
MAX_DELETIONS_PER_COMMIT = 1000

# Calculation
def calculate_pts(commit):
    base = COMMIT_BASE
    additions = min(commit.additions, MAX_ADDITIONS_PER_COMMIT) * ADDITIONS_WEIGHT
    return int(base + additions)

def calculate_reb(commit):
    deletions = min(commit.deletions, MAX_DELETIONS_PER_COMMIT) * DELETIONS_WEIGHT
    return int(deletions)

def calculate_ast(commit):
    if commit.files_changed > 3:
        return MULTI_FILE_BONUS
    return 0

def calculate_blk(commit):
    if re.search(r'\b(fix|bug|hotfix|revert)\b', commit.message_title, re.I):
        return FIX_BONUS
    return 0

def calculate_tov(commit):
    if re.search(r'\b(wip|tmp|debug|test)\b', commit.message_title, re.I):
        return WIP_PENALTY
    return 0

# Impact score (composite)
def calculate_impact_score(pts, reb, ast, blk, tov):
    return pts * 1.0 + reb * 0.6 + ast * 0.8 + blk * 1.2 + tov * 0.7
```

### Aggregation Pipeline

```python
# Recompute stats for a season
def recompute_season_stats(season_id):
    commits = get_commits_in_season(season_id)

    # Group by user + period
    for period_type in ['day', 'week', 'month', 'season']:
        stats = defaultdict(lambda: {
            'commits': 0, 'additions': 0, 'deletions': 0,
            'pts': 0, 'reb': 0, 'ast': 0, 'blk': 0, 'tov': 0
        })

        for commit in commits:
            user_id = get_user_by_email(commit.author_email)
            period_start = get_period_start(commit.commit_date, period_type)
            key = (user_id, period_start)

            stats[key]['commits'] += 1
            stats[key]['additions'] += commit.additions
            stats[key]['deletions'] += commit.deletions
            stats[key]['pts'] += calculate_pts(commit)
            stats[key]['reb'] += calculate_reb(commit)
            stats[key]['ast'] += calculate_ast(commit)
            stats[key]['blk'] += calculate_blk(commit)
            stats[key]['tov'] += calculate_tov(commit)

        # Upsert into player_period_stats
        bulk_upsert(stats, season_id, period_type)
```

---

## 🔐 Authentication & Authorization

### Authentication Flow

**Magic Link (V1):**
1. User enters email
2. Backend generates token (JWT, exp=15min)
3. Email sent with link: `https://app/auth/verify?token=...`
4. User clicks → token validated → session created
5. Session token (JWT, exp=24h) returned

**Token Structure:**
```json
{
  "sub": "user-id-123",
  "email": "alice@example.com",
  "role": "player",
  "exp": 1234567890
}
```

### Authorization (RBAC)

**Roles:**

| Role | Permissions |
|------|------------|
| **Commissioner** | All access (manage projects, repos, seasons, users, awards) |
| **Player** | Read own stats, leaderboards, fantasy; manage own fantasy roster |
| **Spectator** | Read-only access to leaderboards, awards, public profiles |

**Enforcement:**

```python
# FastAPI dependency
def require_commissioner(token: str = Depends(get_token)):
    user = decode_token(token)
    if user.role != 'commissioner':
        raise HTTPException(403, "Commissioner role required")
    return user

# Usage
@router.post("/repos", dependencies=[Depends(require_commissioner)])
async def create_repo(...):
    ...
```

---

## 🚀 Deployment Architecture

### Docker Compose (Development & Production)

```yaml
version: '3.9'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: thegitleague
      POSTGRES_USER: gitleague
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    environment:
      DATABASE_URL: postgresql://gitleague:${POSTGRES_PASSWORD}@postgres:5432/thegitleague
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - repos_storage:/repos

  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    command: celery -A app.workers.celery_app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql://gitleague:${POSTGRES_PASSWORD}@postgres:5432/thegitleague
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - repos_storage:/repos

  beat:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    command: celery -A app.workers.celery_app beat --loglevel=info
    environment:
      DATABASE_URL: postgresql://gitleague:${POSTGRES_PASSWORD}@postgres:5432/thegitleague
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - redis

  frontend:
    build:
      context: .
      dockerfile: docker/Dockerfile.frontend
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000/api/v1
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
  repos_storage:
```

---

## 🔒 Security Considerations

### 1. No Source Code Storage
- Only commit metadata stored
- SHA, message, stats (additions/deletions)
- Never store file contents or diffs

### 2. Encrypted Secrets
- Repository credentials encrypted at rest (Fernet)
- Environment variables for sensitive config
- Secrets never logged

### 3. Input Validation
- All inputs validated via Pydantic
- SQL injection prevented by ORM
- XSS prevented by React escaping

### 4. Rate Limiting
- API: 100 requests/min per user
- Auth endpoints: 5 requests/min
- Redis-based rate limiter

### 5. Audit Logs
- User approvals logged
- Config changes logged
- Sync operations logged

---

## ⚡ Performance Optimizations

### 1. Database
- Indexes on hot paths
- Pre-aggregated stats tables
- Connection pooling (SQLAlchemy)

### 2. Caching
- TanStack Query (frontend, 5min TTL)
- Redis for session + rate limiting
- HTTP cache headers

### 3. Async Processing
- Git ingestion in background
- Stats recompute asynchronous
- Awards calculation batched

### 4. Query Optimization
- Select only needed fields
- Pagination on large lists
- EXPLAIN ANALYZE for slow queries

---

## 📈 Scaling Strategy

### Vertical Scaling (Initial)
- More CPU/RAM for backend
- PostgreSQL tuning (shared_buffers, work_mem)

### Horizontal Scaling (Future)
- Multiple backend instances (stateless)
- Load balancer (nginx)
- Read replicas for PostgreSQL
- Celery workers on separate machines

### Sharding (If Needed)
- Partition `commits` table by repo_id
- Separate databases per project (extreme scale)

---

**For API details, see [API_SPEC.md](./API_SPEC.md)**
