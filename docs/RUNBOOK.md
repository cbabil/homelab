# Operations Runbook

> Deployment, monitoring, and troubleshooting procedures

## Deployment

### Prerequisites

- Docker and Docker Compose installed
- Domain/SSL configured (for production)
- JWT secret key generated

### Production Deployment

```bash
# 1. Clone repository
git clone <repo-url>
cd tomo

# 2. Configure environment
cp backend/.env-default backend/.env
# Edit backend/.env - set JWT_SECRET_KEY and other production values

cp frontend/.env-default frontend/.env
# Edit frontend/.env - set VITE_MCP_SERVER_URL for production

# 3. Build and start
make docker-prod

# 4. Initialize database and create admin
docker compose exec backend python src/cli.py init-db
docker compose exec backend python src/cli.py create-admin

# 5. Verify
curl http://localhost:8000/health
```

### Docker Compose Commands

| Command | Description |
|---------|-------------|
| `make docker-prod` | Start production containers |
| `make docker-prod-down` | Stop production containers |
| `make docker-logs` | View container logs |
| `docker compose ps` | Check container status |
| `docker compose restart backend` | Restart backend only |

### Manual Deployment (Bare Metal)

```bash
# Use the install script
chmod +x install.sh
sudo ./install.sh

# Or manually:
# 1. Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Setup frontend
cd frontend
yarn install
yarn build

# 3. Configure systemd service (see install.sh for template)
```

## Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Check MCP server status
curl http://localhost:8000/mcp

# Database connectivity
cd backend && source venv/bin/activate
python src/cli.py check-db
```

### Log Locations

| Component | Location |
|-----------|----------|
| Backend (Docker) | `docker compose logs backend` |
| Backend (Bare Metal) | `journalctl -u tomo-backend` |
| Frontend (Build) | Static files, no runtime logs |
| Database | `backend/data/tomo.db` |

### Key Metrics to Monitor

- Backend response time (< 500ms)
- Database size growth
- Failed login attempts (security)
- SSH connection pool usage

## Common Issues

### Backend Won't Start

**Symptoms:** Port 8000 already in use

```bash
# Find and kill process
lsof -i :8000
kill <PID>
```

**Symptoms:** Module not found errors

```bash
# Reinstall dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Build Fails

**Symptoms:** TypeScript errors

```bash
cd frontend
yarn type-check  # See specific errors
```

**Symptoms:** Dependency issues

```bash
rm -rf node_modules yarn.lock
yarn install
```

### Database Issues

**Symptoms:** Database locked

```bash
# Stop all connections
make docker-prod-down
# or: pkill -f "python src/main.py"

# Check for corruption
sqlite3 backend/data/tomo.db "PRAGMA integrity_check;"
```

**Symptoms:** Migration needed

```bash
cd backend && source venv/bin/activate
python src/cli.py init-db
```

### Authentication Failures

**Symptoms:** JWT validation errors

```bash
# Check JWT_SECRET_KEY is set
grep JWT_SECRET_KEY backend/.env

# Regenerate if needed
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

**Symptoms:** Account locked

```bash
cd backend && source venv/bin/activate
python reset_admin_password.py --password "NewSecurePassword123!"
```

### SSH Connection Issues

**Symptoms:** Server connection timeouts

```bash
# Check SSH_TIMEOUT setting
grep SSH_TIMEOUT backend/.env

# Test SSH manually
ssh -o ConnectTimeout=10 user@server
```

## Backup & Restore

### Create Backup

```bash
make backup
# Creates: backend/backup.enc (encrypted)
```

### Restore Backup

```bash
make restore FILE=backup.enc
# Prompts for encryption password
```

### Manual Database Backup

```bash
# SQLite backup
cp backend/data/tomo.db backend/data/tomo.db.backup

# With timestamp
cp backend/data/tomo.db "backend/data/tomo-$(date +%Y%m%d-%H%M%S).db"
```

## Rollback Procedures

### Code Rollback

```bash
# List recent deployments
git log --oneline -10

# Rollback to specific commit
git checkout <commit-hash>
make docker-prod
```

### Database Rollback

```bash
# Stop services
make docker-prod-down

# Restore from backup
cp backend/data/tomo.db.backup backend/data/tomo.db

# Restart
make docker-prod
```

### Emergency Procedures

**Complete Reset:**

```bash
# Stop everything
make docker-prod-down

# Remove data (DESTRUCTIVE)
rm -rf backend/data/tomo.db

# Reinitialize
make docker-prod
docker compose exec backend python src/cli.py init-db
docker compose exec backend python src/cli.py create-admin
```

## Security Procedures

### Rotate JWT Secret

```bash
# 1. Generate new secret
NEW_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(64))")

# 2. Update backend/.env
sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$NEW_SECRET/" backend/.env

# 3. Restart backend (invalidates all sessions)
make docker-prod-down
make docker-prod
```

### Review Failed Logins

```bash
cd backend && source venv/bin/activate
python src/cli.py audit-logins --failed --last-24h
```

### Unlock Account

```bash
cd backend && source venv/bin/activate
python src/cli.py unlock-account --username <user>
```

---

*Last updated: 2026-01-22*
