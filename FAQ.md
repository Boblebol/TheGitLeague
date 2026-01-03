# ❓ Frequently Asked Questions — The Git League

Common questions and troubleshooting guide.

---

## Installation & Setup

### Q: How do I install The Git League?

**A:** The easiest way is with Docker:

```bash
git clone https://github.com/Boblebol/TheGitLeague.git
cd TheGitLeague
cp .env.example .env
docker-compose up -d
```

Then visit `http://localhost:3000`. See [QUICKSTART.md](./QUICKSTART.md) for detailed steps.

### Q: What are the system requirements?

**A:** Minimum:
- Docker & Docker Compose
- 2GB RAM
- 10GB disk space

Recommended:
- 4GB+ RAM
- 20GB+ disk space (depends on commit history)
- 2+ CPU cores

### Q: Can I run it without Docker?

**A:** Yes, but Docker is recommended. For local development:

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

You'll also need PostgreSQL and Redis running separately.

### Q: How do I set up email?

**A:** See [EMAIL_SETUP.md](./EMAIL_SETUP.md) for detailed instructions. Quick version:

1. Get SMTP credentials from your email provider (Gmail, SendGrid, etc.)
2. Set environment variables:
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   EMAIL_FROM=noreply@yourdomain.com
   ```
3. Restart services: `docker-compose restart backend`

---

## Configuration

### Q: How do I configure the scoring system?

**A:** Score coefficients are set per-project in the Commissioner dashboard:

1. Go to Settings → Projects → Your Project
2. Scroll to "Scoring Configuration"
3. Adjust coefficients for each metric (PTS, REB, AST, etc.)
4. All commits from that point forward use new coefficients
5. Optionally recalculate past stats

**Default values:**
```
Points (PTS):        additions * 1.0 (capped at 1000) + 10 per commit
Rebounds (REB):      deletions * 0.5 (capped at 500)
Assists (AST):       files_changed * 1.5 (capped at 100)
Blocks (BLK):        2.0 per revert or bug-fix commit
Steals (STL):        Reserved for future features
Turnovers (TOV):     WIP/debug commits or excessive churn
```

### Q: How do I add multiple repositories?

**A:**

1. Go to your Project settings
2. Click "Add Repository"
3. Enter repository URL (SSH or HTTPS)
4. If SSH, ensure your server has credentials
5. Click "Test Connection"
6. Save and sync

You can add unlimited repos to one project.

### Q: Can I have multiple commissioners?

**A:** Currently, only the first user (creator) is Commissioner. To add commissioners:

1. Contact the original Commissioner
2. They can upgrade users to Commissioner role in Settings → Users

We're planning flexible role management for v2.

### Q: How do I create seasons?

**A:**

1. Go to Seasons
2. Click "Create Season"
3. Set start/end dates
4. Configure auto-period split (weekly, monthly)
5. Click "Activate" when ready

Once activated, a season cannot be deleted (to preserve history).

---

## Git Synchronization

### Q: How often does it sync?

**A:** By default, every 6 hours. You can:

1. Manual sync: Click "Sync Now" in project settings
2. Change frequency: Set `SYNC_INTERVAL_HOURS` in `.env`
3. Immediate: Use API endpoint `/api/v1/projects/{id}/sync`

### Q: What if sync fails?

**A:** Check the sync log:

1. Go to Project → Sync History
2. Click failed sync to see error details
3. Common issues:
   - **Bad URL** — Verify repository URL is correct
   - **Auth failed** — Check SSH key or HTTPS credentials
   - **Network timeout** — Check internet connection and firewall
   - **Disk full** — Ensure `/repos` directory has space

### Q: Can I sync multiple repos in parallel?

**A:** Yes! Background workers handle this automatically. To increase parallelism:

```bash
# In .env
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_PREFETCH_MULTIPLIER=1
```

Then restart worker: `docker-compose restart worker`

### Q: How long does initial sync take?

**A:** Depends on repo size:
- Small repo (< 10k commits): 1-2 minutes
- Medium repo (10k-100k commits): 5-15 minutes
- Large repo (> 100k commits): 30+ minutes

Run sync during off-hours for large repos.

### Q: Can I sync private repositories?

**A:** Yes, in two ways:

**SSH (Recommended):**
1. Generate key: `ssh-keygen -t ed25519`
2. Add public key to GitHub/GitLab deploy keys
3. Use SSH URL: `git@github.com:org/repo.git`

**HTTPS with Personal Token:**
1. Create personal access token (GitHub → Settings → Tokens)
2. Use URL: `https://token@github.com/org/repo.git`
3. Note: Credentials are encrypted at rest (Fernet)

