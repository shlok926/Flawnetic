# Operational Runbook: Celery Worker Starvation & Queue Backlog

**Alert ID**: `FLAWNETIC-ALERT-QUEUE-001`  
**Severity**: `HIGH`  
**Owner**: Platform Team / SRE  
**Escalation Path**: Primary SRE On-Call  

---

## 1. Symptoms & Detection
- Queue depth metric `queue_depth > 50` for > 5 minutes.
- Scans remaining in `PENDING` state for > 120 seconds.
- `/metrics` endpoint reports elevated `queue_depth`.

---

## 2. Recovery Procedure
1. Scale Celery worker replicas:
   ```bash
   docker-compose up -d --scale worker=8
   ```
2. Purge orphaned or dead-lettered jobs if necessary:
   ```bash
   celery -A workers.tasks purge -f
   ```
