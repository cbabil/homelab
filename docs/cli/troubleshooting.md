# Troubleshooting

## Common Issues

### "Database not found"

**Symptom:**
```
✗ Error: Database not found at: /path/to/tomo.db
Please run the backend server first to initialize the database.
```

**Cause:** The CLI cannot locate `tomo.db`.

**Solutions:**

1. **Run the backend server first** to initialize the database:
   ```bash
   cd backend
   python src/main.py
   ```

2. **Find the database** and specify its location:
   ```bash
   # Find the database
   find / -name "tomo.db" 2>/dev/null

   # Specify path
   tomo admin create --data-dir /path/to/data
   ```

3. **Check the expected locations:**
   - `../backend/data/tomo.db` (relative to CLI)
   - `/var/lib/tomo/data/tomo.db`
   - `~/.tomo/data/tomo.db`

---

### "User already exists"

**Symptom:**
```
✗ Error: User 'admin' already exists
```

**Cause:** A user with that username is already in the database.

**Solutions:**

1. **Use a different username:**
   ```bash
   tomo admin create -u admin2
   ```

2. **Reset the existing user's password instead:**
   ```bash
   tomo user reset-password -u admin
   ```

---

### "User not found"

**Symptom:**
```
✗ Error: User 'admin' not found
```

**Cause:** The specified username doesn't exist in the database.

**Solutions:**

1. **Check the username spelling** (case-sensitive)

2. **List existing users** by checking the database:
   ```bash
   sqlite3 /path/to/tomo.db "SELECT username FROM users;"
   ```

3. **Create the user instead:**
   ```bash
   tomo admin create -u admin
   ```

---

### "SQLITE_BUSY" or Database Locked

**Symptom:**
```
SQLITE_BUSY: database is locked
```

**Cause:** Another process has an exclusive lock on the database.

**Solutions:**

1. **Wait and retry** - The lock may be temporary

2. **Stop the backend server** temporarily:
   ```bash
   # Stop server, run CLI, restart server
   ```

3. **Check for zombie processes:**
   ```bash
   lsof /path/to/tomo.db
   fuser /path/to/tomo.db
   ```

4. **Remove stale lock files** (use with caution):
   ```bash
   rm /path/to/tomo.db-wal
   rm /path/to/tomo.db-shm
   ```

---

### Permission Denied

**Symptom:**
```
SQLITE_CANTOPEN: unable to open database file
# or
Error: EACCES: permission denied
```

**Cause:** Insufficient file system permissions.

**Solutions:**

1. **Check permissions:**
   ```bash
   ls -la /path/to/data/
   ls -la /path/to/data/tomo.db
   ```

2. **Fix file permissions:**
   ```bash
   chmod 644 /path/to/data/tomo.db
   chmod 755 /path/to/data/
   ```

3. **Fix ownership:**
   ```bash
   chown $USER /path/to/data/tomo.db
   ```

4. **Run with appropriate user:**
   ```bash
   sudo -u tomo tomo admin create
   ```

---

### "command not found: tomo"

**Symptom:**
```
zsh: command not found: tomo
# or
bash: tomo: command not found
```

**Cause:** The CLI is not linked globally or not in PATH.

**Solutions:**

1. **Link globally:**
   ```bash
   cd cli
   npm link
   ```

2. **Run directly:**
   ```bash
   node /path/to/cli/dist/bin/tomo.js --help
   ```

3. **Check npm global bin directory:**
   ```bash
   npm bin -g
   # Add to PATH if needed
   export PATH=$(npm bin -g):$PATH
   ```

---

### Build Errors

**Symptom:**
```
tsc: command not found
# or
Cannot find module 'typescript'
```

**Solutions:**

1. **Install dependencies:**
   ```bash
   cd cli
   npm install
   ```

2. **Use npx:**
   ```bash
   npx tsc
   ```

3. **Check Node version:**
   ```bash
   node --version  # Should be 18+
   ```

---

### Validation Errors

**Symptom:**
```
? Enter admin username: ab
Username must be at least 3 characters
```

**Solutions:**

Follow the validation rules:

| Field | Requirement |
|-------|-------------|
| Username | At least 3 characters |
| Email | Valid email format (user@domain.com) |
| Password | At least 8 characters |

---

## Debug Mode

For verbose debugging output:

```bash
# Node.js debug output
NODE_DEBUG=* node dist/bin/tomo.js admin create

# SQLite verbose mode (modify db.ts temporarily)
db.pragma('journal_mode = WAL');
db.verbose(console.log);
```

## Getting Help

1. **Check this documentation**

2. **Use built-in help:**
   ```bash
   tomo --help
   tomo admin --help
   tomo admin create --help
   ```

3. **Check GitHub Issues** for known problems

4. **Collect diagnostic info** before reporting:
   ```bash
   node --version
   npm --version
   tomo --version
   uname -a
   ```
