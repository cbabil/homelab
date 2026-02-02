# Security

## Password Handling

| Aspect | Implementation |
|--------|----------------|
| Input | Masked with `*` characters in terminal |
| Hashing | bcrypt with 12 salt rounds |
| Storage | Only hash stored, never plaintext |
| Memory | Password cleared after hashing |

## bcrypt Configuration

```typescript
const SALT_ROUNDS = 12;
const passwordHash = await bcrypt.hash(password, SALT_ROUNDS);
```

12 rounds provides a good balance between security and performance:

- ~250ms to hash on modern hardware
- Resistant to brute-force attacks
- Matches backend server configuration

### Why bcrypt?

- **Adaptive** - Cost factor can be increased as hardware improves
- **Salt built-in** - Each hash includes a unique salt
- **Slow by design** - Resistant to GPU-based attacks
- **Battle-tested** - Widely used and audited

## Database Access

- CLI requires direct file system access to the SQLite database
- No network exposure - all operations are local
- WAL mode enabled for safe concurrent access with backend

## Best Practices

### Do

- Use interactive mode for password entry (masked input)
- Use strong passwords (12+ characters, mixed case, numbers, symbols)
- Restrict database file permissions
- Run CLI from a secure terminal

### Don't

- Use `-p` flag in shared terminals (visible in history)
- Share passwords in scripts committed to version control
- Run CLI over unencrypted remote connections
- Leave terminal sessions unattended after use

## Command History Security

If you accidentally used `-p` with a password in the command:

### Bash

```bash
# View history with line numbers
history

# Delete specific line
history -d <line_number>

# Clear all history
history -c

# Prevent command from being saved (prefix with space)
 tomo admin create -p "secret"  # Note leading space
```

### Zsh

```bash
# Write history to file
fc -W

# Edit history file manually
nano ~/.zsh_history

# Or clear current session
fc -p
```

### Fish

```bash
# Delete specific entry
history delete --exact --case-sensitive "tomo admin create -p"

# Clear all history
history clear
```

## Secure Password Generation

Generate strong passwords before using the CLI:

```bash
# Using openssl
openssl rand -base64 16

# Using /dev/urandom
head -c 16 /dev/urandom | base64

# Using pwgen (if installed)
pwgen -s 16 1
```

## Audit Logging

The CLI does not currently implement audit logging. For production environments, consider:

1. Running CLI commands through a wrapper that logs operations
2. Monitoring database file access with OS-level auditing
3. Using the backend API with proper audit trails instead

## Network Security

The CLI is designed for local use only:

- No network listeners
- No remote connections
- Database access is file-based only

For remote administration:

1. SSH into the server
2. Run CLI commands locally
3. Or use the web interface with proper TLS

## Container Security

When running in Docker:

```dockerfile
# Mount data directory as volume
-v /host/data:/app/data

# Run as non-root user
USER node

# Read-only filesystem except data
--read-only
```

```bash
# Example Docker run
docker run -it --rm \
  -v /var/lib/tomo/data:/app/data \
  --user 1000:1000 \
  tomo-cli admin create -d /app/data
```
