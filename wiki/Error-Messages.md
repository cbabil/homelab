# Error Messages

Reference guide for common error messages and their solutions.

---

## Authentication Errors

### AUTH001: Invalid credentials

**Message:** "Invalid username or password"

**Cause:** The username or password is incorrect.

**Solution:**
1. Verify username (case-sensitive)
2. Check password (case-sensitive)
3. Reset password if forgotten: `tomo admin reset-password`

---

### AUTH002: Account locked

**Message:** "Account is locked due to too many failed attempts"

**Cause:** Exceeded maximum login attempts (default: 5).

**Solution:**
1. Wait for lockout to expire (default: 15 minutes)
2. Or have admin unlock: `tomo user unlock --username <name>`

---

### AUTH003: Session expired

**Message:** "Your session has expired. Please log in again."

**Cause:** Session timeout reached or server restarted.

**Solution:**
1. Log in again
2. Consider increasing `SESSION_TIMEOUT` if too short

---

### AUTH004: Invalid token

**Message:** "Authentication token is invalid or expired"

**Cause:** JWT token validation failed.

**Solution:**
1. Clear browser cookies
2. Log in again
3. Check server time sync (JWT validation is time-sensitive)

---

## Connection Errors

### CONN001: Connection refused

**Message:** "Connection refused to host:port"

**Cause:** Target service is not running or firewall blocking.

**Solution:**
1. Verify service is running on target server
2. Check firewall rules
3. Confirm correct IP/hostname and port

---

### CONN002: Connection timeout

**Message:** "Connection timed out after X seconds"

**Cause:** Network issue or server unresponsive.

**Solution:**
1. Check network connectivity
2. Verify server is online
3. Check for firewall or routing issues
4. Increase timeout if network is slow

---

### CONN003: SSH authentication failed

**Message:** "SSH authentication failed for user@host"

**Cause:** Wrong credentials or key issue.

**Solution:**
1. Verify username
2. Check password or SSH key
3. Ensure key has correct permissions (600)
4. Try connecting manually: `ssh user@host`

---

### CONN004: Host key verification failed

**Message:** "Host key verification failed"

**Cause:** Server's SSH key has changed.

**Solution:**
1. If legitimate (server reinstalled): Remove old key
   ```bash
   ssh-keygen -R hostname
   ```
2. If unexpected: Investigate potential security issue

---

## Server Errors

### SRV001: Server not found

**Message:** "Server with ID X not found"

**Cause:** Referenced server doesn't exist.

**Solution:**
1. Verify server ID
2. Refresh server list
3. Check if server was deleted

---

### SRV002: Server offline

**Message:** "Cannot connect to server: server is offline"

**Cause:** Server is unreachable.

**Solution:**
1. Check server power and network
2. Verify SSH service is running
3. Check firewall rules
4. Review server credentials

---

### SRV003: Docker not available

**Message:** "Docker is not installed or not accessible on this server"

**Cause:** Docker not installed or permission issue.

**Solution:**
1. Install Docker: **Server** > **Install Docker**
2. Or add user to docker group: `usermod -aG docker $USER`

---

## Application Errors

### APP001: Deployment failed

**Message:** "Application deployment failed"

**Cause:** Various deployment issues.

**Solution:**
1. Check container logs
2. Verify Docker is running
3. Check disk space
4. Ensure image is accessible

---

### APP002: Image not found

**Message:** "Unable to pull image: image not found"

**Cause:** Docker image doesn't exist or is private.

**Solution:**
1. Verify image name and tag
2. Check Docker Hub or registry
3. For private images, add registry credentials

---

### APP003: Port already in use

**Message:** "Port X is already in use on the host"

**Cause:** Another container or service using the port.

**Solution:**
1. Choose a different host port
2. Or stop the conflicting service:
   ```bash
   docker ps | grep :PORT
   ```

---

### APP004: Container exited

**Message:** "Container exited with code X"

**Cause:** Application crashed or misconfigured.

**Solution:**
1. Check container logs: `docker logs container-name`
2. Review environment variables
3. Check volume permissions
4. Verify health check configuration

---

## Agent Errors

### AGT001: Agent not connected

**Message:** "Agent is not connected"

