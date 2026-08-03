# Operational Guide: Database Backup & Restore Procedure

**Recovery Time Objective (RTO)**: ≤ 15 minutes  
**Recovery Point Objective (RPO)**: ≤ 5 minutes  

---

## 1. Automated Snapshot Backup Procedure
Backups are executed automatically every 6 hours via Celery Cron / Systemd timer.

Manual Backup Execution:
```bash
python -c "from scripts.disaster_recovery import dr_manager; print(dr_manager.create_backup_snapshot())"
```

---

## 2. Backup Integrity Verification
Every generated snapshot is verified for completeness:
```bash
python -c "from scripts.disaster_recovery import dr_manager; dr_manager.verify_restore_procedure('backend/reports/backups/<snapshot>.json')"
```

---

## 3. Disaster Recovery Failover Procedure
1. Halt write operations on API layer:
   ```bash
   docker-compose -f docker-compose.prod.yml stop api worker
   ```
2. Restore database state from verified snapshot:
   ```bash
   docker-compose -f docker-compose.prod.yml exec -T postgres psql -U flawnetic -d flawnetic_db < backup.sql
   ```
3. Restart API & Workers and perform post-restore smoke check:
   ```bash
   docker-compose -f docker-compose.prod.yml start api worker
   curl http://localhost:8000/health/ready
   ```
