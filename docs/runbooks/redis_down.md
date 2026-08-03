# Operational Runbook: Redis Broker Failure

**Alert ID**: `FLAWNETIC-ALERT-REDIS-001`  
**Severity**: `CRITICAL`  
**Owner**: SRE / Platform Team  
**Escalation Path**: Primary SRE On-Call ➔ Infrastructure Lead  

---

## 1. Symptoms & Detection
- API requests enqueuing scans return `503 Service Unavailable` or log `RedisConnectionError`.
- Celery worker tasks freeze or fail to register progress events.
- `/health/dependencies` reports `"redis": {"status": "DOWN"}`.

---

## 2. Root Cause Diagnosis
1. Inspect Redis container/service status:
   ```bash
   docker ps | grep redis
   docker logs flawnetic-redis --tail 100
   ```
2. Check network connectivity and port 6379 binding:
   ```bash
   redis-cli -h localhost -p 6379 ping
   ```
3. Check system memory usage on host (OOM Killer check):
   ```bash
   dmesg -T | grep -i oom
   ```

---

## 3. Recovery Procedure
1. Restart the Redis container / service:
   ```bash
   docker-compose restart redis
   ```
2. Verify Redis status via ping:
   ```bash
   redis-cli ping  # Expected response: PONG
   ```
3. Verify Celery workers re-establish connection:
   ```bash
   docker-compose logs flawnetic-worker --tail 50
   ```
4. Verify `/health/dependencies` returns `"redis": {"status": "UP"}`.

---

## 4. Verification & Rollback
- Trigger a test scan via API `POST /api/v1/projects/{id}/scans`.
- Verify scan transitions from `PENDING` to `RUNNING` to `COMPLETED`.
