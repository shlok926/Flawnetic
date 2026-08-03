# Operational Guide: Enterprise Production Deployment

**Target Systems**: Staging & Production Clusters  
**Supported Deployment Models**: Rolling Update (Zero Downtime) & Blue-Green  

---

## 1. Prerequisites
- Docker & Docker Compose v2.20+
- Access to configured Production Environment variables (`.env`)
- Passed CI/CD verification gate (100% test pass, coverage ≥ 90%)

---

## 2. Deployment Execution Steps
1. Pull latest production-certified commit (`main` or `v1.0.0-foundation` tag):
   ```bash
   git checkout main && git pull origin main
   ```
2. Validate environment configuration:
   ```bash
   python -c "from config.settings import settings; print('Env validated:', settings.environment)"
   ```
3. Execute database schema migration:
   ```bash
   venv/Scripts/python.exe -m alembic upgrade head
   ```
4. Perform Rolling Update using production compose profile:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

---

## 3. Post-Deployment Verification (Smoke Tests)
- Verify API Liveness & Readiness:
  ```bash
  curl http://localhost:8000/health/live
  curl http://localhost:8000/health/ready
  curl http://localhost:8000/health/dependencies
  ```
