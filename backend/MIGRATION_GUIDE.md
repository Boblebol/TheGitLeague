# Migration Guide: Pull-based to Push-based Synchronization

## Overview

This guide walks you through migrating repositories from the legacy **pull-based** (PULL_CELERY) synchronization method to the new **push-based** (PUSH_CLIENT) method.

## Why Migrate?

### Benefits of Push-based Sync

| Aspect | Pull (PULL_CELERY) | Push (PUSH_CLIENT) |
|--------|-----------|-------------|
| **PAT Security** | ❌ Stored encrypted in DB | ✅ Stays on commissioner's PC |
| **Setup Complexity** | ❌ Web form + credentials | ✅ YAML config file |
| **Flexibility** | ❌ Cron job on server | ✅ Cron on local machine |
| **Revocation** | ❌ Change token everywhere | ✅ Revoke API key instantly |
| **Audit Trail** | ⚠️ Limited | ✅ Comprehensive |
| **Dependencies** | ❌ Celery + Redis | ✅ Lightweight CLI tool |

## Migration Process

### Phase 1: Pre-Migration (Planning)

1. **Identify Repositories to Migrate**

```bash
# See current status
python scripts/migrate_repos_to_push.py --status
```

Output:
```
📊 Migration Status:
   PULL_CELERY (legacy): 12
   PUSH_CLIENT (new):    2
   Total:                14
   Progress:             14.3% migrated
```

2. **Create API Key for Commissioners**

- Go to GitLeague web UI → Settings → API Keys
- Click "Create API Key"
- Name it: "Python CLI Client"
- Scopes: `sync:commits,read:repos`
- Copy the key (shown only once!)

3. **Prepare Commissioners**

- Provide them with:
  - New API key
  - Python client installation instructions
  - Sample `repos.yaml` configuration
  - Test instructions

### Phase 2: Test Migration (Dry-run)

Before migrating production repositories, test the process:

```bash
# Preview what would happen
python scripts/migrate_repos_to_push.py --dry-run <repo_id>
```

Example output:
```
📦 Repository: My App
   Current: pull_celery
   Target:  push_client
   [DRY RUN] Changes that would be made:
   - Set sync_method to: push_client
   - Clear encrypted credentials
   - Preserve last_ingested_sha: abc123def456
```

### Phase 3: Client Setup

Each commissioner needs to set up the Python client:

**Step 1: Install**

```bash
pip install gitleague-client
```

**Step 2: Generate Config**

```bash
gitleague-client init
```

This creates `repos.yaml`:

```yaml
api_url: "https://api.thegitleague.com"
api_key: "tgl_xxx_yyy"  # Paste your API key here
batch_size: 100
max_retries: 3

projects:
  - name: "My Project"
    project_id: "550e8400-e29b-41d4-a716-446655440000"  # From web UI
    repos:
      - path: "~/code/my-repo"
        git_url: "git@github.com:org/my-repo.git"
        ssh_key: "~/.ssh/id_ed25519"
```

**Step 3: Test Connection**

```bash
gitleague-client test --config repos.yaml
```

Expected output:
```
Testing connection to GitLeague API...
✓ Connected to GitLeague API
✓ API Key: tgl_test_***
✓ Projects: 1
  - My Project (3 repos)
```

**Step 4: Dry-run Sync**

```bash
gitleague-client sync --config repos.yaml --dry-run
```

Shows what would be synced without sending data.

### Phase 4: Perform Migration

#### Option A: Migrate Specific Repositories

```bash
python scripts/migrate_repos_to_push.py <repo_id_1> <repo_id_2> ...
```

Example:
```bash
python scripts/migrate_repos_to_push.py abc123 def456 ghi789
```

Output:
```
📦 Repository: Frontend
   Current: pull_celery
   Target:  push_client
   ✓ Migrated successfully

📦 Repository: Backend API
   Current: pull_celery
   Target:  push_client
   ✓ Migrated successfully

✓ 2/2 migrations completed
```

