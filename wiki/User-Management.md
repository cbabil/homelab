# User Management

This guide covers creating and managing user accounts in Tomo.

---

## User Roles

Tomo supports two user roles:

| Role | Permissions |
|------|-------------|
| **Admin** | Full access to all features |
| **User** | Limited access (view only, no server management) |

---

## Creating Users

### Create Admin User (First Time)

During initial setup:

```bash
tomo admin create
```

Follow the prompts to set username and password.

### Create Additional Users

**Via Web UI:**

1. Go to **Settings** > **Users**
2. Click **Add User**
3. Fill in details:
   - Username
   - Email
   - Password
   - Role (Admin/User)
4. Click **Create**

**Via CLI:**

```bash
tomo user create
```

Or with options:

```bash
tomo user create --username john --email john@example.com --role admin
```

---

## Password Requirements

Passwords must meet NIST SP 800-63B requirements:

| Requirement | Description |
|-------------|-------------|
| **Minimum Length** | 12 characters |
| **Maximum Length** | 128 characters |
| **Blocklist** | Cannot be a common password |
| **Context** | Cannot contain username |
| **Patterns** | No sequential patterns (1234, abcd) |
| **Repetition** | No repetitive patterns (aaaa) |

### Password Blocklist

Passwords are checked against:
- Common password lists (100,000+ entries)
- Context-specific words (tomo, admin, server, etc.)
- Optionally: Have I Been Pwned database

---

## Managing Users

### View Users

1. Go to **Settings** > **Users**
2. See list of all users with:
   - Username
   - Email
   - Role
   - Last login
   - Status

### Edit User

1. Click on a user
2. Modify:
   - Email
   - Role
   - Status (Active/Disabled)
3. Click **Save**

### Reset Password

**For another user (admin only):**

1. Go to **Settings** > **Users**
2. Click on the user
3. Click **Reset Password**
4. Enter new password
5. User must change password on next login

**For yourself:**

1. Go to **Profile** (click your username)
2. Click **Change Password**
3. Enter current and new password

**Via CLI:**

```bash
# Reset admin password
tomo admin reset-password

# Reset any user password
tomo user reset-password --username john
```

### Disable User

1. Go to **Settings** > **Users**
2. Click on the user
3. Toggle **Status** to Disabled
4. Click **Save**

Disabled users:
- Cannot log in
- Active sessions are terminated
- Account is preserved

### Delete User

1. Go to **Settings** > **Users**
2. Click on the user
3. Click **Delete**
4. Confirm deletion

**Warning:** This permanently removes the user. Activity logs are preserved.

---

## Account Lockout

Accounts are automatically locked after failed login attempts:

| Setting | Default |
|---------|---------|
| **Max Attempts** | 5 |
| **Lockout Duration** | 15 minutes |
| **Reset Counter** | After successful login |

### Unlock Account

**Via Web UI (admin):**

1. Go to **Settings** > **Users**
2. Find the locked user
3. Click **Unlock**

**Via CLI:**

```bash
tomo user unlock --username john
```

---

## Session Management

### View Active Sessions

1. Go to **Settings** > **Sessions**
2. See all active sessions:
   - User
   - Device/Browser
   - IP Address
   - Login time
   - Last activity

### Revoke Session

1. Find the session
2. Click **Revoke**
3. User is logged out immediately

### Revoke All Sessions

Force logout all users:

1. Go to **Settings** > **Sessions**
2. Click **Revoke All**

Or for a specific user:

1. Go to user's profile
2. Click **Revoke All Sessions**

---

## Profile Settings

Users can manage their own profile:

1. Click username in top right
2. Go to **Profile**

Available settings:
- Email
- Password
- Timezone
- Theme preference

---

## Audit Logging

All user actions are logged:

| Event | Logged Data |
|-------|-------------|
| Login | Time, IP, device |
| Logout | Time, method |
| Failed login | Time, IP, reason |
| Password change | Time |
| User creation | By whom, details |
| User deletion | By whom |

View audit logs:
1. Go to **Settings** > **Audit Logs**
2. Filter by user, action, date

---

## CLI Reference

```bash
# List users
tomo user list

# Create user
tomo user create [--username <name>] [--email <email>] [--role <admin|user>]

# Delete user
tomo user delete --username <name>

# Reset password
tomo user reset-password --username <name>

# Unlock user
tomo user unlock --username <name>

# Disable user
tomo user disable --username <name>

# Enable user
tomo user enable --username <name>

# Admin commands
tomo admin create          # Create admin user
tomo admin reset-password  # Reset admin password
```

---

## Troubleshooting

### Cannot Create User

| Issue | Solution |
|-------|----------|
| Username exists | Choose different username |
| Invalid email | Check email format |
| Weak password | Use stronger password |

### Cannot Log In

| Issue | Solution |
|-------|----------|
| Wrong password | Try again or reset |
| Account locked | Wait or contact admin |
| Account disabled | Contact admin |
| Session expired | Log in again |

### Forgot Admin Password

If you can't log in:

```bash
# Reset admin password via CLI
tomo admin reset-password
```

This requires server access but not web login.

---

## Next Steps

- [[Security-Settings]] - Configure security options
- [[Session-Management]] - Manage sessions
- [[Data-Retention]] - Configure data cleanup
