# Deployment Checklist: Push-based Synchronization

## Pre-Deployment (1-2 weeks before)

### Planning & Communication

- [ ] Review complete implementation with team
- [ ] Schedule deployment window
- [ ] Notify all commissioners about changes
- [ ] Create FAQ document for commissioners
- [ ] Plan rollback strategy
- [ ] Brief support team on new system

### Testing

- [ ] Run full backend test suite
  ```bash
  cd backend && python -m pytest tests/ -v
  ```
- [ ] Run full client test suite
  ```bash
  cd gitleague-client && python -m pytest tests/ -v
  ```
- [ ] Test migration script on staging
  ```bash
  python scripts/migrate_repos_to_push.py --dry-run <test_repo_id>
  ```
- [ ] Test client setup end-to-end on staging
- [ ] Verify database backups work
- [ ] Test rollback procedure

### Dependencies & Infrastructure

- [ ] Verify Python 3.10+ available on servers
- [ ] Verify httpx, GitPython, pydantic installed
- [ ] Check API endpoint accessibility
- [ ] Verify database connections stable
- [ ] Check rate limiting configuration (slowapi)
- [ ] Verify audit logging enabled

### Documentation

- [ ] Update API documentation with sync endpoints
- [ ] Create commissioner setup guide
- [ ] Create troubleshooting guide
- [ ] Document API key management
- [ ] Create runbook for migration
- [ ] Update architecture diagrams

---

## Day Before Deployment

### Final Verification

- [ ] Get stakeholder sign-off
- [ ] Create production database backup
  ```bash
  pg_dump thegitleague_prod > backup_$(date +%Y%m%d_%H%M%S).sql
  ```
- [ ] Verify backup integrity
- [ ] Create rollback snapshot
- [ ] Check all monitoring systems

### Communication

- [ ] Send deployment notification to commissioners
- [ ] Provide support contact information
- [ ] Remind commissioners to prepare API keys
- [ ] Set up on-call support schedule

### Environment Preparation

- [ ] Deploy code to staging first
- [ ] Run smoke tests on staging
- [ ] Verify all endpoints responding
- [ ] Check logs for errors

---

## Deployment Day

### Morning (Start of Window)

#### 1. Pre-flight Checks

- [ ] Verify database connectivity
  ```sql
  SELECT COUNT(*) FROM repos;
  ```
- [ ] Verify API running and healthy
  ```bash
  curl https://api.thegitleague.com/health
  ```
- [ ] Check all background jobs/workers
- [ ] Verify monitoring systems
- [ ] Check disk space availability
- [ ] Review recent error logs

#### 2. Database Preparation

- [ ] Stop Celery beat scheduler (optional at this point)
  ```bash
  pkill -f celery\ beat
  ```
- [ ] Verify no active sync jobs
  ```bash
  ps aux | grep celery
  ```
- [ ] Create final backup
  ```bash
  pg_dump thegitleague_prod > deployment_backup.sql
  ```

#### 3. Code Deployment

- [ ] Pull latest code
  ```bash
  cd /app && git pull origin main
  ```
- [ ] Run database migrations
  ```bash
  alembic upgrade head
  ```
- [ ] Verify migrations applied
  ```sql
  SELECT * FROM alembic_version;
  ```
- [ ] Restart application server
  ```bash
  systemctl restart gitleague-backend
  ```
- [ ] Wait for service to stabilize (30 seconds)
- [ ] Verify API responding
  ```bash
  curl -v https://api.thegitleague.com/api/v1
  ```

#### 4. Verify New Endpoints

- [ ] Test API key creation endpoint
  ```bash
  curl -X POST https://api.thegitleague.com/api/v1/api-keys/ \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name": "Test", "scopes": "sync:commits,read:repos"}'
  ```
- [ ] Test sync status endpoint
  ```bash
  curl https://api.thegitleague.com/api/v1/sync/projects/{id}/repos/{id}/status \
    -H "Authorization: Bearer $API_KEY"
  ```
- [ ] Test commit push endpoint
  ```bash
  curl -X POST https://api.thegitleague.com/api/v1/sync/projects/{id}/repos/{id}/commits \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"commits": []}'
  ```

#### 5. Release Availability (Phased)

- [ ] Create API key for testing
- [ ] Distribute to 10% of commissioners (early adopters)
- [ ] Monitor for 24 hours
- [ ] Gradually increase to 50% of commissioners
- [ ] Monitor for 24 hours
- [ ] Release to 100%

---

## Post-Deployment: First 48 Hours

### Hourly (First 4 Hours)

- [ ] Monitor error logs
- [ ] Check API response times
- [ ] Verify database queries performant
- [ ] Monitor rate limiting
- [ ] Check CPU/memory usage
- [ ] Verify no data corruption

### Every 4 Hours (First 24 Hours)

- [ ] Check sync success rates
- [ ] Review audit logs
- [ ] Verify commits being ingested
- [ ] Check for any API errors
- [ ] Monitor commissioner feedback

