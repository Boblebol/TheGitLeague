# 🗺️ Product Roadmap

This document outlines the development roadmap for **The Git League**.

---

## 📋 Table of Contents

- [Vision & Timeline](#vision--timeline)
- [Phase 1: MVP (Weeks 1-12)](#phase-1-mvp-weeks-1-12)
- [Phase 2: Enhancement (Months 3-6)](#phase-2-enhancement-months-3-6)
- [Phase 3: Advanced Features (Months 6-12)](#phase-3-advanced-features-months-6-12)
- [Feature Prioritization](#feature-prioritization)
- [Success Metrics](#success-metrics)

---

## 🎯 Vision & Timeline

**Mission:** Transform Git activity into an engaging NBA-style league that celebrates all contributions, not just visible features.

**Timeline Overview:**
- **Phase 1 (Weeks 1-12):** MVP - Core functionality, self-hosted deployment
- **Phase 2 (Months 3-6):** Enhancement - Advanced features, integrations
- **Phase 3 (Months 6-12):** Scale - AI features, enterprise capabilities

---

## 🚀 Phase 1: MVP (Weeks 1-12)

**Goal:** Launch a self-hosted, functional Git League with core features.

**Target:** Solo developer or small team, 12 weeks to v1.0

### Week 1-2: Foundation ✅

**Infrastructure & Setup**

- [x] **Project initialization**
  - Monorepo structure (frontend + backend)
  - Docker Compose configuration (PostgreSQL, Redis)
  - CI/CD pipeline (GitHub Actions)
  - Development environment setup

- [x] **Frontend skeleton**
  - Next.js 14 with App Router
  - shadcn/ui component library integration
  - Global layout and navigation shell
  - Authentication UI (login/magic link)

- [x] **Backend skeleton**
  - FastAPI application structure
  - OpenAPI documentation
  - RBAC middleware
  - Database connection pooling

- [x] **Database schema**
  - Initial Alembic migrations
  - Core models: Users, Projects, Repos, GitIdentities

**Deliverables:**
- Running development environment
- Basic authentication flow
- Database migrations working

---

### Week 3-4: Git Ingestion Core 🧱

**Git Integration & Data Pipeline**

- [ ] **Repository configuration**
  - CRUD operations for repos
  - Support for local, SSH, HTTPS repositories
  - Encrypted credentials storage (Fernet)
  - Environment variable management

- [ ] **Worker infrastructure**
  - Celery/RQ setup with Redis
  - Queue monitoring (Flower)
  - Task retry logic with exponential backoff
  - Error handling and logging

- [ ] **Git ingestion pipeline**
  - Incremental commit extraction
  - Idempotent processing (no duplicates)
  - Batch processing (1000 commits/batch)
  - Metadata extraction: SHA, author, date, message, stats

- [ ] **Sync monitoring**
  - Sync status tracking (healthy/syncing/error)
  - Structured logs (JSON format)
  - Sync history and error reporting UI
  - Last sync timestamp and SHA tracking

- [ ] **First aggregation**
  - Raw commits → player_period_stats table
  - Basic stats calculation (commits, additions, deletions)

**Deliverables:**
- Successfully ingest 100k commits in < 5 minutes
- Commissioner can add/sync repos via UI
- Error logs accessible and actionable

**Technical Challenges:**
- Handling force-pushes and Git history rewrites
- Performance optimization for large repos
- Secure credential storage

---

### Week 5-6: League Engine 🏀

**NBA Metrics & Stats System**

- [ ] **Seasons management**
  - CRUD operations for seasons
  - Season activation (one active per project)
  - Date range validation
  - Season status workflow (draft → active → closed)

- [ ] **NBA metrics calculation**
  - Configurable scoring coefficients
  - PTS: additions (capped) + commit base
  - REB: deletions (capped) × weight
  - AST: multi-file commits bonus
  - BLK: fix/bug commits detection (regex)
  - TOV: WIP/debug commits penalty
  - Impact score: composite metric

- [ ] **Scoring configuration UI**
  - Commissioner can adjust coefficients
  - Real-time preview of score changes
  - "Rules" page explaining calculations
  - Coefficient validation and limits

- [ ] **Leaderboards**
  - Season/week/month views
  - Sortable by any metric
  - Filterable by repo
  - Performance: < 300ms for 200 players
  - Pagination support

- [ ] **Player profiles (basic)**
  - Current season stats
  - Career stats (all-time)
  - Commits list (recent 50)
  - Ranking position

**Deliverables:**
- Functional leaderboard with filtering
- Player profiles with season/career tabs
- Commissioner can adjust scoring rules
- Transparent score calculation visible to users

**Technical Challenges:**
- Efficient aggregation queries (pre-compute stats)
- Database indexes for performance
- Handling score recalculation on coefficient changes

---

### Week 7-8: Awards & Highlights ✨

**Automated Recognition System**

- [ ] **Awards calculation**
  - Player of the Week (automated job)
  - Player of the Month (automated job)
  - MVP (season end)
  - Most Improved (season N vs N-1 comparison)
  - Score breakdown and metadata

- [ ] **Play of the Day**
  - Daily job to select best commit
  - Composite score calculation
  - Exclusion of merge commits (configurable)
  - Commit detail card UI with stats breakdown

- [ ] **Awards display**
  - Awards page with filters (type, period, player)
  - Award cards with winner and score
  - Player profiles show awards history
  - Award notifications (basic)

- [ ] **Hall of Fame (basic)**
  - All-time aggregates
  - Top 10 all-time leaders
  - Career records (most commits, highest PTS, etc.)
  - Retired players list

- [ ] **Retired players**
  - "Retired" status flag
  - Exclude from current leaderboards
  - Preserve historical data
  - HOF eligibility

**Deliverables:**
- Automated weekly/monthly awards
- Daily "Play of the Day" highlights
- Hall of Fame page with records
- Awards visible on player profiles

**Technical Challenges:**
- Deterministic award calculation
- Handling ties (tiebreaker rules)
- Excluding absences from awards (optional)

---

### Week 9-10: Fantasy League 🎮

**Fantasy Draft System**

- [ ] **Fantasy league entity**
  - CRUD operations (Commissioner only)
  - League configuration: roster min/max, lock date
  - Participant management
  - Draftable player pool definition

- [ ] **Draft system (V1 simple)**
  - Pick list draft (not snake draft for V1)
  - Roster validation (min/max players)
  - Duplicate picks prevention
  - Roster locking mechanism

- [ ] **Fantasy scoring**
  - Real-time roster score calculation
  - Individual player contribution to roster
  - Leaderboard for fantasy participants
  - Period-based scoring (week/month/season)

- [ ] **Fantasy UI**
  - League creation wizard
  - Draft interface with player selection
  - My Roster page (edit/lock)
  - Fantasy leaderboard
  - Lock date countdown

**Deliverables:**
- Commissioner can create fantasy leagues
- Participants can draft and lock rosters
- Fantasy leaderboard updates in real-time
- Lock mechanism prevents changes after deadline

**Technical Challenges:**
- Real-time score updates (WebSocket in future)
- Concurrent roster updates (locking)
- Historical roster tracking

---

### Week 11-12: Hardening & OSS Polish 🧼

**Production Readiness**

- [ ] **Testing**
  - Backend API tests (pytest): 80%+ coverage
  - Frontend component tests (Jest): 70%+ coverage
  - Integration tests (Docker Compose test environment)
  - End-to-end smoke tests

- [ ] **Demo data**
  - Seed script with realistic dataset
  - Multiple repos, players, seasons
  - Pre-calculated awards and fantasy league
  - "Demo mode" for easy evaluation

- [ ] **Rate limiting**
  - Redis-based rate limiter
  - API: 100 req/min per user
  - Auth endpoints: 5 req/min
  - Configurable limits per endpoint

- [ ] **Audit system**
  - User approval logs
  - Configuration changes tracking
  - Sync operation logs
  - Commissioner actions audit trail

- [ ] **Observability**
  - JSON structured logging
  - Health check endpoints
  - Metrics collection (Prometheus-ready)
  - Error tracking integration hooks

- [x] **Python Client (gitleague-client)**
  - ✅ Core CLI application with Git scanning and API integration
  - ✅ YAML-based configuration system
  - ✅ Batch commit synchronization
  - ✅ Dry-run mode for preview
  - ✅ SSH and HTTPS authentication support
  - ✅ Retry logic with exponential backoff
  - 🔄 PyPI publication (in progress) — See [PYPI_PUBLISH_GUIDE.md](./PYPI_PUBLISH_GUIDE.md)

- [ ] **Documentation polish**
  - [x] Python Client Installation Guide — See [CLIENT_INSTALLATION_GUIDE.md](./CLIENT_INSTALLATION_GUIDE.md)
  - [x] Python Client README with examples
  - [x] PyPI Publication Guide — See [PYPI_PUBLISH_GUIDE.md](./PYPI_PUBLISH_GUIDE.md)
  - README with screenshots
  - Self-hosting guide (Dokploy, Docker Compose)
  - Environment variables documentation
  - Troubleshooting guide
  - API examples and Postman collection

- [ ] **CI/CD**
  - GitHub Actions workflows
  - Lint + type check + tests
  - Docker image build and push
  - Security scanning (Snyk, Trivy)
  - Release tagging automation

**Deliverables:**
- v1.0.0 release ready for production
- Comprehensive documentation
- Demo environment anyone can spin up
- CI/CD pipeline fully automated

**Technical Challenges:**
- Achieving test coverage targets
- Demo data generation (realistic but fictional)
- Docker image optimization (size, layers)

---

## 🎨 Phase 2: Enhancement (Months 3-6)

**Goal:** Improve UX, add integrations, and enhance anti-bias features.

### Month 3-4: UX & Integrations

#### Search & Discovery (S)
- [ ] **Full-text search**
  - Search commits by message content
  - Search players by name/email
  - Search plays of the day
  - Elasticsearch or PostgreSQL FTS

#### Notifications (M)
- [ ] **Slack integration**
  - Weekly recap messages
  - Award announcements
  - Play of the day notifications
  - Leaderboard updates

- [ ] **Email notifications**
  - Award emails with personalized content
  - Weekly digest for players
  - Commissioner alerts (sync errors, etc.)
  - Configurable notification preferences

#### Teams & Squads (M)
- [ ] **Team entity**
  - Group players into teams/squads
  - Team leaderboards
  - Team-based awards
  - Inter-team competition

#### Export & BI (S)
- [ ] **Data export**
  - CSV export for stats
  - JSON API for external tools
  - Webhook support for integrations
  - Custom report generation

### Month 5-6: Anti-Bias & Quality

#### Advanced Anti-Bias (M)
- [ ] **Dynamic caps**
  - Adaptive caps based on repository norms
  - Outlier detection and capping
  - "Garbage time" detection (low-value commits)
  - Configurable exclusion rules

- [ ] **Smart merge handling**
  - Detect merge vs. squash commits
  - Exclude merge commits from scoring (optional)
  - Rebase detection
  - Contributor attribution for merged PRs

#### Seasons Narratives (S)
- [ ] **Season themes**
  - Commissioner can set season theme/name
  - Season recap generation (automated)
  - Milestone tracking (10k commits, etc.)
  - Season storylines and highlights

#### SSO (L)
- [ ] **Enterprise SSO**
  - SAML support
  - OIDC/OAuth2 integration
  - Google Workspace, Okta, Auth0
  - Role mapping from SSO provider

**Deliverables:**
- Slack/Email notifications working
- Teams feature for multi-squad orgs
- Advanced scoring fairness
- SSO for enterprise deployments

---

## 🤖 Phase 3: Advanced Features (Months 6-12)

**Goal:** AI-powered features, advanced analytics, enterprise scale.

### Month 7-9: AI & Intelligence

#### Commit Quality Coach (L)
- [ ] **AI-powered suggestions**
  - Analyze commit message quality
  - Suggest improvements (conventional commits)
  - Detect WIP commits and recommend squashing
  - Code convention enforcement hints

#### Auto-Clustering (M)
- [ ] **Feature detection**
  - Group commits by feature using embeddings
  - Self-hosted embedding model (no external API)
  - Auto-tagging commits by area (frontend, backend, etc.)
  - Contribution heatmaps by module

#### Impact Estimation (L)
- [ ] **Code ownership**
  - Detect module ownership from commit history
  - Critical path detection (high-impact files)
  - Contribution weight by importance
  - Ownership graphs and visualization

### Month 10-12: Enterprise & Integrations

#### Platform Integrations (M/L)
- [ ] **GitHub/GitLab/Bitbucket**
  - Pull request metrics integration
  - Code review stats (reviews given/received)
  - Issue linkage (commits → issues)
  - PR merge time tracking

- [ ] **Jira/Linear integration**
  - Link commits to tickets
  - Story points correlation
  - Sprint-based stats
  - Ticket completion metrics

- [ ] **Slack/Teams deep integration**
  - Interactive slash commands
  - Real-time leaderboard in channels
  - Award announcements with reactions
  - Bot for stats queries

#### Semi-Automated Awards (M)
- [ ] **Award nomination system**
  - AI proposes award nominees
  - Commissioner reviews and approves
  - Internal voting for team awards
  - Custom award types

**Deliverables:**
- AI commit coach (self-hosted model)
- Deep platform integrations (GitHub, Jira)
- Advanced ownership and impact tracking
- Interactive Slack/Teams bot

---

## 📊 Feature Prioritization

### MoSCoW Framework

**Must-Have (V1)**
- ✅ Git ingestion (multi-repo)
- ✅ NBA metrics calculation
- ✅ Leaderboards & player profiles
- ✅ Seasons management
- ✅ Awards (automated)
- ✅ Fantasy league (basic)
- ✅ RBAC (Commissioner, Player, Spectator)
- ✅ Self-hosted deployment

**Should-Have (V2)**
- 🔄 Notifications (Slack, Email)
- 🔄 Teams/Squads
- 🔄 Advanced anti-bias
- 🔄 Search functionality
- 🔄 SSO (SAML/OIDC)
- 🔄 Export/BI tools

**Could-Have (V3)**
- 💡 AI commit coach
- 💡 Auto-clustering
- 💡 Platform integrations (GitHub, Jira)
- 💡 Impact estimation
- 💡 Interactive bots

**Won't-Have (Out of Scope)**
- ❌ Real-time code analysis (static analysis)
- ❌ Code quality metrics (complexity, coverage) — use dedicated tools
- ❌ Project management features (task tracking, sprints) — use Jira/Linear
- ❌ CI/CD integration — out of scope for V1-V3

---

## 📈 Success Metrics

### Week 1 Post-Launch (v0.1)
- **GitHub Stars:** 200+
- **Real Installs:** 20+ (tracked via issues/discussions)
- **Feedback:** 5+ comments on scoring coefficients
- **Documentation:** < 1 hour "time to first leaderboard"

### Month 1 Post-Launch (v1.0)
- **GitHub Stars:** 1,000+
- **Real Installs:** 100+
- **Contributors:** 10+ external PRs/docs contributions
- **Engagement:** 50%+ retention (weekly active sync)

### Month 3 Post-Launch
- **GitHub Stars:** 3,000+
- **Real Installs:** 300+
- **Feature Requests:** 3+ repeated requests (signal for roadmap)
- **Retention:** 50%+ of installs have weekly sync activity
- **Community:** Active discussions forum (20+ threads/week)

### Success Indicators (Qualitative)
- **Pain Point Solved:** Teams report higher engagement and fun
- **Recognition Fairness:** Players feel cleanup/reviews are valued
- **Enterprise Adoption:** 5+ companies with >50 developers using it
- **Open Source Health:** Regular contributions, active maintainers

---

## 🔄 Iteration & Feedback Loops

### User Feedback Channels
1. **GitHub Issues** — Bug reports, feature requests
2. **GitHub Discussions** — Questions, ideas, show & tell
3. **Discord/Slack** (future) — Real-time community support
4. **User Interviews** — Monthly calls with active users

### Release Cadence
- **Major releases (X.0.0):** Every 3-4 months
- **Minor releases (X.Y.0):** Every 4-6 weeks
- **Patch releases (X.Y.Z):** As needed for bugs

### Backward Compatibility
- Database migrations always include rollback
- API versioning for breaking changes (/api/v2)
- Deprecation warnings 2 releases before removal

---

## 🌍 Go-To-Market Strategy

### Target Channels
1. **Show HN (Hacker News)** — Launch announcement
2. **Reddit** — r/selfhosted, r/devops, r/programming, r/opensource
3. **Dev.to / Medium** — "How I turned Git into an NBA league" article
4. **Twitter/X** — Engineering influencers
5. **Dev communities** — Discord servers, Slack workspaces

### Positioning
- **Tagline:** "Turn your Git into an NBA season"
- **Angle:** Self-hosted + fun + explainable metrics
- **Differentiation:** Not "productivity tracking" — it's a league for celebration

### Content Marketing
- Blog posts on scoring methodology
- Case studies from early adopters
- Video walkthroughs and demos
- Integration guides (GitHub, GitLab, Slack)

---

## 🛠️ Technical Debt Management

### Continuous Refactoring
- **Code reviews** enforce quality standards
- **Quarterly refactor sprints** to address tech debt
- **Performance benchmarks** run in CI

### Known Trade-offs (V1)
- **Heuristic-based scoring** — Good enough for V1, AI in V3
- **Simple draft system** — Snake draft deferred to V2
- **PostgreSQL FTS** — Elasticsearch can be added later if needed

---

## 📅 Release Schedule

### Backend & Frontend Releases

| Version | Target Date | Key Features |
|---------|-------------|--------------|
| **v0.1.0** | Week 6 | Git ingestion + basic stats |
| **v0.5.0** | Week 9 | Leaderboards + awards |
| **v1.0.0** | Week 12 | Fantasy league + production ready |
| **v1.5.0** | Month 4 | Notifications + teams |
| **v2.0.0** | Month 6 | Anti-bias + SSO |
| **v3.0.0** | Month 12 | AI features + deep integrations |

### Client Releases

| Version | Status | Installation |
|---------|--------|--------------|
| **v0.1.0** | 🟡 Ready for PyPI | `pip install gitleague-client` (once published) |

---

## 🐍 Python Client (gitleague-client) Status

### Current State
- ✅ **Development Complete** — Core CLI fully functional
- ✅ **Tested** — 27 unit tests with 85%+ coverage
- ✅ **Documentation** — Complete README and API docs
- 🔄 **PyPI Publication** — Steps ready, awaiting token setup

### What's Included
- Push-based Git commit synchronization
- YAML configuration with multiple auth methods
- Batch processing (1-1000 commits per request)
- Retry logic with exponential backoff
- Dry-run mode for safe previewing
- Full CLI with `init`, `test`, and `sync` commands

### How to Get Started

**Installation:**
```bash
pip install gitleague-client
gitleague-client init  # Interactive setup
gitleague-client sync --config repos.yaml  # Start syncing
```

**Full Guides:**
1. 📖 [Client Installation Guide](./CLIENT_INSTALLATION_GUIDE.md) — Complete setup walkthrough
2. 🚀 [PyPI Publication Guide](./PYPI_PUBLISH_GUIDE.md) — How to publish to PyPI
3. 📚 [Client README](./gitleague-client/README.md) — Detailed API and configuration

---

**Next Steps:**
1. Follow [DEVELOPMENT.md](./DEVELOPMENT.md) to set up your environment
2. Install the Python client: [CLIENT_INSTALLATION_GUIDE.md](./CLIENT_INSTALLATION_GUIDE.md)
3. Publish to PyPI: [PYPI_PUBLISH_GUIDE.md](./PYPI_PUBLISH_GUIDE.md)
4. Check [FEATURES_SUMMARY.md](./FEATURES_SUMMARY.md) for feature-by-feature breakdown
5. Join discussions on GitHub to shape the roadmap

**Your feedback shapes this roadmap!** 🏀
