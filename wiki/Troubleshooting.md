# Troubleshooting

This guide helps you solve common problems with Tomo.

---

## Quick Diagnostics

### Check Service Status

```bash
sudo systemctl status tomo
```

### View Logs

```bash
# Real-time logs
journalctl -u tomo -f

# Last 100 lines
journalctl -u tomo -n 100
```

### Test Connection

```bash
curl -I http://localhost:8000/health
```

---

## Installation Issues

### DEB Package Won't Install

**Error:** `dpkg: dependency problems`

**Solution:**
```bash
sudo apt update
sudo apt --fix-broken install
sudo apt install ./tomo_*.deb
```

---

**Error:** `E: Unable to locate package`

**Solution:** Download the package directly:
```bash
wget https://github.com/cbabil/tomo/releases/latest/download/tomo_1.0.0-1_amd64.deb
```

---

### Service Won't Start

**Check logs:**
```bash
journalctl -u tomo -e
```

**Common causes:**

| Cause | Solution |
|-------|----------|
| Port in use | Change port or stop conflicting service |
| Database locked | Remove stale lock files |
| Missing config | Recreate environment file |

**Restart service:**
```bash
sudo systemctl restart tomo
```

---

### Docker Installation Fails

**Error:** Docker commands fail

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply group change
newgrp docker

# Verify
docker ps
```

---

## Authentication Issues

### Cannot Log In

**Causes and solutions:**

| Symptom | Cause | Solution |
|---------|-------|----------|
| "Invalid credentials" | Wrong password | Try again or reset |
| "Account locked" | Too many attempts | Wait 15 min or unlock |
| Blank page | JavaScript error | Clear browser cache |
| Redirect loop | Cookie issue | Clear cookies |

**Reset admin password:**
```bash
tomo admin reset-password
```

**Unlock account:**
```bash
tomo user unlock --username admin
```

---

### Session Expires Immediately

**Causes:**
- Clock skew between client and server
- Cookie settings issue
- Short session timeout

**Solutions:**
```bash
# Check server time
date

# Sync time
sudo timedatectl set-ntp true

# Increase timeout
# Edit /etc/tomo/environment
SESSION_TIMEOUT=60
```

---

### CORS Errors

**Error:** `Access-Control-Allow-Origin` error in browser

**Solution:** Add your domain to allowed origins:

```bash
# Edit environment file
ALLOWED_ORIGINS=http://localhost,https://tomo.example.com

# Restart service
sudo systemctl restart tomo
```

---

## Server Connection Issues

### SSH Connection Fails

**Error:** "Connection refused"

| Check | Command |
|-------|---------|
| SSH running | `systemctl status ssh` |
| Port open | `nc -zv HOST 22` |
| Firewall | `sudo ufw status` |

---

**Error:** "Authentication failed"

| Check | Solution |
|-------|----------|
| Username | Verify SSH username |
| Password | Try SSH manually first |
| Key format | Use RSA or ED25519 |
| Key permissions | `chmod 600 ~/.ssh/id_rsa` |

---

**Error:** "Host key verification failed"

The server's SSH key has changed. This could be legitimate (server reinstalled) or a security issue.

If legitimate:
```bash
ssh-keygen -R hostname
```

---

### Server Shows Offline

1. **Verify connectivity:**
   ```bash
   ping server-ip
   ssh user@server-ip
   ```

2. **Check from Tomo server:**
   ```bash
   curl -I http://server-ip:22
   ```

3. **Review stored credentials:**
   - Edit server in web UI
   - Re-enter credentials
   - Test connection

---

## Agent Issues

### Agent Won't Connect

**Check agent service:**
```bash
ssh user@server "systemctl status tomo-agent"
```

**View agent logs:**
```bash
ssh user@server "journalctl -u tomo-agent -n 50"
```

**Common issues:**

| Issue | Solution |
|-------|----------|
| Token expired | Rotate token |
| Firewall blocking | Open port 8765 |
| DNS issue | Use IP instead of hostname |

---

### Agent Keeps Disconnecting

1. Check network stability
2. Review both server and agent logs
3. Increase reconnect interval
4. Check for resource exhaustion

---

### Metrics Not Updating

1. Verify agent is connected
2. Check agent logs for errors
3. Restart agent: `tomo agent restart <id>`
4. Reinstall agent: `tomo agent install <id> --force`

---

## Application Issues

### Deployment Fails

**Check Docker:**
```bash
ssh user@server "docker info"
```

**View container logs:**
```bash
ssh user@server "docker logs container-name"
```

**Common issues:**

| Error | Solution |
|-------|----------|
| Image not found | Check image name/tag |
| Port in use | Choose different port |
| Disk full | Free up space |
| Permission denied | Check Docker permissions |

---

### Container Won't Start

1. Check container logs:
   ```bash
   docker logs container-name
   ```

2. Check resource limits:
   ```bash
   docker stats --no-stream
   ```

3. Verify volumes exist:
   ```bash
   docker volume ls
   ```

---

### Cannot Access Application

| Check | Solution |
|-------|----------|
| Container running | `docker ps` |
| Port mapping | Verify port configuration |
| Firewall | Open required ports |
| DNS/hosts | Verify hostname resolution |

---

## Database Issues

### Database Locked

**Error:** "database is locked"

**Solution:**
```bash
# Stop the service
sudo systemctl stop tomo

