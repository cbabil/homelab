# Troubleshooting Guide

This guide helps resolve common issues with Tomo.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Backend Issues](#backend-issues)
- [Frontend Issues](#frontend-issues)
- [Authentication Issues](#authentication-issues)
- [Server Connection Issues](#server-connection-issues)
- [Database Issues](#database-issues)
- [CLI Issues](#cli-issues)
- [Agent Issues](#agent-issues)

---

## Installation Issues

### Python dependencies fail to install

**Symptoms:**
- `pip install` fails with compilation errors
- Missing system libraries

**Solutions:**

1. Ensure Python 3.12+ is installed:
   ```bash
   python --version
   ```

2. Install system dependencies (Ubuntu/Debian):
   ```bash
   sudo apt-get install build-essential libffi-dev python3-dev
   ```

3. Install system dependencies (macOS):
   ```bash
   xcode-select --install
   ```

4. Use a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Node.js dependencies fail to install

**Symptoms:**
- `yarn install` fails
- npm ERR! messages

**Solutions:**

1. Clear yarn cache:
   ```bash
   yarn cache clean
   ```

2. Delete node_modules and reinstall:
   ```bash
   rm -rf node_modules yarn.lock
   yarn install
   ```

3. Ensure Node.js 18+ is installed:
   ```bash
   node --version
   ```

---

## Backend Issues

### Backend won't start

**Symptoms:**
- "Environment variable not set" errors
- Server exits immediately

**Solutions:**

1. Copy and configure environment file:
   ```bash
   cp .env.example .env
   ```

2. Generate required secrets:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   # Add output to JWT_SECRET_KEY in .env
   
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   # Add output to TOMO_MASTER_PASSWORD in .env
   
   python -c "import secrets; print(secrets.token_urlsafe(16))"
   # Add output to TOMO_SALT in .env
   ```

3. Check all required variables are set:
   ```bash
   grep -E "^(JWT_SECRET_KEY|TOMO_MASTER_PASSWORD|TOMO_SALT)=" .env
   ```

### Port already in use

**Symptoms:**
- "Address already in use" error
- Backend fails to bind to port 8000

**Solutions:**

1. Find process using the port:
   ```bash
   lsof -i :8000
   ```

2. Kill the process:
   ```bash
   kill -9 <PID>
   ```

3. Or use a different port:
   ```bash
   uvicorn src.main:app --port 8001
   ```

### Database errors

**Symptoms:**
- "Unable to open database file"
- "Database is locked"

**Solutions:**

1. Check data directory exists:
   ```bash
   mkdir -p backend/data
   ```

2. Check file permissions:
   ```bash
   chmod 755 backend/data
   ```

3. If database is corrupted, reset:
   ```bash
   rm backend/data/tomo.db
   # Restart backend to recreate database
   ```

---

## Frontend Issues

### Frontend can't connect to backend

**Symptoms:**
- Network errors in browser console
- "Failed to fetch" messages
- CORS errors

**Solutions:**

1. Verify backend is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check VITE_MCP_SERVER_URL in frontend/.env:
   ```bash
   # Development
   VITE_MCP_SERVER_URL=http://localhost:8000/mcp
   
   # Production (with reverse proxy)
   VITE_MCP_SERVER_URL=/mcp
   ```

3. Check CORS configuration in backend:
   ```bash
   # .env
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
   ```

### Blank page or loading forever

**Symptoms:**
- Page shows loading spinner indefinitely
- Browser console shows JavaScript errors

**Solutions:**

1. Clear browser cache and local storage
2. Check browser console for errors (F12)
3. Rebuild frontend:
   ```bash
   cd frontend
   rm -rf dist node_modules
   yarn install
   yarn build
   ```

### Build fails

**Symptoms:**
- TypeScript errors during build
- Module not found errors

**Solutions:**

1. Check TypeScript version:
   ```bash
   yarn tsc --version
   ```

2. Clear build cache:
   ```bash
   rm -rf dist .tsbuildinfo
   ```

3. Run type check:
   ```bash
   yarn tsc --noEmit
   ```

---

## Authentication Issues

### Can't log in

**Symptoms:**
- "Invalid credentials" error
- Login page reloads

**Solutions:**

1. Verify user exists:
   ```bash
   sqlite3 backend/data/tomo.db "SELECT username, is_active FROM users;"
   ```

2. Reset password using CLI:
   ```bash
   yarn tomo user reset-password -u <username>
   ```

3. Check if account is active:
   ```bash
   sqlite3 backend/data/tomo.db "UPDATE users SET is_active=1 WHERE username='<username>';"
   ```

### Session expires too quickly

**Symptoms:**
- Logged out frequently
- "Session expired" messages

**Solutions:**

1. Check JWT configuration in backend
2. Verify system clock is synchronized
3. Check for browser extensions blocking cookies

### No admin account exists

**Symptoms:**
- Setup page keeps appearing
- Can't create admin from CLI

**Solutions:**

1. Use the setup page at http://localhost:3000/setup
2. Or create admin via CLI:
   ```bash
   yarn tomo admin create
   ```

---

## Server Connection Issues

### SSH connection fails

**Symptoms:**
- "Connection refused" when testing server
- "Authentication failed" errors

**Solutions:**

1. Verify server is reachable:
   ```bash
   ping <server-ip>
   ```

2. Test SSH manually:
   ```bash
   ssh -v user@server-ip
   ```

3. Check SSH port (default 22):
   ```bash
   nc -zv <server-ip> 22
   ```

4. Verify credentials in Tomo are correct

### Host key verification failed

**Symptoms:**
- "Host key verification failed" in development
- Strict host checking errors in production

**Solutions:**

Development mode (`PYTHON_ENV=development`):
- Host key checking is relaxed

Production mode (`PYTHON_ENV=production`):
1. Add server to known_hosts first:
   ```bash
   ssh-keyscan <server-ip> >> ~/.ssh/known_hosts
   ```

### Server shows as offline

**Symptoms:**
- Server card shows "Offline" status
- Can't connect to server

**Solutions:**

1. Verify server is running and accessible
2. Check if SSH service is running on target server
3. Verify firewall allows SSH connections
4. Check Tomo server credentials

---

## Database Issues

### Data not persisting

**Symptoms:**
- Settings reset after restart
- Servers disappear

**Solutions:**

1. Check DATA_DIRECTORY in .env:
   ```bash
   DATA_DIRECTORY=./data
   ```

2. Verify database file exists:
   ```bash
   ls -la backend/data/tomo.db
   ```

3. Check write permissions

### Migration errors

**Symptoms:**
- "Table already exists" errors
- Schema mismatch errors

**Solutions:**

1. Backup existing database
2. Check current schema:
   ```bash
   sqlite3 backend/data/tomo.db ".schema"
   ```

---

## CLI Issues

### Command not found

**Symptoms:**
- "tomo: command not found"

**Solutions:**

1. Build CLI first:
   ```bash
   cd cli
   yarn build
   ```

2. Run with yarn:
   ```bash
   yarn tomo <command>
   ```

3. Or link globally:
   ```bash
   npm link
   ```

### CLI can't connect to backend

**Symptoms:**
- "Connection refused" errors
- "Failed to connect to MCP server"

**Solutions:**

1. Verify backend is running
2. Specify correct MCP URL:
   ```bash
   yarn tomo admin create -m http://localhost:8000/mcp
   ```

3. Set environment variable:
   ```bash
   export MCP_SERVER_URL=http://localhost:8000/mcp
   ```

---

## Agent Issues

### Agent won't connect

**Symptoms:**
- Agent shows "Connection failed" errors
- Agent status stuck on "PENDING" or "DISCONNECTED"

**Solutions:**

1. Verify backend WebSocket is accessible:
   ```bash
   curl -i http://localhost:8000/ws/agent
   # Should return 426 Upgrade Required
   ```

2. Check agent state file exists:
   ```bash
   cat ~/.tomo/agent_state.json
   ```

3. Verify registration code hasn't expired (30-day validity)

4. Re-register agent if needed:
   ```bash
   tomo agent install <server-id>
   ```

### Token rotation fails

**Symptoms:**
- "Failed to send rotation to agent" error
- Agent disconnects during rotation
- Rotation times out

**Solutions:**

1. **Agent must be connected** - Check agent status:
   ```bash
   tomo agent status <server-id>
   ```

2. **Check WebSocket connection** - The rotation command is sent via WebSocket. If the agent is disconnected, rotation cannot proceed.

3. **Grace period issue** - If rotation started but agent didn't save new token, both old and new tokens are valid during grace period (default: 5 minutes). Wait and retry.

4. **Cancel stuck rotation** - If rotation is stuck with a pending token:
   ```sql
   sqlite3 backend/data/tomo.db \
     "UPDATE agents SET pending_token_hash=NULL WHERE server_id='<server-id>';"
   ```

5. **Manual rotation** - Trigger rotation manually:
   ```bash
   tomo agent rotate <server-id>
   ```

### Agent token expired

**Symptoms:**
- Agent shows "Token expired" or authentication failures
- Agent was offline when automatic rotation was attempted

**Solutions:**

1. **Reconnect agent** - When the agent reconnects, it will trigger automatic rotation completion if a pending token exists.

2. **Force re-registration** - If the old token is completely invalid:
   ```bash
   # On the agent server
   rm ~/.tomo/agent_state.json

   # On the admin CLI
   tomo agent install <server-id>
   ```

3. **Check rotation settings** - Ensure rotation interval isn't too short:
   - Default: 7 days (`agent_token_rotation_days`)
   - Grace period: 5 minutes (`agent_token_grace_period_minutes`)

### Automatic rotation not working

**Symptoms:**
- Agents with expired tokens are not being rotated
- No rotation attempts in logs

**Solutions:**

1. **Check scheduler is running** - Look for "Rotation scheduler started" in logs

2. **Verify agents have expiry set**:
   ```sql
   sqlite3 backend/data/tomo.db \
     "SELECT id, server_id, token_expires_at FROM agents;"
   ```

3. **Check for pending rotations**:
   ```sql
   sqlite3 backend/data/tomo.db \
     "SELECT id, pending_token_hash IS NOT NULL as has_pending FROM agents;"
   ```

4. **Force expiry check** - The scheduler runs hourly. Restart the backend to trigger immediate check.

---

## FAQ

### How do I reset everything?

```bash
# Stop all services
# Remove database
rm backend/data/tomo.db

# Clear frontend cache
rm -rf frontend/dist frontend/node_modules

# Reinstall dependencies
cd frontend && yarn install
cd ../backend && pip install -r requirements.txt

# Start fresh
```

### How do I check logs?

Backend logs:
```bash
# Run with debug logging
MCP_LOG_LEVEL=DEBUG python src/main.py
```

Frontend logs:
- Open browser developer tools (F12)
- Check Console tab

### How do I report a bug?

1. Check existing issues on GitHub
2. Include:
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages/logs
   - Environment (OS, Node version, Python version)

---

## Getting Help

- **GitHub Issues**: [Report bugs](https://github.com/your-org/tomo/issues)
- **Documentation**: Check `/docs` directory
- **Community**: Join discussions on GitHub
