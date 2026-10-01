# LogiAgent — Enterprise Backup, Disaster Recovery & Maintenance Strategy

## 1. Database Backup & Retention Policy

### Automated Supabase / PostgreSQL Backups
- **Continuous WAL Archiving**: Point-In-Time Recovery (PITR) enabled on Supabase PostgreSQL with a 7 to 30-day retention window.
- **Daily Full Logical Backups**: Automated daily snapshot via `pg_dump`:
  ```bash
  pg_dump --format=custom --no-owner --no-privileges -d "$DATABASE_URL" -f "logiagent_backup_$(date +%Y%m%d_%H%M%S).dump"
  ```
- **Offsite S3 / GCS Replication**: Backup artifacts are encrypted using AES-256 and pushed to an isolated, multi-region cloud storage bucket with 90-day lifecycle expiration.

---

## 2. Disaster Recovery & Rollback Strategy

### Recovery Time Objective (RTO) & Recovery Point Objective (RPO)
- **Target RTO**: < 15 minutes (Full service restoration from cold backup or read-replica promotion).
- **Target RPO**: < 5 minutes (Near zero data loss using Write-Ahead Logging PITR).

### Database Restoration Procedure
1. Provision target PostgreSQL instance with `pgvector` extension enabled.
2. Restore logical dump:
   ```bash
   pg_restore --clean --if-exists --no-owner --dbname="$TARGET_DATABASE_URL" logiagent_backup_YYYYMMDD_HHMMSS.dump
   ```
3. Run Phase 10 validation checks to confirm index integrity:
   ```bash
   python backend/migrate_phase10_performance.py
   ```
4. Verify backend readiness probe:
   ```bash
   curl -i http://localhost:8000/health/ready
   ```

---

## 3. Database Migration Management
- All schema alterations are versioned in `database/migrations/`.
- Migrations are tested for backward compatibility (additive changes, idempotent index creations `CREATE INDEX IF NOT EXISTS`).
- Pre-deployment rollback scripts are maintained for zero-downtime rollbacks.

---

## 4. Secret Rotation & Security Key Lifecycle

### JWT Secret Rotation
1. Update `JWT_SECRET` in secret manager (e.g., AWS Secrets Manager / Vault).
2. For seamless rotation without logging out active users immediately, support dual-key verification (active signing key + previous grace key for validation during transition window).
3. Revoke legacy active tokens by invalidating tokens older than rotation timestamp.

### Database Credential Rotation
1. Create secondary DB user with identical role permissions.
2. Update application connection strings with zero downtime.
3. Terminate active connections and drop the retired DB user.

---

## 5. Health Probes & Monitoring SLA
- **Liveness Probe**: `GET /health/live` (monitored by Kubernetes / load balancer every 10s).
- **Readiness Probe**: `GET /health/ready` (verifies DB connectivity & query execution).
- **Correlation**: Trace production issues using `X-Request-ID` attached to all logs and error responses.
