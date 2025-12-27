# 📡 API Specification

REST API documentation for **The Git League**.

**Base URL:** `/api/v1`

**Authentication:** Bearer token (JWT) in `Authorization` header

---

## 📋 Table of Contents

- [Authentication](#authentication)
- [Users](#users)
- [Projects](#projects)
- [Repositories](#repositories)
- [Seasons](#seasons)
- [Players](#players)
- [Leaderboards](#leaderboards)
- [Awards](#awards)
- [Fantasy Leagues](#fantasy-leagues)
- [Stats](#stats)
- [Common Patterns](#common-patterns)
- [Error Responses](#error-responses)

---

## 🔐 Authentication

### POST `/auth/magic-link`

Request a magic link for authentication.

**Request:**
```json
{
  "email": "alice@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "Magic link sent to alice@example.com",
  "expires_in": 900
}
```

**Errors:**
- `400` — Invalid email format
- `429` — Too many requests (rate limited)

---

### GET `/auth/verify`

Verify magic link token and get access token.

**Query Parameters:**
- `token` (required) — Magic link token from email

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "user-123",
    "email": "alice@example.com",
    "role": "player",
    "status": "approved",
    "display_name": "Alice"
  }
}
```

**Errors:**
- `401` — Invalid or expired token
- `403` — User not approved (spectator awaiting approval)

---

### GET `/auth/me`

Get current authenticated user.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "id": "user-123",
  "email": "alice@example.com",
  "role": "player",
  "status": "approved",
  "display_name": "Alice",
  "git_identities": [
    {
      "id": "identity-1",
      "git_name": "Alice",
      "git_email": "alice@example.com"
    }
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors:**
- `401` — Unauthorized (invalid/missing token)

---

## 👥 Users

### GET `/users`

List all users (Commissioner only).

**Query Parameters:**
- `role` (optional) — Filter by role: `commissioner`, `player`, `spectator`
- `status` (optional) — Filter by status: `approved`, `pending`, `retired`
- `page` (optional, default=1)
- `limit` (optional, default=50)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "user-123",
      "email": "alice@example.com",
      "role": "player",
      "status": "approved",
      "display_name": "Alice",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "pages": 1
}
```

**Errors:**
- `403` — Forbidden (not commissioner)

---

### GET `/users/{user_id}`

Get user by ID.

**Response:** `200 OK`
```json
{
  "id": "user-123",
  "email": "alice@example.com",
  "role": "player",
  "status": "approved",
  "display_name": "Alice",
  "git_identities": [...],
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors:**
- `404` — User not found

---

### PATCH `/users/{user_id}`

Update user (Commissioner only).

**Request:**
```json
{
  "role": "player",
  "status": "approved",
  "display_name": "Alice Builder"
}
```

**Response:** `200 OK`
```json
{
  "id": "user-123",
  "email": "alice@example.com",
  "role": "player",
  "status": "approved",
  "display_name": "Alice Builder"
}
```

**Errors:**
- `403` — Forbidden
- `404` — User not found

---

### POST `/users/{user_id}/git-identities`

Add Git identity to user.

**Request:**
```json
{
  "git_name": "Alice",
  "git_email": "alice@company.com"
}
```

**Response:** `201 Created`
```json
{
  "id": "identity-2",
  "user_id": "user-123",
  "git_name": "Alice",
  "git_email": "alice@company.com",
  "created_at": "2024-01-20T15:00:00Z"
}
```

---

## 🗂️ Projects

### GET `/projects`

List all projects.

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "project-1",
      "name": "Main League",
      "slug": "main-league",
      "created_by": "user-123",
      "created_at": "2024-01-01T00:00:00Z",
      "active_season": {
        "id": "season-1",
        "name": "2024 Season 1"
      }
    }
  ],
  "total": 1
}
```

---

### POST `/projects`

Create project (Commissioner only).

**Request:**
```json
{
  "name": "Engineering League",
  "slug": "eng-league"
}
```

**Response:** `201 Created`
```json
{
  "id": "project-2",
  "name": "Engineering League",
  "slug": "eng-league",
  "created_by": "user-123",
  "created_at": "2024-01-20T10:00:00Z"
}
```

**Errors:**
- `400` — Slug already exists
- `403` — Forbidden

---

### GET `/projects/{project_id}`

Get project details.

**Response:** `200 OK`
```json
{
  "id": "project-1",
  "name": "Main League",
  "slug": "main-league",
  "created_by": "user-123",
  "created_at": "2024-01-01T00:00:00Z",
  "repos_count": 5,
  "active_season": {
    "id": "season-1",
    "name": "2024 Season 1",
    "start_at": "2024-01-01T00:00:00Z",
    "end_at": "2024-06-30T23:59:59Z"
  }
}
```

---

## 📦 Repositories

### GET `/projects/{project_id}/repos`

List repositories in project.

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "repo-1",
      "project_id": "project-1",
      "name": "backend",
      "remote_url": "git@github.com:company/backend.git",
      "remote_type": "ssh",
      "branch": "main",
      "sync_frequency": "0 */6 * * *",
      "last_sync_at": "2024-01-20T12:00:00Z",
      "last_ingested_sha": "abc123def456",
      "status": "healthy",
      "error_message": null,
      "commits_count": 12543
    }
  ],
  "total": 5
}
```

---

### POST `/projects/{project_id}/repos`

Add repository to project (Commissioner only).

**Request:**
```json
{
  "name": "frontend",
  "remote_url": "https://github.com/company/frontend.git",
  "remote_type": "https",
  "branch": "main",
  "sync_frequency": "0 */6 * * *",
  "credentials": {
    "token": "ghp_xxxxxxxxxxxx"
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "repo-2",
  "project_id": "project-1",
  "name": "frontend",
  "remote_url": "https://github.com/company/frontend.git",
  "branch": "main",
  "status": "pending"
}
```

**Errors:**
- `400` — Invalid repo configuration
- `403` — Forbidden

---

### POST `/repos/{repo_id}/sync`

Trigger immediate sync (Commissioner only).

**Response:** `202 Accepted`
```json
{
  "task_id": "task-abc123",
  "message": "Sync started",
  "status_url": "/api/v1/tasks/task-abc123"
}
```

---

### GET `/repos/{repo_id}/sync-logs`

Get sync logs for repository.

**Query Parameters:**
- `limit` (optional, default=50)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "log-1",
      "repo_id": "repo-1",
      "started_at": "2024-01-20T12:00:00Z",
      "completed_at": "2024-01-20T12:05:30Z",
      "status": "success",
      "commits_ingested": 45,
      "error_message": null
    }
  ],
  "total": 120
}
```

---

## 📅 Seasons

### GET `/projects/{project_id}/seasons`

List seasons in project.

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "season-1",
      "project_id": "project-1",
      "name": "2024 Season 1",
      "start_at": "2024-01-01T00:00:00Z",
      "end_at": "2024-06-30T23:59:59Z",
      "status": "active",
      "players_count": 42,
      "commits_count": 12543
    }
  ],
  "total": 3
}
```

---

### POST `/projects/{project_id}/seasons`

Create season (Commissioner only).

**Request:**
```json
{
  "name": "2024 Season 2",
  "start_at": "2024-07-01T00:00:00Z",
  "end_at": "2024-12-31T23:59:59Z"
}
```

**Response:** `201 Created`
```json
{
  "id": "season-2",
  "project_id": "project-1",
  "name": "2024 Season 2",
  "start_at": "2024-07-01T00:00:00Z",
  "end_at": "2024-12-31T23:59:59Z",
  "status": "draft"
}
```

---

### POST `/seasons/{season_id}/activate`

Activate season (Commissioner only). Only one season can be active per project.

**Response:** `200 OK`
```json
{
  "id": "season-2",
  "status": "active"
}
```

**Errors:**
- `409` — Another season is already active

---

### POST `/seasons/{season_id}/recompute`

Recompute stats for season (Commissioner only).

**Response:** `202 Accepted`
```json
{
  "task_id": "task-recompute-123",
  "message": "Recompute started",
  "status_url": "/api/v1/tasks/task-recompute-123"
}
```

---

## 👤 Players

### GET `/players/{player_id}`

Get player profile.

**Query Parameters:**
- `season_id` (optional) — Filter stats by season

**Response:** `200 OK`
```json
{
  "id": "user-123",
  "display_name": "Alice",
  "email": "alice@example.com",
  "role": "player",
  "status": "approved",
  "current_season_stats": {
    "season_id": "season-1",
    "commits": 234,
    "additions": 8543,
    "deletions": 3421,
    "pts": 1245,
    "reb": 520,
    "ast": 310,
    "blk": 45,
    "stl": 12,
    "tov": 23,
    "impact_score": 1823.5,
    "rank": 3
  },
  "career_stats": {
    "total_commits": 1234,
    "total_pts": 5432,
    "seasons_played": 3,
    "awards_count": 7
  },
  "awards": [
    {
      "id": "award-1",
      "season_id": "season-1",
      "award_type": "player_of_week",
      "period_start": "2024-01-15",
      "score": 234.5
    }
  ],
  "recent_commits": [
    {
      "sha": "abc123",
      "repo_name": "backend",
      "message_title": "Add user authentication",
      "commit_date": "2024-01-20T15:30:00Z",
      "additions": 156,
      "deletions": 23,
      "pts": 166
    }
  ]
}
```

---

### GET `/players/{player_id}/stats`

Get player stats breakdown.

**Query Parameters:**
- `season_id` (required)
- `period_type` (optional) — `day`, `week`, `month`, `season`
- `start_date` (optional)
- `end_date` (optional)

**Response:** `200 OK`
```json
{
  "player_id": "user-123",
  "season_id": "season-1",
  "period_type": "week",
  "stats": [
    {
      "period_start": "2024-01-15",
      "commits": 12,
      "additions": 456,
      "deletions": 123,
      "pts": 476,
      "reb": 74,
      "ast": 15,
      "blk": 3,
      "tov": 1,
      "impact_score": 560.2
    }
  ]
}
```

---

## 🏆 Leaderboards

### GET `/seasons/{season_id}/leaderboard`

Get leaderboard for season.

**Query Parameters:**
- `period_type` (optional, default=`season`) — `day`, `week`, `month`, `season`
- `period_start` (optional) — Filter by specific period (YYYY-MM-DD)
- `repo_id` (optional) — Filter by repository
- `sort_by` (optional, default=`pts`) — `pts`, `reb`, `ast`, `blk`, `commits`, `impact_score`
- `order` (optional, default=`desc`) — `asc`, `desc`
- `page` (optional, default=1)
- `limit` (optional, default=50)

**Response:** `200 OK`
```json
{
  "season_id": "season-1",
  "period_type": "week",
  "period_start": "2024-01-15",
  "items": [
    {
      "rank": 1,
      "player": {
        "id": "user-123",
        "display_name": "Alice",
        "email": "alice@example.com"
      },
      "stats": {
        "commits": 45,
        "additions": 1234,
        "deletions": 456,
        "pts": 1344,
        "reb": 274,
        "ast": 60,
        "blk": 9,
        "stl": 2,
        "tov": 3,
        "impact_score": 1567.8
      },
      "trend": "up"
    }
  ],
  "total": 42,
  "page": 1,
  "pages": 1
}
```

---

## 🏅 Awards

### GET `/seasons/{season_id}/awards`

Get awards for season.

**Query Parameters:**
- `period_type` (optional) — `week`, `month`, `season`
- `award_type` (optional) — `player_of_week`, `player_of_month`, `mvp`, `most_improved`
- `player_id` (optional) — Filter by player

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "award-1",
      "season_id": "season-1",
      "period_type": "week",
      "period_start": "2024-01-15",
      "award_type": "player_of_week",
      "player": {
        "id": "user-123",
        "display_name": "Alice"
      },
      "score": 1567.8,
      "metadata": {
        "pts": 1344,
        "reb": 274,
        "ast": 60,
        "commits": 45
      },
      "created_at": "2024-01-22T00:00:00Z"
    }
  ],
  "total": 24
}
```

---

### GET `/plays-of-the-day`

Get recent "Play of the Day" highlights.

**Query Parameters:**
- `season_id` (optional)
- `date` (optional) — Specific date (YYYY-MM-DD)
- `limit` (optional, default=10)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "play-1",
      "date": "2024-01-20",
      "commit": {
        "sha": "abc123def456",
        "repo_name": "backend",
        "message_title": "Implement caching layer for API",
        "commit_date": "2024-01-20T15:30:00Z",
        "additions": 234,
        "deletions": 45,
        "files_changed": 8
      },
      "player": {
        "id": "user-123",
        "display_name": "Alice"
      },
      "score": 892.5,
      "reason": {
        "pts": 244,
        "reb": 27,
        "ast": 10,
        "blk": 0,
        "description": "High-impact multi-file commit"
      }
    }
  ],
  "total": 10
}
```

---

## 🎮 Fantasy Leagues

### GET `/seasons/{season_id}/fantasy-leagues`

List fantasy leagues for season.

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "fantasy-1",
      "season_id": "season-1",
      "name": "Main Fantasy League",
      "roster_min": 3,
      "roster_max": 5,
      "lock_at": "2024-01-31T23:59:59Z",
      "participants_count": 15,
      "status": "open"
    }
  ],
  "total": 1
}
```

---

### POST `/seasons/{season_id}/fantasy-leagues`

Create fantasy league (Commissioner only).

**Request:**
```json
{
  "name": "Engineering Fantasy 2024",
  "roster_min": 3,
  "roster_max": 5,
  "lock_at": "2024-01-31T23:59:59Z",
  "draftable_player_ids": ["user-123", "user-456", ...]
}
```

**Response:** `201 Created`
```json
{
  "id": "fantasy-2",
  "season_id": "season-1",
  "name": "Engineering Fantasy 2024",
  "roster_min": 3,
  "roster_max": 5,
  "lock_at": "2024-01-31T23:59:59Z"
}
```

---

### POST `/fantasy-leagues/{league_id}/join`

Join fantasy league.

**Response:** `200 OK`
```json
{
  "league_id": "fantasy-1",
  "user_id": "user-789",
  "joined_at": "2024-01-20T16:00:00Z"
}
```

**Errors:**
- `409` — Already joined

---

### GET `/fantasy-leagues/{league_id}/roster`

Get user's roster in fantasy league.

**Response:** `200 OK`
```json
{
  "id": "roster-1",
  "league_id": "fantasy-1",
  "user_id": "user-789",
  "picks": [
    {
      "position": 1,
      "player": {
        "id": "user-123",
        "display_name": "Alice"
      },
      "current_score": 1567.8
    }
  ],
  "total_score": 7234.5,
  "locked_at": null
}
```

---

### PUT `/fantasy-leagues/{league_id}/roster`

Update roster (before lock).

**Request:**
```json
{
  "picks": [
    {"player_id": "user-123"},
    {"player_id": "user-456"},
    {"player_id": "user-789"}
  ]
}
```

**Response:** `200 OK`
```json
{
  "id": "roster-1",
  "picks": [...],
  "updated_at": "2024-01-20T16:30:00Z"
}
```

**Errors:**
- `400` — Invalid picks (min/max violated, duplicate players)
- `409` — Roster already locked

---

### POST `/fantasy-leagues/{league_id}/roster/lock`

Lock roster (cannot be changed after lock).

**Response:** `200 OK`
```json
{
  "id": "roster-1",
  "locked_at": "2024-01-20T16:45:00Z"
}
```

**Errors:**
- `409` — Already locked

---

### GET `/fantasy-leagues/{league_id}/leaderboard`

Get fantasy league leaderboard.

**Response:** `200 OK`
```json
{
  "items": [
    {
      "rank": 1,
      "participant": {
        "id": "user-789",
        "display_name": "Bob"
      },
      "roster_id": "roster-2",
      "total_score": 8234.5,
      "picks_count": 5,
      "locked_at": "2024-01-28T12:00:00Z"
    }
  ],
  "total": 15
}
```

---

## 📊 Stats

### GET `/seasons/{season_id}/stats/summary`

Get season summary stats.

**Response:** `200 OK`
```json
{
  "season_id": "season-1",
  "total_commits": 12543,
  "total_players": 42,
  "total_additions": 456789,
  "total_deletions": 123456,
  "active_players_this_week": 38,
  "top_contributors": [
    {
      "player_id": "user-123",
      "display_name": "Alice",
      "commits": 234,
      "pts": 1567
    }
  ],
  "repos": [
    {
      "repo_id": "repo-1",
      "name": "backend",
      "commits": 5432
    }
  ]
}
```

---

## 🔧 Common Patterns

### Pagination

All list endpoints support pagination:

```
GET /api/v1/players?page=2&limit=25
```

Response includes:
```json
{
  "items": [...],
  "total": 150,
  "page": 2,
  "pages": 6
}
```

### Filtering

Use query parameters:
```
GET /api/v1/users?role=player&status=approved
```

### Sorting

Use `sort_by` and `order`:
```
GET /api/v1/seasons/season-1/leaderboard?sort_by=pts&order=desc
```

### Date Formats

All dates are ISO 8601:
- `2024-01-20T15:30:00Z` (timestamps)
- `2024-01-20` (dates)

---

## ❌ Error Responses

### Standard Error Format

```json
{
  "detail": "Error message",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-20T15:30:00Z"
}
```

### Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| `200` | OK | Successful request |
| `201` | Created | Resource created |
| `202` | Accepted | Async task started |
| `400` | Bad Request | Invalid input |
| `401` | Unauthorized | Missing/invalid token |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource doesn't exist |
| `409` | Conflict | Resource already exists |
| `422` | Unprocessable Entity | Validation failed |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server error |

### Validation Errors

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

---

## 🔗 WebSocket (Future)

Real-time updates via WebSocket (planned for V2):

```
ws://localhost:8000/ws/updates?token=<jwt>
```

**Events:**
- `sync.started` — Repo sync started
- `sync.completed` — Repo sync completed
- `award.created` — New award issued
- `leaderboard.updated` — Leaderboard changed

---

**For implementation details, see [ARCHITECTURE.md](./ARCHITECTURE.md)**

**Interactive API docs:** `http://localhost:8000/docs` (FastAPI auto-generated)