**Cause:** Agent service down or network issue.

**Solution:**
1. Check agent service: `systemctl status tomo-agent`
2. Review agent logs
3. Verify network connectivity
4. Check firewall (port 8765)

---

### AGT002: Token expired

**Message:** "Agent token has expired"

**Cause:** Token not rotated properly.

**Solution:**
1. Rotate token: `tomo agent rotate-token <id>`
2. Agent will automatically reconnect

---

### AGT003: Version mismatch

**Message:** "Agent version X is not compatible with server version Y"

**Cause:** Agent needs update.

**Solution:**
1. Update agent: `tomo agent update <id>`

---

### AGT004: Command not allowed

**Message:** "Command X is not in the allowed list"

**Cause:** Security restriction on agent.

**Solution:**
1. This is by design for security
2. Only whitelisted commands can be executed
3. Use SSH for one-off commands

---

## Database Errors

### DB001: Database locked

**Message:** "Database is locked"

**Cause:** Another process has exclusive access.

**Solution:**
1. Wait for other operations to complete
2. Check for stale locks:
   ```bash
   lsof /var/lib/tomo/tomo.db
   ```
3. Restart service if needed

---

### DB002: Database corrupted

**Message:** "Database integrity check failed"

**Cause:** File corruption.

**Solution:**
1. Stop service
2. Restore from backup: `tomo backup import`
3. If no backup, attempt recovery:
   ```bash
   sqlite3 tomo.db ".recover" | sqlite3 recovered.db
   ```

---

### DB003: Migration failed

**Message:** "Database migration failed"

**Cause:** Update migration issue.

**Solution:**
1. Check migration logs
2. Restore backup from before update
3. Report issue with migration logs

---

## Backup Errors

### BKP001: Wrong password

**Message:** "Incorrect backup password"

**Cause:** Wrong password provided.

**Solution:**
1. Try the correct password
2. Backups cannot be recovered without password

---

### BKP002: Backup corrupted

**Message:** "Backup file is corrupted or invalid"

**Cause:** File damaged or incomplete.

**Solution:**
1. Verify file integrity
2. Use a different backup
3. Check if download completed properly

---

### BKP003: Version incompatible

**Message:** "Backup version X is not compatible"

**Cause:** Backup from different version.

**Solution:**
1. Update Tomo to match backup version
2. Or upgrade backup if migration path exists

---

## Configuration Errors

### CFG001: Invalid configuration

**Message:** "Configuration value X is invalid"

**Cause:** Environment variable or setting incorrect.

**Solution:**
1. Check environment file
2. Verify value format
3. See [[Configuration]] for valid values

---

### CFG002: Missing required configuration

**Message:** "Required configuration X is not set"

**Cause:** Missing environment variable.

**Solution:**
1. Add to environment file:
   ```bash
   /etc/tomo/environment
   ```
2. Restart service

---

### CFG003: CORS origin not allowed

**Message:** "Origin X is not allowed by CORS policy"

**Cause:** Accessing from non-whitelisted domain.

**Solution:**
1. Add origin to `ALLOWED_ORIGINS`:
   ```bash
   ALLOWED_ORIGINS=http://localhost,https://your-domain.com
   ```
2. Restart service

---

## Password Errors

### PWD001: Password too weak

**Message:** "Password does not meet requirements"

**Cause:** Password doesn't meet NIST requirements.

**Solution:**
1. Use at least 12 characters
2. Avoid common passwords
3. Don't include username
4. Avoid sequential patterns (1234, abcd)

---

### PWD002: Password in blocklist

**Message:** "Password is too common"

**Cause:** Password is in the common passwords list.

**Solution:**
1. Choose a unique password
2. Use a password manager to generate

---

### PWD003: Password compromised

**Message:** "Password found in X data breaches"

**Cause:** Password found in Have I Been Pwned database.

**Solution:**
1. Choose a different password
2. Check your accounts on https://haveibeenpwned.com

---

## Getting Help

If you encounter an error not listed here:

1. Check the full error in logs
2. See [[Troubleshooting]] for general guidance
3. Search [GitHub Issues](https://github.com/cbabil/tomo/issues)
4. Report new issues with full error details
