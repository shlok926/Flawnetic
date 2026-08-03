# Operational Runbook: PostgreSQL Database Disconnection

**Alert ID**: `FLAWNETIC-ALERT-PG-001`  
**Severity**: `CRITICAL`  
**Owner**: SRE / DB Admin Team  
**Escalation Path**: Primary SRE On-Call ➔ Lead DB Engineer  

---

## 1. Symptoms & Detection
- API endpoints returning `500 Internal Server Error` with `OperationalError: connection refused`.
- `/health/ready` returns `530 Service Unavailable`.
- `/health/dependencies` reports `"postgresql": {"status": "DOWN"}`.

---

## 2. Root Cause Diagnosis
1. Inspect PostgreSQL container status:
   ```bash
   docker ps | grep postgres
   docker logs flawnetic-postgres --tail 100
   ```
2. Verify pool exhaustion vs instance down:
   ```bash
   pg_isready -h localhost -p 5432 -U flawnetic
   ```

---

## 3. Recovery Procedure
1. Restart PostgreSQL instance:
   ```bash
   docker-compose restart db
   ```
2. Check database connection pool readiness:
   ```bash
   curl http://localhost:8000/health/dependencies
   ```

---

## 4. Verification
- Execute `GET /health/ready` and confirm `200 OK`.
