# CLI Admin Commands

This page covers administrative CLI commands for user and system management.

---

## Admin Commands

### Create Admin User

Create the initial admin account:

```bash
tomo admin create
```

**Interactive prompts:**
- Username (default: admin)
- Password
- Confirm password

**With options:**

```bash
tomo admin create --username admin --password MySecurePass123
```

**Options:**

| Option | Description |
|--------|-------------|
| `--username`, `-u` | Admin username |
| `--password`, `-p` | Admin password |
| `--force` | Overwrite existing admin |

---

### Reset Admin Password

Reset the admin account password:

```bash
tomo admin reset-password
```

**Interactive prompts:**
- New password
- Confirm password

**With options:**

```bash
tomo admin reset-password --password NewSecurePass456
```

**Options:**

| Option | Description |
|--------|-------------|
| `--password`, `-p` | New password |
| `--username`, `-u` | Specific admin user |

---

## User Commands

### List Users

List all user accounts:

```bash
tomo user list
```

**Output:**
```
ID  USERNAME  EMAIL              ROLE   STATUS  LAST LOGIN
1   admin     admin@local        admin  active  2024-01-15 10:30
2   john      john@example.com   user   active  2024-01-14 15:45
3   jane      jane@example.com   admin  locked  2024-01-10 09:00
```

**Options:**

| Option | Description |
|--------|-------------|
| `--json` | JSON output |
| `--role <role>` | Filter by role |
| `--status <status>` | Filter by status |

---

### Create User

Create a new user account:

```bash
tomo user create
```

**Interactive prompts:**
- Username
- Email
- Password
- Role (admin/user)

**With options:**

```bash
tomo user create \
  --username john \
  --email john@example.com \
  --password SecurePass123 \
  --role user
```

**Options:**

| Option | Description |
|--------|-------------|
| `--username`, `-u` | Username |
| `--email`, `-e` | Email address |
| `--password`, `-p` | Password |
| `--role`, `-r` | Role (admin/user) |

---

### Delete User

Delete a user account:

```bash
tomo user delete --username john
```

**Options:**

| Option | Description |
|--------|-------------|
| `--username`, `-u` | Username to delete |
| `--force` | Skip confirmation |

**Warning:** This permanently removes the user account.

---

### Reset User Password

Reset a user's password:

```bash
tomo user reset-password --username john
```

**Interactive prompts:**
- New password
- Confirm password

**Options:**

| Option | Description |
|--------|-------------|
| `--username`, `-u` | Username |
| `--password`, `-p` | New password |

---

### Unlock User

Unlock a locked user account:

```bash
tomo user unlock --username john
```

Users get locked after too many failed login attempts.

---

### Disable User

Disable a user account (prevent login):

```bash
tomo user disable --username john
```

---

### Enable User

Re-enable a disabled user account:

```bash
tomo user enable --username john
```

---

## Session Commands

### List Sessions

List all active sessions:

```bash
tomo session list
```

**Output:**
```
ID        USER   IP            DEVICE      LAST ACTIVITY
abc123    admin  192.168.1.5   Chrome      2024-01-15 10:30
def456    john   192.168.1.10  Firefox     2024-01-15 09:45
```

**Options:**

| Option | Description |
|--------|-------------|
| `--user <name>` | Filter by user |
| `--json` | JSON output |

---

### Revoke Session

Revoke a specific session:

```bash
tomo session revoke <session-id>
```

---

### Revoke User Sessions

Revoke all sessions for a user:

```bash
tomo session revoke-user --username john
```

---

### Revoke All Sessions

Revoke all active sessions:

```bash
tomo session revoke-all
```

**Warning:** This logs out all users including yourself.

---

## Audit Commands

### View Audit Logs

View security audit logs:

```bash
tomo audit list
```

**Options:**

| Option | Description |
|--------|-------------|
| `--user <name>` | Filter by user |
| `--action <type>` | Filter by action |
| `--from <date>` | Start date |
| `--to <date>` | End date |
| `--limit <n>` | Limit results |

**Example:**

```bash
tomo audit list --user admin --action login --from 2024-01-01
```

---

### Export Audit Logs

Export audit logs to file:

```bash
tomo audit export --output audit-logs.json
```

**Options:**

| Option | Description |
|--------|-------------|
| `--output`, `-o` | Output file |
| `--format` | Format (json/csv) |
| `--from` | Start date |
| `--to` | End date |

---

## System Commands

### System Status

Check system status:

```bash
tomo status
```

**Output:**
```
Service Status:
  Backend:    Running
  Database:   Connected
  Agents:     3 connected

System Info:
  Version:    1.0.0
  Uptime:     5 days 3 hours
  Database:   45 MB
```

---

### Database Operations

**Optimize database:**

```bash
tomo db optimize
```

Reclaims space after deletions.

**Check database:**

```bash
tomo db check
```

Verifies database integrity.

---

### Configuration

**Show configuration:**

```bash
tomo config show
```

**Set configuration:**

```bash
tomo config set session_timeout 60
```

**Reset to defaults:**

```bash
tomo config reset
```

---

## Examples

### Create Multiple Users

```bash
#!/bin/bash
users=("alice" "bob" "charlie")
for user in "${users[@]}"; do
  tomo user create \
    --username "$user" \
    --email "${user}@example.com" \
    --role user \
    --password "TempPass123!"
done
```

### Audit Failed Logins

```bash
tomo audit list \
  --action failed_login \
  --from "$(date -d '7 days ago' +%Y-%m-%d)" \
  --json | jq '.[] | .username + " from " + .ip'
```

### Cleanup Inactive Users

```bash
tomo user list --json | \
  jq -r '.[] | select(.last_login < "2024-01-01") | .username' | \
  while read user; do
    echo "Disabling inactive user: $user"
    tomo user disable --username "$user"
  done
```

---

## Next Steps

- [[CLI-Backup-Commands]] - Backup commands
- [[CLI-Agent-Commands]] - Agent commands
- [[CLI-Overview]] - CLI overview