### Q: How do I skip certain commits?

**A:** Add to commit message:

```bash
git commit -m "chore: update deps

[SKIP-STATS]
```

Commits with `[SKIP-STATS]` are not counted in the league.

---

## Leaderboards & Stats

### Q: Why aren't my commits showing up?

**A:**

1. **Not synced yet** — Run "Sync Now"
2. **Outside season range** — Create/activate a season that covers the commits
3. **Marked as skip** — Remove `[SKIP-STATS]` from commit message
4. **No author match** — Player email must match Git author email exactly

### Q: How do I match authors to players?

**A:**

**Automatic:**
- Sync and The Git League auto-matches Git author emails to user emails

**Manual:**
1. Go to Player profile
2. Click "Linked Emails"
3. Add email addresses that Git author might use
4. Past commits are retroactively assigned

### Q: How do I filter leaderboard results?

**A:**

1. Click "Filters" button on leaderboard
2. Filter by:
   - **Period:** Daily, Weekly, Monthly, Seasonal, All-time
   - **Repository:** Single repo or all
   - **Role:** All players or specific team
   - **Metric:** Any stat (PTS, REB, AST, etc.)
3. Click "Apply"

### Q: Can I download leaderboard data?

**A:**

**Via UI:**
- Export button (coming in v2)

**Via API:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://yourdomain.com/api/v1/leaderboards?period=monthly&format=csv"
```

---

## Awards & Recognition

### Q: How are awards calculated?

**A:**

- **Player of the Week/Month/Season** — Highest PTS in period
- **MVP (Most Valuable Player)** — Highest combined score
- **Most Improved** — Largest stat increase from previous period
- **Play of the Day** — Best single commit (highest PTS earned)
- **Hall of Fame** — Retired players who earned 3+ major awards

All calculated automatically weekly at midnight UTC.

### Q: Can I create custom awards?

**A:** Not yet in v1, but planned for v2. Currently:

1. Admins can manually add players to Hall of Fame
2. Custom awards coming in future release

### Q: Why didn't someone get an award?

**A:** Check:

1. **Award criteria not met** — Must have commits in period
2. **Tied scoring** — Multiple people tied are all awarded
3. **Absence marked** — Players on leave don't get awards

---

## Fantasy League

### Q: How do I create a fantasy league?

**A:**

1. Go to Fantasy → Create League
2. Name league (e.g., "Team Devs")
3. Set draftable players (usually all active players)
4. Set roster size (1-10 players per team)
5. Start draft immediately or schedule for later
6. Share draft link with participants

### Q: How do fantasy scoring work?

**A:** Fantasy players score based on real player stats during the season:

- 1 point per 10 PTS scored
- 1 point per 5 REB collected
- 2 points per AST
- 3 points per BLK
- 1 point per STL
- -1 point per TOV

Scoring updates daily.

### Q: Can I trade players?

**A:** Not yet in v1. Planned for v2. Currently:

1. Rosters are locked before season starts
2. Can't trade or add/drop players mid-season

### Q: What happens if a player leaves?

**A:**

1. Mark player as "Inactive" in Users
2. Their fantasy points freeze at that date
3. Teams keep the player on roster (they score zero going forward)

---

## Permissions & Roles

### Q: What can each role do?

**A:**

| Action | Commissioner | Player | Spectator |
|--------|--------------|--------|-----------|
| Create projects | ✅ | ❌ | ❌ |
| Manage repos | ✅ | ❌ | ❌ |
| Create seasons | ✅ | ❌ | ❌ |
| Adjust scoring | ✅ | ❌ | ❌ |
| Create leagues | ✅ | ❌ | ❌ |
| View leaderboards | ✅ | ✅ | ✅ |
| View own stats | ✅ | ✅ | ❌ |
| View all stats | ✅ | ✅ | ✅ |
| Invite users | ✅ | ❌ | ❌ |
| Manage users | ✅ | ❌ | ❌ |

### Q: How do I invite people?

**A:**

1. Go to Settings → Users
2. Click "Invite User"
3. Enter email address
4. Select role (Commissioner, Player, Spectator)
5. Send invite

User gets magic link email and auto-activates on first login.

### Q: Can I change a user's role?

**A:** Yes (Commissioner only):

1. Go to Settings → Users
2. Click user's role dropdown
3. Select new role
4. Click "Save"

---

## Troubleshooting

### Q: Services won't start

**A:** Check logs:

```bash
docker-compose logs -f

# If database error:
docker-compose down -v  # ⚠️ WARNING: Deletes data
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