### After 24 Hours

- [ ] Run comprehensive tests
  ```bash
  python -m pytest tests/test_sync.py -v
  python -m pytest tests/test_api_keys.py -v
  ```
- [ ] Verify all repos syncing
- [ ] Check data consistency
- [ ] Review performance metrics
- [ ] Start migration process if stable

### After 48 Hours

- [ ] Make final determination on stability
- [ ] Begin repository migrations (if stable)
- [ ] Continue monitoring
- [ ] Gather commissioner feedback

---

## Migration Phase (Weeks 1-3)

### Week 1: Soft Launch

- [ ] Migrate 2-3 test repositories
  ```bash
  python scripts/migrate_repos_to_push.py <test_repo_id>
  ```
- [ ] Commissioners do initial sync
- [ ] Verify commits sync successfully
- [ ] Monitor for issues
- [ ] Gather feedback

### Week 2: Gradual Rollout

- [ ] Migrate 5-10 additional repositories
- [ ] Continue monitoring
- [ ] Verify sync patterns
- [ ] Address any issues
- [ ] Collect metrics

### Week 3+: Full Migration

- [ ] Migrate remaining repositories
  ```bash
  python scripts/migrate_repos_to_push.py --all
  ```
- [ ] Confirm all successfully migrated
- [ ] Monitor for stabilization
- [ ] Continue support

---

## Stability Criteria

### All boxes must be checked before considering deployment successful:

#### Functionality
- [ ] API key endpoints working
- [ ] Sync endpoints working
- [ ] Authentication (JWT + API key) working
- [ ] Rate limiting working
- [ ] Hybrid auth working

#### Data Integrity
- [ ] No data corruption detected
- [ ] Audit logs capturing all actions
- [ ] Commit deduplication working
- [ ] Status updates accurate

#### Performance
- [ ] API response times < 200ms median
- [ ] 99th percentile < 1s
- [ ] Database queries < 100ms
- [ ] No memory leaks

#### Reliability
- [ ] 99.9% uptime
- [ ] Error rate < 0.1%
- [ ] No unhandled exceptions
- [ ] Graceful degradation under load

#### Security
- [ ] API keys properly hashed
- [ ] No credentials in logs
- [ ] Rate limiting effective
- [ ] HTTPS enforced

---

## Rollback Procedure

### If deployment is unstable:

#### Immediate Actions (First 15 minutes)

1. **Stop the bleeding**
   ```bash
   systemctl stop gitleague-backend
   ```

2. **Revert code**
   ```bash
   git revert HEAD
   git push origin main
   ```

3. **Restore backup**
   ```bash
   psql thegitleague_prod < deployment_backup.sql
   ```

4. **Restart services**
   ```bash
   systemctl start gitleague-backend
   systemctl start celery
   systemctl start celery_beat
   ```

5. **Verify rollback**
   ```bash
   curl https://api.thegitleague.com/health
   ```

#### Communication

- [ ] Notify all stakeholders
- [ ] Update status page
- [ ] Post update to Slack
- [ ] Schedule post-mortem within 24 hours

#### Investigation

- [ ] Review error logs
- [ ] Check database state
- [ ] Document what failed
- [ ] Plan fix before retry

---

## Post-Deployment Support

### First Week

- [ ] Monitor all systems closely
- [ ] Answer commissioner questions
- [ ] Address any issues immediately
- [ ] Daily check-in with team

### Ongoing

- [ ] Weekly sync status review
- [ ] Monthly performance metrics
- [ ] Quarterly security audit
- [ ] Continuous monitoring

---

## Sign-off

**Ready for Deployment?**

- [ ] Tech Lead: _______________________ Date: _______
- [ ] DevOps Lead: _____________________ Date: _______
- [ ] Product Owner: ____________________ Date: _______

**Deployment Executed By:**

Name: _________________ Date: _______ Time: _______

**Deployment Result:**

- [ ] Successful (proceed to monitoring)
- [ ] Partial Success (proceed with caution, monitor closely)
- [ ] Failed (execute rollback)

**Notes:**
```
[Space for deployment notes]
```

---

## Emergency Contacts

- **On-Call Engineer**: ___________________
- **DevOps Lead**: ___________________
- **Backend Lead**: ___________________
- **Database Admin**: ___________________

**Escalation**: If issue not resolved in 15 minutes, escalate to engineering manager.

---

## Appendix: Common Commands

```bash
# Check service status
systemctl status gitleague-backend

# View recent logs
journalctl -u gitleague-backend -n 100

# Run migrations
alembic upgrade head

# Restart services
systemctl restart gitleague-backend

# Database backup
pg_dump thegitleague_prod > backup.sql

# Database restore
psql thegitleague_prod < backup.sql

# Check API health
curl https://api.thegitleague.com/health

# Run tests
python -m pytest tests/ -v

# Migrate repositories
python scripts/migrate_repos_to_push.py --status
```

---

**Last Updated**: 2026-01-02
**Version**: 1.0