#### Option B: Migrate All Repositories

```bash
# Migrate all PULL_CELERY repos
python scripts/migrate_repos_to_push.py --all

# Or only migrate inactive repos (safe option)
python scripts/migrate_repos_to_push.py --all --exclude-active
```

#### Option C: Migrate with Dry-run First

```bash
# Preview
python scripts/migrate_repos_to_push.py --dry-run <repo_id>

# Then actually migrate
python scripts/migrate_repos_to_push.py <repo_id>
```

### Phase 5: Initial Sync

Commissioners run the first sync:

```bash
gitleague-client sync --config repos.yaml
```

This will:
1. Connect to GitLeague API
2. Scan all configured repositories
3. Upload all new commits since last sync
4. Update sync status to "healthy"

For large repositories with many commits, this may take a while.

### Phase 6: Verify & Monitor

**Check Status in Web UI:**

1. Go to Project → Repositories
2. Verify sync_method shows "push_client"
3. Check last_sync_at timestamp
4. Verify commit counts are increasing

**Monitor Logs:**

```bash
# See audit logs for the migration
curl -H "Authorization: Bearer $JWT_TOKEN" \
  https://api.thegitleague.com/api/v1/audit-logs?action=migrate_repo_sync_method
```

**Run Periodic Syncs:**

Add to cron on commissioner's machine:

```bash
# Daily at 2 AM
0 2 * * * /path/to/python gitleague-client sync --config ~/repos.yaml >> ~/sync.log 2>&1
```

## Rollback Plan

If you need to revert to pull-based sync:

```bash
# Rollback specific repositories
python scripts/migrate_repos_to_push.py --rollback <repo_id_1> <repo_id_2> ...

# Rollback and show what would happen
python scripts/migrate_repos_to_push.py --rollback <repo_id> --dry-run
```

**Note**: After rollback, you'll need to reconfigure credentials on the repository.

## Migration Strategies

### Strategy 1: Gradual Migration (Recommended)

Migrate repositories gradually to catch issues early:

```bash
# Week 1: Migrate 2-3 test repositories
python scripts/migrate_repos_to_push.py test-repo-1 test-repo-2

# Week 2: Monitor and migrate 5-10 more
python scripts/migrate_repos_to_push.py repo-3 repo-4 repo-5

# Week 3+: Migrate remaining repositories
python scripts/migrate_repos_to_push.py --all --exclude-active
```

**Advantages**:
- Catch issues early
- Allow commissioners time to set up client
- Easier to troubleshoot
- Low risk of widespread failure

### Strategy 2: All at Once

Migrate all repositories in one go:

```bash
python scripts/migrate_repos_to_push.py --all
```

**Advantages**:
- Quick transition
- Single deployment window
- Easier to coordinate

**Disadvantages**:
- Higher risk
- Need to have all commissioners ready
- Harder to troubleshoot widespread issues

### Strategy 3: By Project

Migrate entire projects at once:

```bash
# Get all repos for a project
python scripts/list_repos_by_project.py <project_id>

# Migrate all repos for that project
python scripts/migrate_repos_to_push.py repo-1 repo-2 repo-3 ...
```

## Coexistence Period

Both sync methods can run simultaneously:

- `PULL_CELERY` repos still sync via Celery
- `PUSH_CLIENT` repos sync via CLI client
- No conflicts or data loss
- Can migrate incrementally

To disable Celery when all repos migrated:

```python
# In settings
CELERY_ENABLED = False  # Stop Celery beat scheduler
```

## Troubleshooting

### Issue: "API key not found"

**Cause**: Commissioner hasn't created API key yet

**Solution**:
1. Create API key in web UI
2. Add to repos.yaml or GITLEAGUE_API_KEY env var

### Issue: "Repository not found"

**Cause**: Repo ID doesn't match config

**Solution**:
1. Verify project_id in repos.yaml from web UI
2. Verify git_url is correct

### Issue: "No new commits"

**Cause**: Repository already synced

