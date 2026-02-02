# Security Settings

This guide covers security configuration and best practices for Tomo.

---

## Security Overview

Tomo implements multiple security layers:

| Layer | Features |
|-------|----------|
| **Authentication** | JWT tokens, bcrypt passwords |
| **Encryption** | AES-256 for credentials |
| **Session** | HttpOnly cookies, CSRF protection |
| **Network** | CORS, rate limiting |
| **Audit** | Comprehensive logging |

---

## Password Policy

### NIST SP 800-63B Compliance

Tomo follows NIST password guidelines:

| Feature | Implementation |
|---------|----------------|
| **Minimum Length** | 12 characters |
| **Maximum Length** | 128 characters |
| **Complexity** | Not required (per NIST) |
| **Blocklist** | 100,000+ common passwords |
| **Context Check** | Blocks username in password |
| **Pattern Check** | Blocks sequential/repetitive patterns |
| **Breach Check** | Optional Have I Been Pwned integration |

### Enable Breach Checking

Check passwords against known data breaches:

1. Go to **Settings** > **Security**
2. Enable **Check Passwords Against Breaches**
3. Uses k-Anonymity (only sends first 5 chars of hash)

Or via environment:

```bash
ENABLE_HIBP=true
```

### Custom Blocklist Words

Add domain-specific words to block:

1. Go to **Settings** > **Security** > **Password Policy**
2. Add words to **Context Blocklist**

Or edit the file:
```
/var/lib/tomo/data/blocklist/context_words.txt
```

---

## Session Security

### Session Timeout

Configure automatic logout:

1. Go to **Settings** > **Security**
2. Set **Session Timeout** (minutes)

| Setting | Recommended |
|---------|-------------|
| Personal use | 60-480 minutes |
| Shared system | 15-30 minutes |
| High security | 5-15 minutes |

### Cookie Security

Sessions use secure cookies:

| Attribute | Value |
|-----------|-------|
| HttpOnly | Yes (prevents XSS) |
| Secure | Yes (HTTPS only)* |
| SameSite | Strict (prevents CSRF) |

*Secure flag requires HTTPS

### View Active Sessions

1. Go to **Settings** > **Sessions**
2. See all active sessions with:
   - User
   - IP address
   - Browser/device
   - Last activity

### Revoke Sessions

- **Single session:** Click Revoke next to session
- **All user sessions:** User profile > Revoke All
- **All sessions:** Settings > Sessions > Revoke All

---

## Account Protection

### Brute Force Protection

Automatic lockout after failed logins:

| Setting | Default | Configure |
|---------|---------|-----------|
| Max attempts | 5 | `MAX_LOGIN_ATTEMPTS` |
| Lockout duration | 15 min | `LOCKOUT_DURATION` |

### Rate Limiting

API endpoints are rate limited:

| Endpoint | Limit |
|----------|-------|
| Login | 5/minute |
| Password reset | 3/minute |
| API calls | 100/minute |

---

## Encryption

### Credential Encryption

SSH passwords and private keys are encrypted:

| Algorithm | Key Derivation |
|-----------|----------------|
| AES-256-GCM | PBKDF2 (100,000 iterations) |

### Encryption Keys

**Required environment variables:**

```bash
# Master encryption key (32+ chars)
TOMO_MASTER_PASSWORD=your-secure-master-key

# Encryption salt (16+ chars)
TOMO_SALT=your-random-salt
```

Generate secure values:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Key Rotation

To rotate encryption keys:

1. Export backup with current keys
2. Update environment variables
3. Import backup (will re-encrypt with new keys)

---

## JWT Authentication

### Token Configuration

| Setting | Default | Environment Variable |
|---------|---------|---------------------|
| Secret key | Required | `JWT_SECRET_KEY` |
| Algorithm | HS256 | - |
| Expiry | 60 min | `JWT_EXPIRY` |

### Generate JWT Secret

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## CORS Configuration

Configure allowed origins:

```bash
# Single origin
ALLOWED_ORIGINS=https://tomo.example.com

# Multiple origins
ALLOWED_ORIGINS=https://tomo.example.com,https://admin.example.com
```

---

## HTTPS Configuration

### Enable HTTPS

**Option 1: Nginx with Certbot**

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tomo.example.com
```

**Option 2: Reverse Proxy**

Use Nginx Proxy Manager or Traefik in front of Tomo.

### Force HTTPS

After enabling SSL:

```bash
FORCE_HTTPS=true
```

---

## Agent Security

### Agent Authentication

Agents connect using secure tokens:

| Feature | Description |
|---------|-------------|
| Token rotation | Automatic every 24 hours |
| TLS encryption | WebSocket over TLS |
| Command allowlist | Only approved commands |

### Rotate Agent Tokens

```bash
tomo agent rotate-token <server-id>
```

Or rotate all:

```bash
tomo agent rotate-all
```

### Agent Command Allowlist

Agents only execute approved commands. The allowlist is configured per-server.

---

## Audit Logging

### What's Logged

| Event Category | Examples |
|----------------|----------|
| Authentication | Login, logout, failed attempts |
| User Management | Create, update, delete users |
| Server Actions | Add, remove, connect to servers |
| Application | Deploy, start, stop, delete |
| Settings | Configuration changes |
| Security | Password changes, session revocation |

### Log Security

Audit logs are:
- Tamper-evident (hashed)
- Sanitized (no passwords/keys)
- Timestamped (UTC)

### View Audit Logs

1. Go to **Settings** > **Audit Logs**
2. Filter by:
   - Date range
   - User
   - Action type
   - Severity

### Export Logs

```bash
tomo audit export --from 2024-01-01 --to 2024-01-31
```

---

## Security Checklist

### Initial Setup

- [ ] Use strong admin password
- [ ] Set JWT secret key
- [ ] Set encryption keys
- [ ] Configure allowed origins
- [ ] Enable HTTPS

### Ongoing

- [ ] Review audit logs regularly
- [ ] Rotate agent tokens periodically
- [ ] Update to latest version
- [ ] Remove unused users
- [ ] Revoke unused sessions

### Before Going Public

- [ ] Enable HTTPS (required)
- [ ] Configure firewall
- [ ] Set short session timeout
- [ ] Enable breach checking
- [ ] Review all user permissions

---

## Environment Variables Reference

| Variable | Purpose | Required |
|----------|---------|----------|
| `JWT_SECRET_KEY` | Token signing | Yes |
| `TOMO_MASTER_PASSWORD` | Credential encryption | Yes |
| `TOMO_SALT` | Encryption salt | Yes |
| `ALLOWED_ORIGINS` | CORS origins | Recommended |
| `SESSION_TIMEOUT` | Session duration | No |
| `MAX_LOGIN_ATTEMPTS` | Lockout threshold | No |
| `LOCKOUT_DURATION` | Lockout time | No |
| `ENABLE_HIBP` | Breach checking | No |
| `FORCE_HTTPS` | Require HTTPS | Recommended |

---

## Troubleshooting

### CORS Errors

Add your domain to `ALLOWED_ORIGINS`:

```bash
ALLOWED_ORIGINS=http://localhost,https://tomo.example.com
```

### Session Expires Too Fast

Increase `SESSION_TIMEOUT`:

```bash
SESSION_TIMEOUT=480  # 8 hours
```

### Account Locked Out

```bash
tomo user unlock --username <username>
```

---

## Next Steps

- [[Session-Management]] - Manage active sessions
- [[Data-Retention]] - Configure log retention
- [[Backup-and-Restore]] - Secure your backups
