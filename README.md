# 🏀 The Git League

> Turn your Git activity into an NBA season — stats, leaderboards, awards, and fantasy league.
>
> Created by [Alexandre Enouf](https://alexandre-enouf.fr) | [LinkedIn](https://fr.linkedin.com/in/alexandre-enouf-47834990) | [AI Fabrik](https://aifabrik.ovh)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Self-Hosted](https://img.shields.io/badge/deployment-self--hosted-blue)](https://github.com/Boblebol/TheGitLeague)
[![Open Source](https://img.shields.io/badge/open-source-green)](https://github.com/Boblebol/TheGitLeague)

**The Git League** transforms your team's Git commits into an engaging NBA-style competition with:
- 📊 **NBA-inspired stats** (PTS, REB, AST, BLK, STL, TOV)
- 🏆 **Automated awards** (Player of the Week/Month, MVP, Most Improved)
- 🎮 **Fantasy league** with draft system
- 🎯 **Play of the Day** highlights
- 🏛️ **Hall of Fame** for retired players
- 🔒 **100% self-hosted** — your code never leaves your infrastructure

---

## 🎯 Why The Git League?

### Problems Solved
- **No engaging visibility** into team contributions — raw Git logs are boring and don't drive engagement
- **Biased recognition** — only "visible" features get celebrated, missing cleanup, reviews, and infrastructure work
- **Hard to animate teams** — no seasons, no rhythm, no storyline
- **Multi-project chaos** — contributions scattered across repos with no unified view
- **Privacy requirements** — need a tool that doesn't push code data to external SaaS

### Who It's For
- **Engineering Managers / Tech Leads** ("Commissioners") — animate, measure, celebrate, structure seasons
- **Developers** ("Players") — track stats, earn awards, get recognized
- **Stakeholders** ("Spectators") — follow progress without writing code

---

## ✨ Features (V1 MVP)

### Core Features
- ✅ **Multi-repo ingestion** — Connect multiple Git repositories (local, SSH, HTTPS)
- ✅ **NBA-style metrics** — Transparent, configurable scoring system
- ✅ **Seasons & periods** — Structure competition with seasons, weeks, and months
- ✅ **Role-based access** — Commissioner, Player, Spectator roles with proper RBAC
- ✅ **Leaderboards** — Sortable rankings by any metric, filterable by repo/period
- ✅ **Player profiles** — Individual stats, career progression, awards history
- ✅ **Automated awards** — Player of Week/Month, MVP, Most Improved
- ✅ **Play of the Day** — Highlight the best commit each day
- ✅ **Fantasy league** — Draft players and compete based on their real stats
- ✅ **Hall of Fame** — Honor retired players and preserve history

### Enterprise-Ready
- 🔐 **Self-hosted** — Docker Compose deployment, no external dependencies
- 🔒 **Privacy-first** — Only metadata stored (no source code)
- 🎛️ **Configurable scoring** — Adjust coefficients to match your team culture
- 📝 **Audit trails** — Track who approved whom, rule changes, sync operations
- 🚀 **Performant** — Handles millions of commits efficiently

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git repositories to analyze (local or remote)

### Installation

```bash
# Clone the repository
git clone https://github.com/Boblebol/TheGitLeague.git
cd TheGitLeague

# Copy environment template
cp .env.example .env

# Edit configuration (database, secrets, etc.)
nano .env

# Start the stack
docker-compose up -d

# Access the application
open http://localhost:3000
```

### First Setup (Commissioner)

1. **Create your account** — First user becomes Commissioner
2. **Create a project** — Settings → Projects → New Project
3. **Add repositories** — Configure repos with remote URLs and sync frequency
4. **Run initial sync** — Sync Now to ingest commit history
5. **Create a season** — Define start/end dates and activate
6. **Configure scoring rules** — Adjust NBA metric coefficients
7. **Invite players** — Email invitations with automatic identity matching

---

## 🐍 Python Client (Push Commits)

### What is the gitleague-client?

A lightweight Python package that commissioners and developers can use to **push commits directly to The Git League** from their local machines. No pull-based Celery sync — just a simple CLI tool that extracts commits from your Git repos and submits them via API.

### Key Benefits
- 🔐 **PAT tokens stay local** — GitHub/GitLab tokens never leave your machine
- ⚡ **Fast & efficient** — Incremental syncing with deduplication
- 🎯 **Simple configuration** — YAML-based setup
- 🔄 **Batch processing** — Push multiple repos and thousands of commits in one command
- 🧪 **Dry-run mode** — Preview what will be synced before sending

### Installation

```bash
# Via pip (when published to PyPI)
pip install gitleague-client

# Or from source
git clone https://github.com/Boblebol/TheGitLeague.git
cd TheGitLeague/gitleague-client
pip install -e .
```

### Quick Start

#### 1. Initialize Configuration
```bash
gitleague-client init
```
This creates a `repos.yaml` file with your API key and Git repos.

#### 2. Validate Setup
```bash
gitleague-client test --config repos.yaml
```
Verifies that repositories are accessible and API key is valid.

#### 3. Sync Commits
```bash
gitleague-client sync --config repos.yaml
```
Pushes all commits to The Git League. Add `--dry-run` to preview first.

### Example Configuration (repos.yaml)

```yaml
api:
  url: http://localhost:8000
  key: tgl_xxxxxxxxxxxxx_yyyyyyyyyyyyy

repositories:
  - name: "backend"
    path: /home/dev/projects/my-backend

  - name: "frontend"
    path: /home/dev/projects/my-frontend

  - name: "infra"
    path: /home/dev/projects/infrastructure
```

### Full Documentation

👉 See [**gitleague-client README**](./gitleague-client/README.md) for complete documentation including:
- Authentication setup
- Configuration options
- Batch processing
- Error handling
- Contributing to the client

---

## 📖 Documentation

- [**Landing Page**](https://github.com/Boblebol/TheGitLeague_Landing) — Modern, responsive landing page with project showcase
- [**Python Client Guide**](./gitleague-client/README.md) — Installation, configuration, and usage of the CLI tool
- [**Backend Setup**](./backend/README.md) — Backend API, database, and services documentation
- [**Development Guide**](./DEVELOPMENT.md) — Setup dev environment, architecture, stack
- [**Email Setup Guide**](./EMAIL_SETUP.md) — Configure email providers for magic link authentication
- [**Security Audit**](./SECURITY.md) — Security measures, vulnerabilities, and recommendations
- [**Contributing**](./CONTRIBUTING.md) — How to contribute to the project
- [**Architecture**](./ARCHITECTURE.md) — Technical design and data models
- [**API Specification**](./API_SPEC.md) — REST API endpoints and schemas
- [**Testing Documentation**](./backend/TESTING.md) — Backend test suite and coverage (164 tests)
- [**Deployment Guide**](./DEPLOYMENT.md) — Multi-platform deployment instructions
- [**Accessibility**](./ACCESSIBILITY.md) — WCAG 2.1 Level AA compliance
- [**FAQ**](./FAQ.md) — Frequently asked questions and troubleshooting
- [**Open Source Readiness**](./OPEN_SOURCE_READINESS.md) — Audit report and open-source certification
- [**PRD (Product Requirements)**](./Base%20doc#PRD) — Full product vision and features
- [**UX Guidelines**](./Base%20doc#UX_GUIDELINES) — Design principles and flows
- [**Roadmap**](./Base%20doc#ROADMAP_AND_GTM) — Feature timeline and go-to-market

---

## 🛠️ Tech Stack

### Frontend
- **Next.js** (App Router) + TypeScript
- **Tailwind CSS** + shadcn/ui components
- **TanStack Query** for data fetching
- **Recharts** for visualizations

### Backend
- **FastAPI** (Python) — REST API with OpenAPI
- **PostgreSQL** — Primary database
- **Redis** — Caching and job queue
- **Celery/RQ** — Background workers for Git ingestion

### Deployment
- **Docker Compose** — Local and production deployment
- **Dokploy** compatible — Easy enterprise deployment
- **Alembic** — Database migrations

---

## 🎮 How It Works

### 1. Git Ingestion
The Git League connects to your repositories and extracts commit metadata:
- SHA, author, committer, date, message
- Additions, deletions, files changed
- Branch and parent commits

**Privacy:** Only metadata is stored — never source code.

### 2. NBA Metrics Calculation
Commits are transformed into basketball stats:

- **PTS (Points)** — Based on additions (capped) + weighted commits
- **REB (Rebounds)** — Deletions/cleanup work (capped)
- **AST (Assists)** — Multi-file commits (collaboration proxy)
- **BLK (Blocks)** — Reverts and bug fixes (detected via message heuristics)
- **STL (Steals)** — (Reserved for future features)
- **TOV (Turnovers)** — WIP/debug commits or excessive churn

All coefficients are **configurable** and **transparent**.

### 3. Leaderboards & Awards
- Automated calculation of rankings and awards
- Periods: daily, weekly, monthly, seasonal, all-time
- Filters by repo, role, absence periods

### 4. Fantasy League
- Commissioner creates league and defines draftable pool
- Participants pick 1-5 players (roster)
- Scoring based on real player stats during the season
- Lock rosters before season starts

---

## 🏗️ Project Structure

```
TheGitLeague/
├── frontend/          # Next.js application
│   ├── src/
│   │   ├── app/       # App Router pages
│   │   ├── components/# React components
│   │   └── lib/       # Utilities and API client
│   └── package.json
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/       # API routes
│   │   ├── models/    # SQLAlchemy models
│   │   ├── workers/   # Celery tasks
│   │   └── core/      # League engine logic
│   └── requirements.txt
├── docker-compose.yml # Full stack orchestration
├── alembic/           # Database migrations
└── docs/              # Additional documentation
```

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for:
- Code of conduct
- Development workflow
- Pull request process
- Coding standards

---

## 🗺️ Roadmap

### Phase 1 (MVP) — ✅ Current Focus
- Core ingestion + stats + leaderboards
- Awards + Play of the Day
- Fantasy league (simple draft)
- Self-hosted deployment

### Phase 2 (3-6 months)
- Advanced anti-bias (dynamic caps, garbage time detection)
- Teams/Squads support
- Notifications (Slack, Email)
- SSO (SAML/OIDC)
- Enhanced search

### Phase 3 (6-12 months)
- AI-powered commit quality coach
- Impact estimation (critical modules)
- Code ownership integration
- Advanced integrations (GitHub, GitLab, Jira)

See full [Roadmap](./Base%20doc#ROADMAP_AND_GTM) for details.

---

## 📊 Performance Targets

- **Ingestion:** 100k commits < 5 minutes
- **Leaderboards:** < 300ms for 200 players / 1M commits
- **Recompute:** Async jobs with progress tracking

---

## 🔒 Security & Privacy

- ✅ **No source code stored** — only commit metadata
- ✅ **Encrypted secrets** — Repository credentials encrypted at rest
- ✅ **RBAC enforcement** — Role-based access control on all endpoints
- ✅ **Audit logs** — Track approvals, rule changes, sync operations
- ✅ **Self-hosted** — Complete control over your data
- 📋 **Security Audit** — See [SECURITY.md](./SECURITY.md) for detailed security analysis and recommendations

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](./LICENSE) file for details.

---

## 🌟 Support

- **GitHub Issues:** [Report bugs or request features](https://github.com/Boblebol/TheGitLeague/issues)
- **Discussions:** [Ask questions and share ideas](https://github.com/Boblebol/TheGitLeague/discussions)
- **Documentation:** [Full docs](./docs/)

---

## 👨‍💻 About the Creator

**Alexandre Enouf** is a full-stack developer and AI enthusiast passionate about building innovative solutions.

- 🌐 **Website:** [alexandre-enouf.fr](https://alexandre-enouf.fr)
- 💼 **LinkedIn:** [linkedin.com/in/alexandre-enouf-47834990](https://fr.linkedin.com/in/alexandre-enouf-47834990)
- 🤖 **AI Projects:** [aifabrik.ovh](https://aifabrik.ovh) - Explore more AI-powered projects created with Claude

---

## 🙏 Acknowledgments

Inspired by the joy of basketball and the art of software craftsmanship.

Built with ❤️ by developers, for developers.

---

**Ready to turn your Git into an NBA season?** 🏀

[Get Started](#-quick-start) | [Documentation](./DEVELOPMENT.md) | [Contribute](./CONTRIBUTING.md)