### Q: "Port already in use" error

**A:** Another service is using ports 3000/8000. Options:

1. Kill the other service
2. Change ports in `.env`:
   ```bash
   FRONTEND_PORT=3001
   BACKEND_PORT=8001
   ```
3. Change docker-compose.yml ports

### Q: Database connection refused

**A:**

```bash
# Check PostgreSQL running
docker-compose ps postgres

# Restart database
docker-compose restart postgres

# Verify connection string
echo $DATABASE_URL

# Test manually
docker-compose exec postgres psql -U postgres
```

### Q: Redis connection timeout

**A:**

```bash
# Check Redis running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping

# View Redis logs
docker-compose logs redis

# Restart
docker-compose restart redis
```

### Q: Magic link not working

**A:**

1. **Email not arriving** — Check SMTP configuration in EMAIL_SETUP.md
2. **Link expired** — Magic links expire in 15 minutes
3. **Already used** — Each link can only be used once
4. **Wrong email** — Ensure email matches invitation

### Q: API returns 401 Unauthorized

**A:**

```bash
# Check token
echo $ACCESS_TOKEN

# Get new token
curl -X POST http://localhost:8000/api/v1/auth/magic-link \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com"}'

# Use in requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/health
```

### Q: Commits aren't being scored

**A:**

1. **Sync not run** — Click "Sync Now"
2. **Author email mismatch** — User email must match Git author email
3. **No active season** — Create and activate a season
4. **Commit outside season range** — Extend season dates if needed
5. **[SKIP-STATS] in message** — Remove skip marker

Check sync logs for details: Project → Sync History

### Q: Performance is slow

**A:**

1. **CPU usage high** — Reduce Celery workers: `CELERY_WORKER_CONCURRENCY=2`
2. **Memory usage high** — Increase Docker memory or reduce cache size
3. **Database slow** — Run: `docker-compose exec postgres VACUUM ANALYZE`
4. **Redis full** — Check: `docker-compose exec redis redis-cli INFO memory`

---

## Development & Contributing

### Q: How do I run tests?

**A:**

```bash
# Backend tests
cd backend
pytest

# Frontend tests (coming soon)
cd frontend
npm run test

# All tests in CI
gh workflow run tests
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for details.

### Q: How do I report a bug?

**A:**

1. Check if issue exists: https://github.com/Boblebol/TheGitLeague/issues
2. Open new issue with:
   - Clear title
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment (OS, Docker version, etc.)
   - Screenshots if helpful

### Q: How do I request a feature?

**A:**

1. Check [roadmap](./ROADMAP.md)
2. Open feature request issue with:
   - Problem you're solving
   - Proposed solution
   - Alternatives considered
   - Use cases

### Q: Can I contribute?

**A:** Yes! See [CONTRIBUTING.md](./CONTRIBUTING.md) for:
- Development workflow
- Coding standards
- Testing requirements
- Pull request process

---

## Security & Privacy

### Q: Is source code stored?

**A:** No. Only commit metadata:
- Hash, author, date, message
- Files changed, additions, deletions
- No actual code or file contents

### Q: Are my credentials encrypted?

**A:** Yes. Repository credentials (SSH keys, tokens) are:
- Encrypted with Fernet (AES-128)
- Never logged or exposed
- Only decrypted when syncing

### Q: Can I self-host to keep data private?

**A:** Yes! That's the entire purpose. Deploy with:

```bash
docker-compose up -d
# All data stays on your server
```

No cloud dependencies or external sync.

### Q: How do I report security issues?

**A:** Don't open public issue. Instead:

Email: security@thegitleague.com (when available)

Or contact maintainers privately on GitHub.

---

## Getting Help

### Resources

- 📖 [Documentation](./README.md)
- 🚀 [Deployment Guide](./DEPLOYMENT.md)
- 📧 [Email Setup](./EMAIL_SETUP.md)
- 🔒 [Security Audit](./SECURITY.md)
- 🤝 [Contributing Guide](./CONTRIBUTING.md)

### Community

- 💬 [GitHub Discussions](https://github.com/Boblebol/TheGitLeague/discussions)
- 🐛 [GitHub Issues](https://github.com/Boblebol/TheGitLeague/issues)
- 📬 Future: Discord/Slack community

### Direct Contact

For urgent issues:
1. Check this FAQ first
2. Search GitHub issues
3. Open GitHub discussion (preferred)
4. Open GitHub issue if necessary

---

**Last Updated:** January 2026
**Version:** 1.0.0

**Didn't find your answer?** Open a discussion: https://github.com/Boblebol/TheGitLeague/discussions
