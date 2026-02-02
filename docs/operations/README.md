# Operations Documentation

This section covers deployment, monitoring, and administrative procedures for the Tomo.

## Documents

| Document | Description |
|----------|-------------|
| [Data Retention Monitoring](data-retention-monitoring.md) | Monitoring data retention policies |
| [Admin Procedures](../admin/data-retention-security-procedures.md) | Security administration procedures |

## Deployment

### Development Setup

```bash
# Clone and setup
git clone https://github.com/cbabil/tomo.git
cd tomo
make setup
make dev
```

Access at: http://localhost:5173

### Production Deployment

#### Docker (Recommended)

```bash
# Build and run
docker-compose up -d

# Or build image directly
docker build -t tomo .
docker run -p 80:80 -v tomo_data:/app/data tomo
```

#### RPM Package

```bash
# Build RPM
rpmbuild -ba packaging/tomo.spec

# Install
sudo dnf install tomo-1.0.0-1.x86_64.rpm

# Start service
sudo systemctl start tomo
sudo systemctl enable tomo
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET_KEY` | Yes | JWT signing secret |
| `TOMO_MASTER_PASSWORD` | Yes | Encryption master password |
| `TOMO_SALT` | Yes | Encryption salt |
| `DATA_DIRECTORY` | No | Data storage path |
| `MCP_LOG_LEVEL` | No | Logging level (INFO) |
| `ALLOWED_ORIGINS` | No | CORS allowed origins |

### Configuration File

Production config: `/etc/tomo/config.yaml`

```yaml
server:
  host: 127.0.0.1
  port: 8080

security:
  session_timeout_minutes: 60
  max_login_attempts: 5
  lockout_duration_minutes: 15

metrics:
  enabled: true
  collection_interval_seconds: 300
  retention_days: 30
```

## Monitoring

### Health Checks

```bash
# Basic health check
curl http://localhost:8080/health

# MCP ping
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "ping"}}'
```

### Logs

- **Backend logs**: `backend/logs/app.log`
- **Docker logs**: `docker logs tomo`
- **systemd logs**: `journalctl -u tomo`

### Metrics

The system collects:
- Server health status
- Container metrics (CPU, memory)
- Activity logs and audit trails

## Backup & Recovery

### Create Backup

```bash
cd backend
python src/cli.py export -o backup.enc -p
# Enter password when prompted
```

### Restore Backup

```bash
python src/cli.py import -i backup.enc -p
# Enter password when prompted
```

### What's Included

- User accounts and settings
- Server configurations (encrypted credentials)
- Application catalog and deployments
- Activity logs

## Maintenance

### Database

```bash
# Initialize database
python src/cli.py init-db

# Create admin user
python src/cli.py create-admin
```

### Data Retention

Configure automatic cleanup in settings:
- Log retention period
- Metrics retention
- Cleanup schedules

See [Data Retention Monitoring](data-retention-monitoring.md).

## Related Documentation

- [Security](../security/README.md) - Security best practices
- [Architecture](../architecture/README.md) - System architecture
- [Developer Guide](../developer/README.md) - Development setup
