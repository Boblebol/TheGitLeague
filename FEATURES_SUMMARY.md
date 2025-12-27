# 🎯 Features Summary

This document provides a comprehensive breakdown of all features in **The Git League**, organized by development phase.

---

## 📋 Table of Contents

- [Phase 1: MVP Features (V1.0)](#phase-1-mvp-features-v10)
  - [Feature A: Onboarding & Authentication](#feature-a-onboarding--authentication)
  - [Feature B: Multi-Project & Repository Management](#feature-b-multi-project--repository-management)
  - [Feature C: Git Ingestion Pipeline](#feature-c-git-ingestion-pipeline)
  - [Feature D: NBA Metrics & Scoring](#feature-d-nba-metrics--scoring)
  - [Feature E: Seasons & Periods](#feature-e-seasons--periods)
  - [Feature F: Leaderboards](#feature-f-leaderboards)
  - [Feature G: Player Profiles](#feature-g-player-profiles)
  - [Feature H: Awards & Highlights](#feature-h-awards--highlights)
  - [Feature I: Fantasy League](#feature-i-fantasy-league)
  - [Feature J: Hall of Fame](#feature-j-hall-of-fame)
- [Phase 2: Enhancement Features (V2.0)](#phase-2-enhancement-features-v20)
- [Phase 3: Advanced Features (V3.0)](#phase-3-advanced-features-v30)

---

## Phase 1: MVP Features (V1.0)

### Feature A: Onboarding & Authentication

**Priority:** Must-Have
**Timeline:** Week 1-2
**Owner:** Backend + Frontend

#### Description
Secure, passwordless authentication system with role-based access control (RBAC). Users log in via magic links sent to their email. Three distinct roles define permissions throughout the application.

#### User Stories

**As a Commissioner:**
- I want to invite users and assign their roles, so I can control who accesses the league and what they can do
- I want to approve spectator requests, so I can manage who views the league data

**As a Player:**
- I want to log in via a magic link, so I don't need to remember a password
- I want my commits automatically linked to my profile, so I don't have to manually claim them

**As a Spectator:**
- I want to request access to the league, so I can follow the team's progress
- I want read-only access, so I can view stats without accidentally changing anything

#### Technical Implementation

**Authentication Flow:**
1. User enters email → `POST /api/v1/auth/magic-link`
2. Backend generates JWT token (15min expiry) + sends email
3. User clicks link → `GET /api/v1/auth/verify?token=xyz`
4. Backend validates token → returns session JWT (24h expiry)
5. Frontend stores token in localStorage/httpOnly cookie

**Database Models:**
```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL, -- 'commissioner', 'player', 'spectator'
    status VARCHAR(20) NOT NULL, -- 'approved', 'pending', 'retired'
    display_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE git_identities (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    git_name VARCHAR(255),
    git_email VARCHAR(255) NOT NULL,
    UNIQUE(user_id, git_email)
);
```

**RBAC Middleware (FastAPI):**
```python
def require_role(allowed_roles: List[str]):
    def dependency(token: str = Depends(get_token)):
        user = decode_jwt(token)
        if user.role not in allowed_roles:
            raise HTTPException(403, "Insufficient permissions")
        return user
    return dependency

# Usage
@router.post("/repos", dependencies=[Depends(require_role(["commissioner"]))])
```

#### Acceptance Criteria

- [x] Magic link authentication works (15min token expiry)
- [x] User can have multiple Git identities (multiple emails)
- [x] Spectators cannot access protected resources until approved
- [x] Audit log tracks user approvals (who approved, when)
- [x] Session tokens expire after 24 hours
- [x] Expired tokens return 401 with clear error message

#### Edge Cases

- **Email already exists:** Return helpful error
- **Token expired:** Show "Link expired, request new one"
- **Git identity conflict:** Allow manual claiming + Commissioner approval
- **Multiple commissioners:** First user is auto-commissioner, can promote others

---

### Feature B: Multi-Project & Repository Management

**Priority:** Must-Have
**Timeline:** Week 3-4
**Owner:** Backend + Frontend

#### Description
Commissioners can create projects (collections of repositories) and configure individual repos for Git ingestion. Supports local bare repos, SSH, and HTTPS with credentials.

#### User Stories

**As a Commissioner:**
- I want to create a project, so I can organize multiple repos under one league
- I want to add repos with different access methods (SSH, HTTPS, local), so I can ingest from any Git source
- I want to see sync status for each repo, so I know if ingestion is working
- I want to configure sync frequency, so I control when repos are updated

#### Technical Implementation

**Project Entity:**
```sql
CREATE TABLE projects (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    created_by VARCHAR(36) REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Repository Entity:**
```sql
CREATE TABLE repos (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    remote_url TEXT,
    remote_type VARCHAR(20), -- 'local', 'ssh', 'https'
    branch VARCHAR(255) DEFAULT 'main',
    sync_frequency VARCHAR(50), -- cron-like: '0 */6 * * *'
    last_sync_at TIMESTAMP,
    last_ingested_sha VARCHAR(40),
    status VARCHAR(20) DEFAULT 'pending', -- 'healthy', 'syncing', 'error'
    error_message TEXT,
    credentials_encrypted TEXT, -- Fernet-encrypted JSON
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Credential Encryption:**
```python
from cryptography.fernet import Fernet

def encrypt_credentials(data: dict, key: str) -> str:
    f = Fernet(key.encode())
    json_data = json.dumps(data)
    return f.encrypt(json_data.encode()).decode()

def decrypt_credentials(encrypted: str, key: str) -> dict:
    f = Fernet(key.encode())
    decrypted = f.decrypt(encrypted.encode())
    return json.loads(decrypted)
```

**API Endpoints:**
- `GET /api/v1/projects` — List projects
- `POST /api/v1/projects` — Create project
- `GET /api/v1/projects/{id}/repos` — List repos in project
- `POST /api/v1/projects/{id}/repos` — Add repo
- `PATCH /api/v1/repos/{id}` — Update repo config
- `DELETE /api/v1/repos/{id}` — Remove repo
- `POST /api/v1/repos/{id}/sync` — Trigger immediate sync

#### UI Components

**Project List:**
```
┌──────────────────────────────────────┐
│ Projects                             │
│ [+ New Project]                      │
├──────────────────────────────────────┤
│ Engineering League (eng-league)      │
│ 5 repos • Active season: 2024 Q1     │
│ [View] [Edit]                        │
└──────────────────────────────────────┘
```

**Add Repo Form:**
```
Name: [frontend          ]
Type: [SSH ▼]
Remote URL: [git@github.com:company/frontend.git]
Branch: [main            ]
Sync Frequency: [Every 6 hours ▼]
Credentials:
  SSH Key: [Upload .ssh/id_rsa] or [Paste key]

[Test Connection] [Add Repository]
```

#### Acceptance Criteria

- [x] CRUD operations for Projects
- [x] CRUD operations for Repos
- [x] Repo status tracking: healthy / syncing / error
- [x] Support for SSH (key-based), HTTPS (token), and local bare repos
- [x] Credentials stored encrypted (Fernet)
- [x] Sync frequency configurable (cron syntax)
- [x] "Test Connection" validates credentials before saving
- [x] Last sync timestamp and SHA displayed
- [x] Error messages stored and visible to Commissioner

#### Edge Cases

- **Invalid credentials:** Show error, don't save repo
- **Duplicate repo name:** Prevent in same project
- **Repo deletion:** Cascade delete commits (with confirmation)
- **Branch doesn't exist:** Mark as error, suggest valid branches

---

### Feature C: Git Ingestion Pipeline

**Priority:** Must-Have
**Timeline:** Week 3-4
**Owner:** Backend (Workers)

#### Description
Background workers that extract commit metadata from Git repositories incrementally and idempotently. Supports large repos (millions of commits) with efficient batch processing.

#### User Stories

**As a Commissioner:**
- I want repos to sync automatically on schedule, so data stays current without manual intervention
- I want to trigger manual syncs, so I can update data immediately when needed
- I want to see sync logs, so I can troubleshoot errors

**As the System:**
- I want idempotent ingestion, so rerunning sync doesn't create duplicates
- I want to handle force-pushes gracefully, so history rewrites don't break the league

#### Technical Implementation

**Ingestion Architecture:**
```
Celery Beat (Scheduler)
    │
    ├─> sync_repo_task(repo_id) [every 6h]
    │       │
    │       ├─> Clone/Fetch bare repo
    │       ├─> Extract commits since last_sha
    │       ├─> Parse metadata (GitPython)
    │       ├─> Batch insert commits (1000/batch)
    │       ├─> Update last_ingested_sha
    │       └─> Trigger recompute_stats_task()
    │
    └─> Error handling + retry (exponential backoff)
```

**Worker Task:**
```python
@celery_app.task(bind=True, max_retries=3)
def sync_repo_task(self, repo_id: str):
    repo = get_repo(repo_id)

    # Update status
    repo.status = 'syncing'
    db.commit()

    try:
        # Clone or fetch
        bare_path = f"/repos/{repo_id}.git"
        if not os.path.exists(bare_path):
            git.Repo.clone_from(repo.remote_url, bare_path, bare=True)
        else:
            git_repo = git.Repo(bare_path)
            git_repo.remote('origin').fetch()

        # Extract commits since last sync
        git_repo = git.Repo(bare_path)
        commits = git_repo.iter_commits(
            f"{repo.last_ingested_sha}..{repo.branch}"
        )

        # Process in batches
        batch = []
        for commit in commits:
            metadata = extract_commit_metadata(commit)
            batch.append(metadata)

            if len(batch) >= 1000:
                bulk_insert_commits(batch)
                batch = []

        if batch:
            bulk_insert_commits(batch)

        # Update repo status
        repo.status = 'healthy'
        repo.last_sync_at = datetime.utcnow()
        repo.last_ingested_sha = git_repo.head.commit.hexsha
        db.commit()

        # Trigger stats recompute
        recompute_stats_task.delay(repo.project_id)

    except Exception as e:
        repo.status = 'error'
        repo.error_message = str(e)
        db.commit()

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
```

**Metadata Extraction:**
```python
def extract_commit_metadata(commit: git.Commit) -> dict:
    stats = commit.stats.total

    return {
        'sha': commit.hexsha,
        'author_name': commit.author.name,
        'author_email': commit.author.email.lower(),
        'committer_name': commit.committer.name,
        'committer_email': commit.committer.email.lower(),
        'commit_date': datetime.fromtimestamp(commit.committed_date),
        'message_title': commit.message.split('\n')[0][:500],
        'message_body': commit.message,
        'additions': stats.get('insertions', 0),
        'deletions': stats.get('deletions', 0),
        'files_changed': stats.get('files', 0),
        'is_merge': len(commit.parents) > 1,
        'parent_count': len(commit.parents),
    }
```

**Idempotent Insert:**
```sql
INSERT INTO commits (sha, repo_id, ...)
VALUES (?, ?, ...)
ON CONFLICT (sha) DO NOTHING;
```

#### Acceptance Criteria

- [x] Incremental ingestion (only new commits since last sync)
- [x] Idempotent (rerunning sync doesn't duplicate)
- [x] Performance: 100k commits ingested in < 5 minutes
- [x] Batch processing (1000 commits per batch)
- [x] Handles merge commits (flag set correctly)
- [x] Email normalization (lowercase)
- [x] Structured logs (JSON format with timestamps)
- [x] Sync errors visible in UI with actionable messages
- [x] Retry logic with exponential backoff (3 attempts)

#### Edge Cases

- **Force-push detected:** Mark orphaned commits, don't fail
- **Empty repo:** Handle gracefully, no commits to ingest
- **Very large commits:** Cap stats at reasonable limits
- **Network timeout:** Retry with backoff
- **Credential expiration:** Mark error, alert Commissioner

#### Performance Optimizations

- Use `--numstat` for faster stat extraction
- Parallel worker processes (multiple repos at once)
- PostgreSQL COPY for bulk inserts (future)
- Streaming for very large repos

---

### Feature D: NBA Metrics & Scoring

**Priority:** Must-Have
**Timeline:** Week 5-6
**Owner:** Backend (League Engine)

#### Description
Transform raw Git stats into NBA-inspired basketball metrics (PTS, REB, AST, BLK, STL, TOV). All calculations are transparent, configurable, and deterministic.

#### User Stories

**As a Player:**
- I want to see my NBA-style stats, so I can understand my contribution in a fun way
- I want to click on any score and see the breakdown, so I understand how it's calculated

**As a Commissioner:**
- I want to adjust scoring coefficients, so the metrics match our team culture
- I want to preview score changes before applying, so I don't accidentally skew results
- I want a "Rules" page that explains calculations, so everyone understands the system

#### Technical Implementation

**Scoring Configuration:**
```sql
CREATE TABLE project_config (
    project_id VARCHAR(36) PRIMARY KEY REFERENCES projects(id),
    scoring_coefficients JSONB DEFAULT '{
        "additions_weight": 1.0,
        "deletions_weight": 0.6,
        "commit_base": 10,
        "multi_file_bonus": 5,
        "fix_bonus": 15,
        "wip_penalty": -10,
        "max_additions_cap": 1000,
        "max_deletions_cap": 1000
    }'::jsonb
);
```

**NBA Metrics Calculation:**
```python
from dataclasses import dataclass

@dataclass
class ScoringCoefficients:
    additions_weight: float = 1.0
    deletions_weight: float = 0.6
    commit_base: int = 10
    multi_file_bonus: int = 5
    fix_bonus: int = 15
    wip_penalty: int = -10
    max_additions_cap: int = 1000
    max_deletions_cap: int = 1000

def calculate_pts(commit: Commit, coeffs: ScoringCoefficients) -> int:
    """
    Points = Base + capped additions * weight

    Example:
      commit.additions = 1500
      capped = min(1500, 1000) = 1000
      pts = 10 + (1000 * 1.0) = 1010
    """
    base = coeffs.commit_base
    capped_additions = min(commit.additions, coeffs.max_additions_cap)
    return int(base + (capped_additions * coeffs.additions_weight))

def calculate_reb(commit: Commit, coeffs: ScoringCoefficients) -> int:
    """
    Rebounds = Capped deletions * weight (cleanup work)

    Example:
      commit.deletions = 500
      reb = 500 * 0.6 = 300
    """
    capped_deletions = min(commit.deletions, coeffs.max_deletions_cap)
    return int(capped_deletions * coeffs.deletions_weight)

def calculate_ast(commit: Commit, coeffs: ScoringCoefficients) -> int:
    """
    Assists = Multi-file bonus (collaboration proxy)

    Example:
      commit.files_changed = 5 → ast = 5
      commit.files_changed = 2 → ast = 0
    """
    if commit.files_changed > 3:
        return coeffs.multi_file_bonus
    return 0

def calculate_blk(commit: Commit, coeffs: ScoringCoefficients) -> int:
    """
    Blocks = Fix/bug commits (defensive work)

    Detects: "fix", "bug", "hotfix", "revert" in message
    """
    message = commit.message_title.lower()
    if any(word in message for word in ['fix', 'bug', 'hotfix', 'revert']):
        return coeffs.fix_bonus
    return 0

def calculate_tov(commit: Commit, coeffs: ScoringCoefficients) -> int:
    """
    Turnovers = WIP/debug commits (negative)

    Detects: "wip", "tmp", "debug", "test" in message
    """
    message = commit.message_title.lower()
    if any(word in message for word in ['wip', 'tmp', 'debug', 'test']):
        return coeffs.wip_penalty
    return 0

def calculate_impact_score(pts, reb, ast, blk, tov) -> float:
    """
    Composite metric: weighted sum of all stats

    Formula: PTS*1.0 + REB*0.6 + AST*0.8 + BLK*1.2 + TOV*0.7
    """
    return (
        pts * 1.0 +
        reb * 0.6 +
        ast * 0.8 +
        blk * 1.2 +
        tov * 0.7
    )
```

**Aggregation Query:**
```python
def aggregate_player_stats(user_id: str, season_id: str, period_type: str):
    """
    Aggregate stats from raw commits into player_period_stats table.
    """
    commits = (
        db.query(Commit)
        .join(Repo, Commit.repo_id == Repo.id)
        .join(Season, Season.project_id == Repo.project_id)
        .filter(
            Commit.author_email.in_(
                db.query(GitIdentity.git_email).filter(GitIdentity.user_id == user_id)
            ),
            Season.id == season_id,
            Commit.commit_date >= Season.start_at,
            Commit.commit_date <= Season.end_at
        )
        .all()
    )

    coeffs = get_project_coefficients(season.project_id)

    totals = {
        'commits': len(commits),
        'additions': sum(c.additions for c in commits),
        'deletions': sum(c.deletions for c in commits),
        'pts': sum(calculate_pts(c, coeffs) for c in commits),
        'reb': sum(calculate_reb(c, coeffs) for c in commits),
        'ast': sum(calculate_ast(c, coeffs) for c in commits),
        'blk': sum(calculate_blk(c, coeffs) for c in commits),
        'tov': sum(calculate_tov(c, coeffs) for c in commits),
    }

    totals['impact_score'] = calculate_impact_score(
        totals['pts'], totals['reb'], totals['ast'], totals['blk'], totals['tov']
    )

    # Upsert into player_period_stats
    upsert_player_stats(user_id, season_id, period_type, totals)
```

#### UI Components

**Rules Page:**
```
┌──────────────────────────────────────────────────────────┐
│ 📋 Scoring Rules                                          │
├──────────────────────────────────────────────────────────┤
│ How NBA Metrics Are Calculated:                          │
│                                                           │
│ PTS (Points) = Base + Additions                          │
│   • Base: 10 points per commit                           │
│   • Additions: +1 per line added (capped at 1,000)       │
│   • Example: 1,500 lines → 10 + 1,000 = 1,010 PTS        │
│                                                           │
│ REB (Rebounds) = Deletions × 0.6                         │
│   • Rewards cleanup work                                 │
│   • Capped at 1,000 deletions                            │
│                                                           │
│ AST (Assists) = Multi-file bonus                         │
│   • +5 if commit touches >3 files                        │
│                                                           │
│ BLK (Blocks) = Fix commits                               │
│   • +15 if message contains "fix", "bug", "hotfix"       │
│                                                           │
│ TOV (Turnovers) = WIP commits                            │
│   • -10 if message contains "wip", "tmp", "debug"        │
│                                                           │
│ [Adjust Coefficients] (Commissioner only)                │
└──────────────────────────────────────────────────────────┘
```

**Score Breakdown Modal:**
```
┌────────────────────────────────────┐
│ PTS Score Breakdown — Alice        │
├────────────────────────────────────┤
│ Total PTS: 1,234                   │
│                                    │
│ Breakdown:                         │
│ • 45 commits × 10 base = 450       │
│ • 12,345 additions                 │
│   → capped at 1,000 = 1,000        │
│ • Total: 450 + 1,000 = 1,450       │
│                                    │
│ [Close]                            │
└────────────────────────────────────┘
```

#### Acceptance Criteria

- [x] "Rules" page explaining all metrics
- [x] Coefficients modifiable per project (Commissioner only)
- [x] Recalculate stats asynchronously when coefficients change
- [x] Score breakdown modal shows formula + values
- [x] Caps applied correctly (no spam commits skewing results)
- [x] Heuristics detect fix/WIP commits accurately
- [x] Impact score calculated as weighted composite

#### Edge Cases

- **Coefficient = 0:** Valid, disables that metric
- **Negative coefficients:** Allow (e.g., TOV is negative by design)
- **Recalculation:** Async job, shows progress in UI
- **Historical stats:** Preserved when coefficients change (option to recompute)

---

### Feature E: Seasons & Periods

**Priority:** Must-Have
**Timeline:** Week 5-6
**Owner:** Backend + Frontend

#### Description
Define competition timeframes (seasons) with start/end dates. Derive weekly and monthly periods automatically. Support for absences (exclude from awards).

#### User Stories

**As a Commissioner:**
- I want to create seasons, so I can structure competition into time periods
- I want one active season at a time, so players know the current competition
- I want to record absences (vacation, leave), so players aren't penalized for inactivity

**As a Player:**
- I want to see stats for the current season, so I know how I'm performing
- I want to see historical seasons, so I can track progression over time

#### Technical Implementation

**Season Entity:**
```sql
CREATE TABLE seasons (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) REFERENCES projects(id),
    name VARCHAR(255) NOT NULL,
    start_at TIMESTAMP NOT NULL,
    end_at TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'active', 'closed'
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, name),
    CHECK (end_at > start_at)
);

CREATE INDEX idx_seasons_project ON seasons(project_id);
CREATE INDEX idx_seasons_status ON seasons(status);
```

**Absence Entity:**
```sql
CREATE TABLE absences (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    season_id VARCHAR(36) REFERENCES seasons(id),
    start_at DATE NOT NULL,
    end_at DATE NOT NULL,
    reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Period Derivation:**
```python
from datetime import datetime, timedelta

def get_period_start(date: datetime, period_type: str) -> date:
    """
    Get the start date of the period containing 'date'.

    Examples:
      date = 2024-01-17 (Wednesday)
      period_type = 'week' → 2024-01-15 (Monday)
      period_type = 'month' → 2024-01-01
    """
    if period_type == 'day':
        return date.date()
    elif period_type == 'week':
        # Monday of the week
        return (date - timedelta(days=date.weekday())).date()
    elif period_type == 'month':
        return date.replace(day=1).date()
    elif period_type == 'season':
        season = get_season_for_date(date)
        return season.start_at.date()
    else:
        raise ValueError(f"Invalid period_type: {period_type}")
```

**Season Activation:**
```python
@router.post("/seasons/{season_id}/activate")
def activate_season(season_id: str, current_user = Depends(require_commissioner)):
    # Deactivate other seasons in project
    db.query(Season).filter(
        Season.project_id == season.project_id,
        Season.status == 'active'
    ).update({'status': 'closed'})

    # Activate this season
    season = db.query(Season).get(season_id)
    season.status = 'active'
    db.commit()

    return season
```

#### Acceptance Criteria

- [x] CRUD operations for seasons
- [x] Season activation (only 1 active per project)
- [x] Date validation (end > start)
- [x] Leaderboard filterable by: season, week, month
- [x] Absences exclude player from awards (configurable)
- [x] Historical seasons preserved (read-only)

#### Edge Cases

- **Overlapping seasons:** Allow (for parallel leagues)
- **No active season:** Show message, prompt Commissioner
- **Absence during award period:** Exclude from that specific award
- **Retroactive seasons:** Allow creation of past seasons

---

### Feature F: Leaderboards

**Priority:** Must-Have
**Timeline:** Week 5-6
**Owner:** Frontend + Backend

#### Description
Sortable, filterable rankings of players by any metric. Supports multiple views (global, repo-specific, period-specific) with performance optimized for large datasets.

#### User Stories

**As a Player:**
- I want to see where I rank, so I know how I'm performing vs. teammates
- I want to filter by repo, so I can see contributions to specific projects
- I want to sort by different metrics, so I can see who leads in different areas

**As a Spectator:**
- I want to view the leaderboard, so I can follow team activity
- I want to see trends (up/down arrows), so I know who's improving

#### Technical Implementation

**API Endpoint:**
```python
@router.get("/seasons/{season_id}/leaderboard")
def get_leaderboard(
    season_id: str,
    period_type: str = 'season',  # 'day', 'week', 'month', 'season'
    period_start: date | None = None,
    repo_id: str | None = None,
    sort_by: str = 'pts',
    order: str = 'desc',
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    # Build query
    query = (
        db.query(
            PlayerPeriodStats,
            User.display_name,
            User.email,
        )
        .join(User, PlayerPeriodStats.user_id == User.id)
        .filter(
            PlayerPeriodStats.season_id == season_id,
            PlayerPeriodStats.period_type == period_type
        )
    )

    if period_start:
        query = query.filter(PlayerPeriodStats.period_start == period_start)

    # Sort
    sort_column = getattr(PlayerPeriodStats, sort_by)
    if order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Paginate
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()

    # Add ranks
    ranked_items = []
    for idx, (stats, name, email) in enumerate(items):
        ranked_items.append({
            'rank': (page - 1) * limit + idx + 1,
            'player': {'id': stats.user_id, 'display_name': name, 'email': email},
            'stats': stats.dict(),
            'trend': calculate_trend(stats.user_id, period_type, period_start)
        })

    return {
        'items': ranked_items,
        'total': total,
        'page': page,
        'pages': (total + limit - 1) // limit
    }
```

**Trend Calculation:**
```python
def calculate_trend(user_id: str, period_type: str, current_period_start: date) -> str:
    """
    Compare current period to previous period.

    Returns: 'up', 'down', 'neutral'
    """
    current = get_stats(user_id, period_type, current_period_start)
    previous = get_stats(user_id, period_type, previous_period_start(current_period_start))

    if current.impact_score > previous.impact_score * 1.05:
        return 'up'
    elif current.impact_score < previous.impact_score * 0.95:
        return 'down'
    else:
        return 'neutral'
```

**Performance Optimization:**
- Pre-aggregate stats in `player_period_stats` table
- Index on `(season_id, period_type, period_start)`
- Index on each sortable column (pts, reb, etc.)
- Cache results in Redis (5min TTL)

#### UI Component

**Leaderboard Table:**
```tsx
interface LeaderboardProps {
  seasonId: string;
  periodType: 'day' | 'week' | 'month' | 'season';
}

export function Leaderboard({ seasonId, periodType }: LeaderboardProps) {
  const [sortBy, setSortBy] = useState('pts');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');

  const { data, isLoading } = useQuery({
    queryKey: ['leaderboard', seasonId, periodType, sortBy, order],
    queryFn: () => fetchLeaderboard({ seasonId, periodType, sortBy, order }),
  });

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Rank</TableHead>
          <TableHead onClick={() => toggleSort('display_name')}>Player</TableHead>
          <TableHead onClick={() => toggleSort('pts')}>PTS</TableHead>
          <TableHead onClick={() => toggleSort('reb')}>REB</TableHead>
          <TableHead onClick={() => toggleSort('ast')}>AST</TableHead>
          <TableHead>Trend</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data?.items.map((item) => (
          <TableRow key={item.player.id}>
            <TableCell>{item.rank}</TableCell>
            <TableCell>
              <Link href={`/players/${item.player.id}`}>
                {item.player.display_name}
              </Link>
            </TableCell>
            <TableCell>{item.stats.pts}</TableCell>
            <TableCell>{item.stats.reb}</TableCell>
            <TableCell>{item.stats.ast}</TableCell>
            <TableCell>
              <TrendIndicator trend={item.trend} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

#### Acceptance Criteria

- [x] Leaderboard sortable by any metric
- [x] Filterable by: season, period, repo
- [x] Performance < 300ms for 200 players, 1M commits
- [x] Pagination working (50 per page)
- [x] Trend arrows showing (up/down/neutral)
- [x] Clickable rows → player profile
- [x] Empty state: "No data yet" + CTA for Commissioner

#### Edge Cases

- **Tie scores:** Use secondary sort (commits, then alphabetically)
- **No data:** Show empty state
- **Period in future:** Show message "Period hasn't started"
- **Retired players:** Option to show/hide

---

### Feature G: Player Profiles

**Priority:** Must-Have
**Timeline:** Week 5-6
**Owner:** Frontend + Backend

#### Description
Individual player pages showing season stats, career stats, awards history, and recent commits. Includes progression graphs and links to repos.

#### User Stories

**As a Player:**
- I want a profile page with my stats, so I have a "player card"
- I want to see my progression over time, so I can track improvement
- I want to see my awards, so I can celebrate achievements

**As a Commissioner:**
- I want to view any player's profile, so I can understand their contributions

#### Technical Implementation

**API Endpoint:**
```python
@router.get("/players/{player_id}")
def get_player_profile(
    player_id: str,
    season_id: str | None = None,
    db: Session = Depends(get_db)
):
    user = db.query(User).get(player_id)
    if not user:
        raise HTTPException(404, "Player not found")

    # Current season stats
    current_season_stats = get_player_season_stats(player_id, season_id)

    # Career stats (all-time)
    career_stats = get_player_career_stats(player_id)

    # Awards
    awards = db.query(Award).filter(Award.user_id == player_id).all()

    # Recent commits
    recent_commits = (
        db.query(Commit)
        .filter(Commit.author_email.in_([gi.git_email for gi in user.git_identities]))
        .order_by(Commit.commit_date.desc())
        .limit(50)
        .all()
    )

    return {
        'id': user.id,
        'display_name': user.display_name,
        'email': user.email,
        'role': user.role,
        'status': user.status,
        'current_season_stats': current_season_stats,
        'career_stats': career_stats,
        'awards': awards,
        'recent_commits': recent_commits,
    }
```

**Weekly Trend Data:**
```python
@router.get("/players/{player_id}/stats/trend")
def get_player_trend(
    player_id: str,
    season_id: str,
    period_type: str = 'week',
    db: Session = Depends(get_db)
):
    stats = (
        db.query(PlayerPeriodStats)
        .filter(
            PlayerPeriodStats.user_id == player_id,
            PlayerPeriodStats.season_id == season_id,
            PlayerPeriodStats.period_type == period_type
        )
        .order_by(PlayerPeriodStats.period_start.asc())
        .limit(12)  # Last 12 weeks
        .all()
    )

    return [{
        'period_start': s.period_start.isoformat(),
        'pts': s.pts,
        'commits': s.commits,
        'impact_score': s.impact_score
    } for s in stats]
```

#### UI Components

**Profile Header:**
```tsx
<div className="profile-header">
  <Avatar size="lg" src={user.avatar_url} />
  <div>
    <h1>{user.display_name}</h1>
    <Badge>{user.role}</Badge>
    <Badge variant={user.status === 'active' ? 'success' : 'secondary'}>
      {user.status}
    </Badge>
  </div>
  <Button variant="outline">
    <Star /> Follow
  </Button>
</div>
```

**Stats Tabs:**
```tsx
<Tabs defaultValue="season">
  <TabsList>
    <TabsTrigger value="season">Season</TabsTrigger>
    <TabsTrigger value="career">Career</TabsTrigger>
    <TabsTrigger value="awards">Awards</TabsTrigger>
    <TabsTrigger value="repos">Repos</TabsTrigger>
  </TabsList>

  <TabsContent value="season">
    <StatsGrid stats={currentSeasonStats} />
    <TrendChart data={weeklyTrend} />
  </TabsContent>

  <TabsContent value="career">
    <StatsGrid stats={careerStats} />
    <SeasonHistory seasons={pastSeasons} />
  </TabsContent>

  <TabsContent value="awards">
    <AwardsList awards={awards} />
  </TabsContent>

  <TabsContent value="repos">
    <RepoContributions repos={repoBreakdown} />
  </TabsContent>
</Tabs>
```

**Trend Chart (Recharts):**
```tsx
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';

export function TrendChart({ data }: { data: TrendData[] }) {
  return (
    <LineChart width={600} height={300} data={data}>
      <XAxis dataKey="period_start" />
      <YAxis />
      <Tooltip />
      <Line type="monotone" dataKey="pts" stroke="#FF6B35" />
      <Line type="monotone" dataKey="commits" stroke="#004E89" />
    </LineChart>
  );
}
```

#### Acceptance Criteria

- [x] Profile accessible via leaderboard + search
- [x] Tabs: Season, Career, Awards, Repos
- [x] Graphs show weekly/monthly trend (last 12 periods)
- [x] Awards list with date and breakdown
- [x] Recent commits (50) with links to repos
- [x] Clickable metrics → breakdown modal

#### Edge Cases

- **No season stats:** Show "No activity this season"
- **New player:** Career stats = current season
- **Retired player:** Show badge, historical data preserved
- **Private profile:** Future feature (V2)

---

### Feature H: Awards & Highlights

**Priority:** Must-Have
**Timeline:** Week 7-8
**Owner:** Backend (Workers)

#### Description
Automated awards system that recognizes top performers weekly, monthly, and seasonally. "Play of the Day" highlights exceptional commits.

#### User Stories

**As a Player:**
- I want to win awards, so I feel recognized for my work
- I want to see "Play of the Day," so I can appreciate great commits

**As a Spectator:**
- I want to see highlights, so I can follow the league storyline

#### Technical Implementation

**Awards Entity:**
```sql
CREATE TABLE awards (
    id VARCHAR(36) PRIMARY KEY,
    season_id VARCHAR(36) REFERENCES seasons(id),
    period_type VARCHAR(20) NOT NULL, -- 'week', 'month', 'season'
    period_start DATE NOT NULL,
    award_type VARCHAR(50) NOT NULL, -- 'player_of_week', 'mvp', etc.
    user_id VARCHAR(36) REFERENCES users(id),
    score FLOAT NOT NULL,
    metadata_json JSONB, -- Breakdown
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(season_id, period_type, period_start, award_type)
);
```

**Awards Calculation (Celery task):**
```python
@celery_app.task
def calculate_weekly_awards():
    """
    Run every Monday at 00:00 to calculate previous week's awards.
    """
    last_week_start = datetime.now().date() - timedelta(days=7)

    active_seasons = db.query(Season).filter(Season.status == 'active').all()

    for season in active_seasons:
        # Get top player by impact score
        top_player = (
            db.query(PlayerPeriodStats)
            .filter(
                PlayerPeriodStats.season_id == season.id,
                PlayerPeriodStats.period_type == 'week',
                PlayerPeriodStats.period_start == last_week_start
            )
            .order_by(PlayerPeriodStats.impact_score.desc())
            .first()
        )

        if top_player:
            # Check absences
            is_absent = db.query(Absence).filter(
                Absence.user_id == top_player.user_id,
                Absence.start_at <= last_week_start,
                Absence.end_at >= last_week_start
            ).first()

            if not is_absent:
                # Create award
                award = Award(
                    season_id=season.id,
                    period_type='week',
                    period_start=last_week_start,
                    award_type='player_of_week',
                    user_id=top_player.user_id,
                    score=top_player.impact_score,
                    metadata_json={
                        'pts': top_player.pts,
                        'reb': top_player.reb,
                        'ast': top_player.ast,
                        'commits': top_player.commits
                    }
                )
                db.add(award)

        db.commit()
```

**Play of the Day:**
```python
@celery_app.task
def calculate_play_of_day():
    """
    Run daily at 23:00 to select best commit of the day.
    """
    today = datetime.now().date()

    active_seasons = db.query(Season).filter(Season.status == 'active').all()

    for season in active_seasons:
        commits = (
            db.query(Commit)
            .join(Repo, Commit.repo_id == Repo.id)
            .filter(
                Repo.project_id == season.project_id,
                func.date(Commit.commit_date) == today,
                Commit.is_merge == False  # Exclude merges
            )
            .all()
        )

        if not commits:
            continue

        # Score each commit
        coeffs = get_project_coefficients(season.project_id)
        scored_commits = []
        for commit in commits:
            score = (
                calculate_pts(commit, coeffs) * 1.0 +
                calculate_reb(commit, coeffs) * 0.6 +
                calculate_ast(commit, coeffs) * 0.8 +
                calculate_blk(commit, coeffs) * 1.2 -
                abs(calculate_tov(commit, coeffs)) * 0.7
            )
            scored_commits.append((commit, score))

        # Select top commit
        best_commit, best_score = max(scored_commits, key=lambda x: x[1])

        # Get author
        author_email = best_commit.author_email
        author = db.query(User).join(GitIdentity).filter(
            GitIdentity.git_email == author_email
        ).first()

        if author:
            play = PlayOfTheDay(
                date=today,
                commit_sha=best_commit.sha,
                user_id=author.id,
                score=best_score,
                metadata_json={
                    'repo_name': best_commit.repo.name,
                    'message': best_commit.message_title,
                    'additions': best_commit.additions,
                    'deletions': best_commit.deletions,
                    'files_changed': best_commit.files_changed
                }
            )
            db.add(play)
            db.commit()
```

**Award Types:**
- **Player of the Week:** Top impact score for the week
- **Player of the Month:** Top impact score for the month
- **MVP (Season End):** Top overall impact score for season
- **Most Improved:** Biggest percentage increase vs. previous season

#### Acceptance Criteria

- [x] Awards calculated automatically (Celery Beat)
- [x] Deterministic scoring (same inputs = same winner)
- [x] Score breakdown visible in metadata
- [x] Play of the Day excludes merge commits (configurable)
- [x] Absences exclude players from awards (optional)
- [x] Tiebreaker: commits, then alphabetical

#### Edge Cases

- **Tie:** Use commits as tiebreaker, then alphabetical
- **No activity:** No award issued for that period
- **Retired player wins:** Still counts (historical accuracy)
- **Recalculate awards:** Async job, deletes old awards for period

---

### Feature I: Fantasy League

**Priority:** Should-Have
**Timeline:** Week 9-10
**Owner:** Backend + Frontend

#### Description
Fantasy draft system where participants pick real players and compete based on their cumulative stats. Rosters lock before the season/period starts.

#### User Stories

**As a Commissioner:**
- I want to create a fantasy league, so participants can compete
- I want to define roster rules (min/max players), so drafts are fair

**As a Participant:**
- I want to draft players, so I can compete in fantasy
- I want to see my roster's total score, so I know my rank

#### Technical Implementation

**Fantasy Entities:**
```sql
CREATE TABLE fantasy_leagues (
    id VARCHAR(36) PRIMARY KEY,
    season_id VARCHAR(36) REFERENCES seasons(id),
    name VARCHAR(255) NOT NULL,
    roster_min INTEGER NOT NULL,
    roster_max INTEGER NOT NULL,
    lock_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE fantasy_participants (
    league_id VARCHAR(36) REFERENCES fantasy_leagues(id),
    user_id VARCHAR(36) REFERENCES users(id),
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (league_id, user_id)
);

CREATE TABLE fantasy_rosters (
    id VARCHAR(36) PRIMARY KEY,
    league_id VARCHAR(36) REFERENCES fantasy_leagues(id),
    user_id VARCHAR(36) REFERENCES users(id),
    locked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(league_id, user_id)
);

CREATE TABLE fantasy_roster_picks (
    roster_id VARCHAR(36) REFERENCES fantasy_rosters(id),
    picked_user_id VARCHAR(36) REFERENCES users(id),
    position INTEGER NOT NULL,
    PRIMARY KEY (roster_id, picked_user_id)
);
```

**Draft Logic:**
```python
@router.put("/fantasy-leagues/{league_id}/roster")
def update_roster(
    league_id: str,
    picks: List[str],  # List of user IDs
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    league = db.query(FantasyLeague).get(league_id)

    # Validate
    if league.lock_at and datetime.utcnow() > league.lock_at:
        raise HTTPException(409, "League is locked")

    if len(picks) < league.roster_min or len(picks) > league.roster_max:
        raise HTTPException(400, f"Roster must have {league.roster_min}-{league.roster_max} players")

    if len(picks) != len(set(picks)):
        raise HTTPException(400, "Duplicate picks not allowed")

    # Get or create roster
    roster = db.query(FantasyRoster).filter(
        FantasyRoster.league_id == league_id,
        FantasyRoster.user_id == current_user.id
    ).first()

    if not roster:
        roster = FantasyRoster(league_id=league_id, user_id=current_user.id)
        db.add(roster)
        db.flush()

    # Delete old picks
    db.query(FantasyRosterPick).filter(
        FantasyRosterPick.roster_id == roster.id
    ).delete()

    # Add new picks
    for position, picked_user_id in enumerate(picks):
        pick = FantasyRosterPick(
            roster_id=roster.id,
            picked_user_id=picked_user_id,
            position=position + 1
        )
        db.add(pick)

    db.commit()
    return roster
```

**Fantasy Scoring:**
```python
@router.get("/fantasy-leagues/{league_id}/leaderboard")
def get_fantasy_leaderboard(league_id: str, db: Session = Depends(get_db)):
    league = db.query(FantasyLeague).get(league_id)

    rosters = db.query(FantasyRoster).filter(
        FantasyRoster.league_id == league_id
    ).all()

    leaderboard = []
    for roster in rosters:
        total_score = 0
        for pick in roster.picks:
            player_stats = get_player_season_stats(
                pick.picked_user_id,
                league.season_id
            )
            total_score += player_stats.impact_score

        leaderboard.append({
            'participant': roster.user,
            'roster_id': roster.id,
            'total_score': total_score,
            'picks_count': len(roster.picks),
            'locked_at': roster.locked_at
        })

    leaderboard.sort(key=lambda x: x['total_score'], reverse=True)

    for rank, item in enumerate(leaderboard):
        item['rank'] = rank + 1

    return leaderboard
```

#### Acceptance Criteria

- [x] Commissioner creates fantasy league with roster rules
- [x] Participants can join league
- [x] Roster draft (simple pick list, no snake draft V1)
- [x] Roster validation (min/max, no duplicates)
- [x] Lock mechanism (changes disabled after lock_at)
- [x] Fantasy leaderboard by total score
- [x] Real-time score updates (based on player stats)

#### Edge Cases

- **Lock date passed:** Prevent roster changes
- **Player retired mid-season:** Roster keeps them, stats frozen
- **Draftable pool:** Commissioner defines (default: all active players)
- **Empty roster:** Can't lock until min picks met

---

### Feature J: Hall of Fame

**Priority:** Should-Have
**Timeline:** Week 7-8
**Owner:** Backend + Frontend

#### Description
All-time records and retired player recognition. Preserves historical data even after players leave the organization.

#### User Stories

**As a Commissioner:**
- I want to retire a player, so they don't appear in current leaderboards
- I want the Hall of Fame to show legends, so we celebrate long-term contributions

**As a Spectator:**
- I want to see all-time records, so I can appreciate the league's history

#### Technical Implementation

**Retired Status:**
```python
@router.patch("/users/{user_id}/retire")
def retire_player(
    user_id: str,
    current_user = Depends(require_commissioner),
    db: Session = Depends(get_db)
):
    user = db.query(User).get(user_id)
    user.status = 'retired'
    db.commit()
    return user
```

**Hall of Fame Query:**
```python
@router.get("/hall-of-fame")
def get_hall_of_fame(db: Session = Depends(get_db)):
    # All-time top 10
    all_time_leaders = (
        db.query(
            User.id,
            User.display_name,
            func.sum(PlayerPeriodStats.pts).label('total_pts'),
            func.sum(PlayerPeriodStats.commits).label('total_commits'),
            func.count(func.distinct(Award.id)).label('awards_count')
        )
        .join(PlayerPeriodStats, User.id == PlayerPeriodStats.user_id)
        .outerjoin(Award, User.id == Award.user_id)
        .group_by(User.id, User.display_name)
        .order_by(func.sum(PlayerPeriodStats.pts).desc())
        .limit(10)
        .all()
    )

    # Records
    records = {
        'most_commits_single_season': get_record_single_season('commits'),
        'highest_pts_single_season': get_record_single_season('pts'),
        'most_awards': get_most_awarded_player(),
        'longest_streak': get_longest_active_streak(),
    }

    # Retired legends
    retired_players = (
        db.query(User)
        .filter(User.status == 'retired')
        .order_by(User.created_at.asc())
        .all()
    )

    return {
        'all_time_leaders': all_time_leaders,
        'records': records,
        'retired_players': retired_players
    }
```

#### Acceptance Criteria

- [x] "Retired" status flag on users
- [x] Retired players excluded from active leaderboards
- [x] HOF page shows top 10 all-time + records
- [x] Historical data preserved (past seasons unchanged)
- [x] Retired player profiles still accessible

#### Edge Cases

- **Un-retire:** Allow Commissioner to reactivate (rare)
- **Partial season retired:** Stats up to retirement date count
- **Future seasons:** Retired players not shown

---

### Feature K: All-Time Rankings

**Priority:** Should-Have
**Timeline:** Week 7-8 (Enhancement)
**Owner:** Backend + Frontend

#### Description
Comprehensive all-time leaderboards across all seasons, supporting multiple metrics and filters. Unlike the Hall of Fame's top 10, this provides full rankings with pagination.

#### User Stories

**As a Player:**
- I want to see my all-time rank, so I know where I stand historically
- I want to compare all-time stats by different metrics (PTS, commits, impact score)

**As a Spectator:**
- I want to browse complete all-time rankings, so I can see all players' historical performance
- I want to filter by project or metric, so I can analyze specific aspects

#### Technical Implementation

**All-Time Leaderboard Endpoint:**
```python
@router.get("/leaderboard/all-time")
def get_all_time_leaderboard(
    project_id: str | None = None,
    sort_by: str = 'impact_score',  # 'pts', 'commits', 'impact_score', etc.
    order: str = 'desc',
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    # Aggregate all PlayerPeriodStats across all seasons
    query = (
        db.query(
            User.id,
            User.display_name,
            User.email,
            func.sum(PlayerPeriodStats.pts).label('total_pts'),
            func.sum(PlayerPeriodStats.commits).label('total_commits'),
            func.sum(PlayerPeriodStats.impact_score).label('total_impact_score'),
            func.sum(PlayerPeriodStats.additions).label('total_additions'),
            func.sum(PlayerPeriodStats.deletions).label('total_deletions'),
            func.count(func.distinct(PlayerPeriodStats.season_id)).label('seasons_count')
        )
        .join(PlayerPeriodStats, User.id == PlayerPeriodStats.user_id)
        .group_by(User.id, User.display_name, User.email)
    )

    # Filter by project if specified
    if project_id:
        query = query.join(Season).filter(Season.project_id == project_id)

    # Sort and paginate
    query = query.order_by(desc(getattr(PlayerPeriodStats, sort_by)))
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()

    # Add ranks
    ranked_items = []
    for idx, item in enumerate(items):
        ranked_items.append({
            'rank': (page - 1) * limit + idx + 1,
            'user_id': item.id,
            'display_name': item.display_name,
            'email': item.email,
            'total_pts': item.total_pts,
            'total_commits': item.total_commits,
            'total_impact_score': item.total_impact_score,
            'total_additions': item.total_additions,
            'total_deletions': item.total_deletions,
            'seasons_count': item.seasons_count
        })

    return {
        'items': ranked_items,
        'total': total,
        'page': page,
        'pages': (total + limit - 1) // limit,
        'sort_by': sort_by,
        'order': order
    }
```

**Multiple Metric Support:**
- Sort by: PTS, commits, impact_score, additions, deletions, REB, AST, BLK
- Include career averages (per season, per commit)
- Show active vs retired status

#### Acceptance Criteria

- [ ] All-time leaderboard endpoint with pagination
- [ ] Sortable by any metric (PTS, commits, impact_score, etc.)
- [ ] Filterable by project
- [ ] Shows total stats + season count
- [ ] Includes both active and retired players
- [ ] Performance optimized for large datasets
- [ ] Ranks calculated correctly with ties handling

#### Edge Cases

- **Ties:** Use secondary sort (commits, then alphabetical)
- **No data:** Show empty state
- **Retired players:** Include in all-time (historical accuracy)
- **Multiple projects:** Filter or aggregate across all

---

## Phase 2: Enhancement Features (V2.0)

### Search & Discovery
- Full-text search on commits (messages, authors)
- Search players by name/email
- Filter highlights by date/repo

### Notifications
- Slack integration for awards and highlights
- Email digests (weekly recap)
- Commissioner alerts (sync errors)

### Teams & Squads
- Group players into teams
- Team leaderboards
- Team-based awards

### Anti-Bias Improvements
- Dynamic caps based on repo norms
- "Garbage time" detection
- Advanced merge handling

### SSO
- SAML/OIDC support for enterprise

---

## Phase 3: Advanced Features (V3.0)

### AI Commit Coach
- Analyze commit message quality
- Suggest improvements (conventional commits)
- Detect WIP commits

### Platform Integrations
- GitHub/GitLab/Bitbucket PRs and reviews
- Jira/Linear issue linkage
- Slack/Teams bot

### Impact Estimation
- Code ownership graphs
- Critical path detection
- Contribution weighting by importance

---

**For implementation timeline, see [ROADMAP.md](./ROADMAP.md)**

**For technical details, see [ARCHITECTURE.md](./ARCHITECTURE.md)**