# Check for stale locks
lsof /var/lib/tomo/tomo.db

# Restart
sudo systemctl start tomo
```

---

### Database Corrupted

1. **Stop service:**
   ```bash
   sudo systemctl stop tomo
   ```

2. **Check database:**
   ```bash
   sqlite3 /var/lib/tomo/tomo.db "PRAGMA integrity_check;"
   ```

3. **Restore from backup if needed:**
   ```bash
   tomo backup import /path/to/backup.backup
   ```

---

## Performance Issues

### Slow Web Interface

**Causes:**
- Many servers/applications
- Large audit logs
- Browser cache issues

**Solutions:**
1. Clear browser cache
2. Enable data retention to reduce log size
3. Check server resources

---

### High CPU Usage

1. Check which process:
   ```bash
   top -c
   ```

2. Review metrics collection frequency
3. Check for runaway containers
4. Reduce concurrent operations

---

### High Memory Usage

1. Check memory by process:
   ```bash
   ps aux --sort=-%mem | head
   ```

2. Reduce number of monitored servers
3. Enable data retention
4. Restart service to clear caches

---

## Backup/Restore Issues

### Backup Fails

| Error | Solution |
|-------|----------|
| Permission denied | Check write permissions |
| Disk full | Free up space |
| Database locked | Stop service first |

---

### Restore Fails

| Error | Solution |
|-------|----------|
| Wrong password | Verify backup password |
| Corrupted file | Use different backup |
| Version mismatch | Update Tomo first |

---

### Forgot Backup Password

Unfortunately, encrypted backups cannot be recovered without the password. This is by design for security.

**Prevention:**
- Store passwords in a password manager
- Keep the password with the backup (securely)
- Test restore periodically

---

## CLI Issues

### Command Not Found

```bash
# Check if installed
which tomo

# Add to PATH if needed
export PATH=$PATH:/usr/local/bin

# For permanent fix, add to ~/.bashrc
echo 'export PATH=$PATH:/usr/local/bin' >> ~/.bashrc
```

---

### Cannot Connect to Server

```bash
# Check server URL
tomo config show

# Set correct URL
export TOMO_SERVER_URL=http://localhost:8000
```

---

## Getting More Help

### Collect Diagnostic Info

```bash
# System info
uname -a
cat /etc/os-release

# Service status
systemctl status tomo

# Recent logs
journalctl -u tomo -n 200 > tomo-logs.txt

# Database info
ls -la /var/lib/tomo/
```

### Report an Issue

1. Collect diagnostic info above
2. Go to [GitHub Issues](https://github.com/cbabil/tomo/issues)
3. Use the bug report template
4. Include relevant logs (sanitize sensitive data)

---

## Next Steps

- [[FAQ]] - Frequently asked questions
- [[Error-Messages]] - Error reference
- [[Configuration]] - Configuration options
