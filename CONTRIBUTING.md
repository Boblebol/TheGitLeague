# 🤝 Contributing to The Git League

Thank you for your interest in contributing to **The Git League**! This document provides guidelines and workflows to help you contribute effectively.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)

---

## 📜 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. We expect all contributors to:

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Trolling, insulting/derogatory comments, and personal attacks
- Publishing others' private information without permission
- Any conduct that could reasonably be considered inappropriate

**Violations:** Report to [maintainers@thegitleague.dev](mailto:maintainers@thegitleague.dev)

---

## 🎯 How Can I Contribute?

### 1. Reporting Bugs

**Before submitting:**
- Check [existing issues](https://github.com/Boblebol/TheGitLeague/issues)
- Verify it's reproducible on the latest version
- Gather relevant information (logs, environment, steps to reproduce)

**Submit a bug report:**
```markdown
**Environment:**
- Version: [e.g., v0.1.0]
- OS: [e.g., Ubuntu 22.04]
- Docker version: [e.g., 24.0.5]

**Steps to Reproduce:**
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Logs/Screenshots:**
[If applicable]
```

### 2. Suggesting Features

**Before suggesting:**
- Check [roadmap](./Base%20doc#ROADMAP_AND_GTM)
- Search existing feature requests

**Submit a feature request:**
```markdown
**Problem Statement:**
[What pain point does this solve?]

**Proposed Solution:**
[How should it work?]

**Alternatives Considered:**
[Other approaches you've thought about]

**Additional Context:**
[Screenshots, mockups, examples]
```

### 3. Code Contributions

**Good First Issues:**
- Look for issues tagged `good-first-issue`
- Check `help-wanted` label
- Small bug fixes and documentation improvements

**Major Features:**
- Discuss in an issue first
- Get approval from maintainers before coding
- Follow the roadmap priorities

---

## 🔄 Development Workflow

### 1. Fork & Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/TheGitLeague.git
cd TheGitLeague

# Add upstream remote
git remote add upstream https://github.com/Boblebol/TheGitLeague.git
```

### 2. Create a Branch

```bash
# Update main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

**Branch naming:**
- `feature/` — New features
- `fix/` — Bug fixes
- `docs/` — Documentation only
- `refactor/` — Code refactoring
- `test/` — Adding/updating tests
- `chore/` — Maintenance tasks

### 3. Make Changes

- Follow [coding standards](#coding-standards)
- Write tests for new functionality
- Update documentation as needed
- Keep commits atomic and well-described

### 4. Test Your Changes

```bash
# Frontend tests
cd frontend
npm run test
npm run lint
npm run type-check

# Backend tests
cd backend
pytest
ruff check .
mypy .

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

### 5. Commit

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add fantasy roster locking functionality"

# Or use conventional commits (recommended)
git commit
```

See [Commit Guidelines](#commit-guidelines) for format details.

### 6. Push & Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
# Fill out the PR template completely
```

---

## 🎨 Coding Standards

### General Principles

- **Simplicity over cleverness** — Prefer readable code
- **Avoid over-engineering** — Only add what's needed
- **No premature optimization** — Profile before optimizing
- **Explainability** — Code should be self-documenting

### Frontend (TypeScript/React)

**Style:**
- Use TypeScript strictly (no `any` unless absolutely necessary)
- Functional components with hooks
- Use shadcn/ui components (don't reinvent)
- Tailwind for styling (avoid custom CSS)

**Naming:**
- Components: `PascalCase` (e.g., `LeaderboardTable.tsx`)
- Functions/variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Files: Match component name

**Example:**
```typescript
// Good
interface PlayerCardProps {
  player: Player;
  onSelect: (id: string) => void;
}

export function PlayerCard({ player, onSelect }: PlayerCardProps) {
  return (
    <Card onClick={() => onSelect(player.id)}>
      <CardHeader>{player.name}</CardHeader>
      <CardContent>PTS: {player.stats.points}</CardContent>
    </Card>
  );
}

// Bad — any, unclear naming, inline styles
export function Card({ data }: any) {
  return <div style={{ padding: '10px' }}>{data.n}</div>;
}
```

**File structure:**
```
src/
├── app/              # Next.js pages
├── components/       # Reusable components
│   ├── ui/          # shadcn/ui components
│   ├── leaderboard/
│   └── player/
├── lib/             # Utilities
├── hooks/           # Custom hooks
└── types/           # TypeScript types
```

### Backend (Python/FastAPI)

**Style:**
- Follow PEP 8
- Use type hints everywhere
- Pydantic for validation
- SQLAlchemy for ORM

**Naming:**
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Files: `snake_case.py`

**Example:**
```python
# Good
from pydantic import BaseModel
from datetime import datetime

class PlayerStatsResponse(BaseModel):
    player_id: str
    season_id: str
    points: int
    rebounds: int
    assists: int
    updated_at: datetime

@router.get("/players/{player_id}/stats", response_model=PlayerStatsResponse)
async def get_player_stats(
    player_id: str,
    season_id: str | None = None,
    db: Session = Depends(get_db),
) -> PlayerStatsResponse:
    """Get player statistics for a season."""
    stats = await stats_service.get_player_stats(db, player_id, season_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Player stats not found")
    return stats

# Bad — no types, unclear naming
@router.get("/stats")
def get(id, s=None):
    result = db.query(Stats).filter(Stats.pid == id).first()
    return result
```

**File structure:**
```
backend/
├── app/
│   ├── api/           # API routes
│   │   └── v1/
│   ├── core/          # League engine
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   ├── workers/       # Celery tasks
│   └── utils/         # Utilities
├── tests/
└── alembic/           # Migrations
```

### SQL & Migrations

- Always use Alembic for schema changes
- Name migrations descriptively: `YYYY_MM_DD_HHMM_description.py`
- Include both `upgrade()` and `downgrade()`
- Test migrations on sample data

**Example:**
```python
"""add_fantasy_league_tables

Revision ID: 2024_01_15_1430
Revises: 2024_01_10_0900
Create Date: 2024-01-15 14:30:00
"""

def upgrade() -> None:
    op.create_table(
        'fantasy_leagues',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('season_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('roster_min', sa.Integer(), nullable=False),
        sa.Column('roster_max', sa.Integer(), nullable=False),
        sa.Column('lock_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['season_id'], ['seasons.id']),
    )

def downgrade() -> None:
    op.drop_table('fantasy_leagues')
```

---

## 📝 Commit Guidelines

### Conventional Commits Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation only
- `style` — Code style (formatting, missing semicolons, etc.)
- `refactor` — Code change that neither fixes a bug nor adds a feature
- `perf` — Performance improvement
- `test` — Adding or updating tests
- `chore` — Maintenance (dependencies, build, etc.)
- `ci` — CI/CD changes

**Scope (optional):**
- `api`, `ui`, `db`, `worker`, `auth`, `fantasy`, `awards`, etc.

**Examples:**
```bash
feat(api): add fantasy roster locking endpoint

Implement POST /api/v1/fantasy/rosters/{id}/lock endpoint
to allow participants to lock their roster before season starts.

Closes #42

---

fix(worker): prevent duplicate commit ingestion

Add idempotency check using (repo_id, sha) unique constraint
to avoid processing the same commit multiple times.

Fixes #38

---

docs(readme): update quick start instructions

Clarify Docker Compose setup steps and add troubleshooting
section for common first-run issues.
```

---

## 🔍 Pull Request Process

### Before Submitting

✅ **Checklist:**
- [ ] Tests pass locally (`npm test`, `pytest`)
- [ ] Linting passes (`npm run lint`, `ruff check`)
- [ ] Type checking passes (`npm run type-check`, `mypy`)
- [ ] Documentation updated (README, docstrings, API specs)
- [ ] Commit messages follow conventions
- [ ] Branch is up-to-date with `main`

### PR Template

When opening a PR, fill out the template:

```markdown
## Description
[Clear description of what this PR does]

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Related Issues
Closes #[issue_number]

## How Has This Been Tested?
[Describe the tests you ran]

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Checklist
- [ ] My code follows the project's coding standards
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have updated the documentation accordingly
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

### Review Process

1. **Automated checks** — CI must pass (tests, linting, build)
2. **Code review** — At least 1 maintainer approval required
3. **Testing** — Reviewer tests functionality manually
4. **Merge** — Squash and merge (maintainers only)

**Review timeline:**
- Initial response: 48 hours
- Full review: 1 week for features, 2-3 days for fixes

---

## 🧪 Testing Requirements

### Frontend Tests

**Required coverage:**
- Unit tests for utilities and hooks
- Component tests for complex UI logic
- Integration tests for critical flows

**Tools:**
- Jest + React Testing Library
- Vitest (alternative)

**Example:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { PlayerCard } from '@/components/player/PlayerCard';

describe('PlayerCard', () => {
  it('displays player name and stats', () => {
    const player = { id: '1', name: 'Alice', stats: { points: 120 } };
    render(<PlayerCard player={player} onSelect={jest.fn()} />);

    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('PTS: 120')).toBeInTheDocument();
  });

  it('calls onSelect when clicked', () => {
    const onSelect = jest.fn();
    const player = { id: '1', name: 'Alice', stats: { points: 120 } };
    render(<PlayerCard player={player} onSelect={onSelect} />);

    fireEvent.click(screen.getByText('Alice'));
    expect(onSelect).toHaveBeenCalledWith('1');
  });
});
```

### Backend Tests

**Required coverage:**
- Unit tests for services and business logic
- API endpoint tests
- Database integration tests
- Worker/job tests

**Tools:**
- pytest
- pytest-asyncio (for async tests)
- httpx (for API tests)

**Example:**
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_get_player_stats_success(async_client: AsyncClient, db_session):
    # Arrange
    player = create_test_player(db_session)
    season = create_test_season(db_session)

    # Act
    response = await async_client.get(f"/api/v1/players/{player.id}/stats?season_id={season.id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == player.id
    assert "points" in data

@pytest.mark.asyncio
async def test_get_player_stats_not_found(async_client: AsyncClient):
    response = await async_client.get("/api/v1/players/nonexistent/stats")
    assert response.status_code == 404
```

### Minimum Coverage

- **Backend:** 80% overall, 90% for core logic
- **Frontend:** 70% overall, 85% for critical paths

---

## 📚 Documentation

### What to Document

**Always update:**
- README — If you change features or setup
- API_SPEC.md — If you add/change endpoints
- ARCHITECTURE.md — If you change data models or structure
- Inline code comments — For complex logic
- Docstrings — For all public functions/classes

**When to create new docs:**
- New major feature → Add section to README + detailed guide
- New deployment method → Update DEVELOPMENT.md
- Architecture changes → Update ARCHITECTURE.md

### Documentation Style

**Code comments:**
```typescript
// Good — Explains WHY
// We cap additions at 1000 to prevent spam commits from skewing stats
const cappedAdditions = Math.min(commit.additions, 1000);

// Bad — States the obvious
// Set capped additions to minimum of additions or 1000
const cappedAdditions = Math.min(commit.additions, 1000);
```

**Docstrings (Python):**
```python
def calculate_nba_points(commit: Commit, coefficients: ScoringCoefficients) -> int:
    """
    Calculate NBA-style points for a commit.

    Points are calculated based on capped additions weighted by a coefficient,
    plus a base value per commit. This prevents massive auto-generated changes
    from dominating the leaderboard.

    Args:
        commit: The commit to score
        coefficients: Project-specific scoring configuration

    Returns:
        Integer point value (0-1000 range)

    Example:
        >>> commit = Commit(additions=500, deletions=100)
        >>> coeffs = ScoringCoefficients(additions_weight=1.0, commit_base=10)
        >>> calculate_nba_points(commit, coeffs)
        510
    """
```

---

## 🎖️ Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- The Git League instance's Hall of Fame (meta!)

Top contributors may be invited to become maintainers.

---

## ❓ Questions?

- **Discussions:** [GitHub Discussions](https://github.com/Boblebol/TheGitLeague/discussions)
- **Issues:** [Bug reports & features](https://github.com/Boblebol/TheGitLeague/issues)
- **Chat:** (Coming soon — Discord/Slack)

---

**Thank you for contributing to The Git League!** 🏀
