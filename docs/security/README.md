# Security Documentation

This section documents security architecture, practices, and audit findings for the Tomo.

## Documents

| Document | Description |
|----------|-------------|
| [Security Review](../SECURITY_REVIEW.md) | Comprehensive security assessment |
| [Cookie Authentication](cookie-auth.md) | Secure cookie-based auth system |
| [Penetration Test Report](penetration-test-report-2025-01-11.md) | Security audit findings |

## Security Architecture Overview

### Authentication

The Tomo uses a multi-layered authentication system:

1. **JWT Tokens** - JSON Web Tokens for session management
2. **bcrypt Password Hashing** - Cost factor 12 for password storage
3. **Secure Cookies** - HTTP-only, secure, SameSite=strict cookies
4. **Session Management** - Activity tracking and automatic expiration

### Credential Protection

- **AES-256 Encryption** - SSH credentials encrypted at rest
- **PBKDF2 Key Derivation** - Master password protection
- **Fernet Encryption** - Backup file encryption

### Input Validation

- **Backend**: Pydantic models with strict validation
- **Frontend**: zod schemas for client-side validation
- **Rate Limiting**: Brute force protection on auth endpoints

## Security Best Practices

### For Operators

1. **Use Strong Master Password** - The master password protects all encrypted credentials
2. **Enable HTTPS** - Always use TLS in production
3. **Regular Backups** - Encrypted backups protect against data loss
4. **Monitor Logs** - Review security events and audit trails

### For Developers

1. **Follow Secure Coding Guidelines** - See [OWASP Top 10](https://owasp.org/www-project-top-ten/)
2. **Never Log Credentials** - Automatic sanitization is in place
3. **Validate All Input** - Use Pydantic/zod for validation
4. **Use Constant-Time Comparison** - For sensitive operations

## Security Features

### Log Sanitization

All logs automatically mask sensitive data:
- Passwords and tokens
- SSH private keys
- API keys and secrets

### Audit Trail

The `activity_log` table records:
- User actions (login, logout, operations)
- Timestamps and IP addresses
- Operation success/failure status

### Compliance

See [Data Retention Compliance](../compliance/data-retention.md) for data handling policies.

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:
1. Do not open public issues for security vulnerabilities
2. Contact the maintainers directly
3. Provide detailed reproduction steps

## Related Documentation

- [Architecture](../architecture/README.md) - System architecture
- [Operations](../operations/README.md) - Deployment and monitoring
- [Compliance](../compliance/) - Compliance documentation