**Solution**:
- This is expected behavior
- Commits are deduplicated by SHA
- Only new commits since last_ingested_sha are sent

### Issue: "Branch not found"

**Cause**: Repository doesn't have configured branch

**Solution**:
1. Check branch name in repos.yaml (default: "main")
2. Verify repository has commits on that branch

### Issue: "Connection timeout"

**Cause**: Network issue or API unreachable

**Solution**:
1. Check API URL is correct
2. Verify network connectivity
3. Check firewall rules
4. Retry (automatic with backoff)

## Monitoring & Metrics

### Dashboard Queries

**Migration Progress**:
```sql
SELECT
  sync_method,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
FROM repos
GROUP BY sync_method;
```

**Last Sync Times**:
```sql
SELECT
  name,
  sync_method,
  last_sync_at,
  CASE WHEN last_sync_at < NOW() - INTERVAL '1 day'
    THEN 'Stale'
    ELSE 'Recent'
  END as status
FROM repos
ORDER BY last_sync_at DESC;
```

**Sync Success Rate**:
```sql
SELECT
  repo_id,
  COUNT(*) as total_syncs,
  SUM(CASE WHEN action = 'sync_commits' AND details LIKE '%errors: 0%'
    THEN 1 ELSE 0 END) as successful
FROM audit_logs
WHERE action = 'sync_commits'
GROUP BY repo_id;
```

## FAQ

**Q: Do both sync methods work at the same time?**

A: Yes, they can coexist. PULL_CELERY repos continue syncing via Celery while PUSH_CLIENT repos sync via CLI.

**Q: Will I lose commit history?**

A: No, all commits are preserved. Migration only changes the sync method.

**Q: What happens to encrypted credentials?**

A: They're deleted during migration (not needed anymore). Old credentials don't work with push-based sync.

**Q: Can I rollback after migration?**

A: Yes, use `--rollback` flag. But you'll need to reconfigure credentials.

**Q: How often should commissioners sync?**

A: As often as needed. Recommended: Daily cron job or after major commits.

**Q: What if a commit is synced twice?**

A: It's automatically deduplicated by SHA. No duplicates created.

**Q: Can commissioners use different sync schedules?**

A: Yes, each commissioner controls their own cron schedule.

**Q: Do I need to update the web UI?**

A: No, the web UI works with both methods automatically.

## Checklist

### Pre-Migration

- [ ] Review Migration Guide with team
- [ ] Create test repositories for migration
- [ ] Generate API keys for all commissioners
- [ ] Install Python client on test machines
- [ ] Test dry-run on test repositories

### Migration Day

- [ ] Create database backup
- [ ] Run `--status` to see current state
- [ ] Perform dry-run on first batch: `--dry-run <repo_id>`
- [ ] Migrate first batch of repositories
- [ ] Commissioners run initial sync
- [ ] Verify commits are syncing
- [ ] Monitor audit logs for errors
- [ ] Migrate remaining repositories

### Post-Migration

- [ ] Verify all repositories migrated
- [ ] Confirm sync success in web UI
- [ ] Check audit logs for migration actions
- [ ] Monitor for 48 hours
- [ ] Update documentation
- [ ] Communicate completion to team
- [ ] Plan Celery deprecation (future)

## Support

If you encounter issues:

1. Check troubleshooting section above
2. Review audit logs: `SELECT * FROM audit_logs WHERE action LIKE '%migrate%'`
3. Test CLI client: `gitleague-client test --config repos.yaml`
4. Check connectivity: `gitleague-client sync --config repos.yaml --dry-run`

## Next Steps

After successful migration:

1. **Optimize Celery**: Consider disabling Celery if no more PULL_CELERY repos
2. **Document Process**: Add to team runbooks
3. **Schedule Maintenance**: Plan for future updates
4. **Monitor Performance**: Track sync success rates and timing
5. **Gather Feedback**: Ask commissioners for improvement suggestions

---

**Questions?** Contact: hello@thegitleague.com
