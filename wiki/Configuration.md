# Configuration

This guide covers all configuration options for Tomo.

---

## Configuration Files

### DEB Package Installation

| File | Purpose |
|------|---------|
| `/etc/tomo/environment` | Environment variables |
| `/var/lib/tomo/tomo.db` | Database |
| `/var/log/tomo/` | Log files |

### Docker Installation

| File | Purpose |
|------|---------|
| `.env` | Environment variables |
| `./data/tomo.db` | Database (mounted volume) |

### Development

| File | Purpose |
|------|---------|
| `backend/.env` | Backend environment |
| `frontend/.env` | Frontend environment |

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret for JWT signing | 64+ character random string |
| `TOMO_MASTER_PASSWORD` | Encryption master key | 32+ character random string |
| `TOMO_SALT` | Encryption salt | 16+ character random string |

Generate secure values:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Server Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Listen address |
| `PORT` | `8000` | Backend port |
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |

### Security Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_TIMEOUT` | `60` | Session timeout (minutes) |
| `MAX_LOGIN_ATTEMPTS` | `5` | Lockout threshold |
| `LOCKOUT_DURATION` | `15` | Lockout duration (minutes) |
| `ALLOWED_ORIGINS` | `http://localhost` | CORS origins (comma-separated) |
| `ENABLE_HIBP` | `false` | Check passwords against Have I Been Pwned |

### Database Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `./data/tomo.db` | SQLite database path |
| `BACKUP_PATH` | `./backups/` | Backup directory |

### Agent Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_PORT` | `8765` | WebSocket port for agents |
| `AGENT_TOKEN_ROTATION` | `24` | Token rotation interval (hours) |

---

## Web UI Settings

Access via **Settings** page in the web interface.

### General Settings

| Setting | Description |
|---------|-------------|
| **Timezone** | Display timezone for timestamps |
| **Date Format** | Date display format |
| **Theme** | Light/Dark/System |
| **Language** | UI language |

### Security Settings

| Setting | Description |
|---------|-------------|
| **Session Timeout** | Auto-logout after inactivity |
| **Require Strong Passwords** | Enforce password complexity |
| **Two-Factor Authentication** | Enable 2FA (if configured) |

### Notification Settings

| Setting | Description |
|---------|-------------|
| **Enable Notifications** | Show in-app notifications |
| **Server Alerts** | Alert on server issues |
| **Deployment Alerts** | Alert on deployment status |

### Data Retention

| Setting | Description |
|---------|-------------|
| **Activity Logs** | How long to keep activity logs |
| **Metrics Data** | How long to keep metrics |
| **Audit Logs** | How long to keep security logs |

---

## Nginx Configuration

### DEB Package

The package installs an Nginx configuration automatically at:
```
/etc/nginx/sites-enabled/tomo
```

### Custom Domain

Edit the Nginx config:
```nginx
server {
    listen 80;
    server_name tomo.example.com;

    location / {
        root /var/www/tomo;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### SSL/TLS

For HTTPS, use Certbot:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tomo.example.com
```

---

## Database Configuration

### SQLite (Default)

Tomo uses SQLite by default. No additional configuration needed.

Database location:
- **DEB:** `/var/lib/tomo/tomo.db`
- **Docker:** `./data/tomo.db`
- **Development:** `./backend/data/tomo.db`

### Backup Database

```bash
# Manual backup
sqlite3 /var/lib/tomo/tomo.db ".backup /backup/tomo-$(date +%Y%m%d).db"

# Or use the CLI
tomo backup export
```

---

## Logging Configuration

### Log Levels

| Level | Description |
|-------|-------------|
| `DEBUG` | Verbose debugging info |
| `INFO` | General information |
| `WARNING` | Warning messages |
| `ERROR` | Error messages only |

Set via environment:
```bash
LOG_LEVEL=DEBUG
```

### Log Locations

| Installation | Location |
|--------------|----------|
| **DEB** | `/var/log/tomo/` |
| **Docker** | Container stdout/stderr |
| **Development** | Console output |

### Log Rotation

For DEB installations, logrotate is configured automatically:
```
/etc/logrotate.d/tomo
```

---

## Performance Tuning

### For High Server Count (50+)

```bash
# Increase worker processes
WORKER_PROCESSES=4

# Increase connection pool
DB_POOL_SIZE=20
```

### For Limited Resources

```bash
# Reduce memory usage
CACHE_TTL=60
METRICS_INTERVAL=60
```

---

## Troubleshooting Configuration

### Verify Environment

```bash
# Check loaded environment
tomo config show

# Test database connection
tomo config test-db

# Validate settings
tomo config validate
```

### Common Issues

| Issue | Solution |
|-------|----------|
| CORS errors | Add your domain to `ALLOWED_ORIGINS` |
| Session expires too fast | Increase `SESSION_TIMEOUT` |
| Can't connect to server | Check firewall, verify SSH credentials |

---

## Next Steps

- [[Security-Settings]] - Harden your installation
- [[Backup-and-Restore]] - Set up backups
- [[Troubleshooting]] - Solve common problems
