# User Management & Security Guide

This guide covers user account management, roles, permissions, and security best practices in Tomo.

## Overview

Tomo supports multiple users with role-based access control:

- **Admin** - Full access to all features and settings
- **User** - Limited access, cannot modify system settings

## User Roles

### Admin Role

Admins have complete control over the system:

| Permission | Description |
|------------|-------------|
| Manage Users | Create, edit, delete user accounts |
| System Settings | Configure all application settings |
| Security Settings | Set password policies, view sessions |
| Server Management | Full CRUD operations on servers |
| Application Deployment | Deploy and manage all applications |
| Marketplace | Manage repositories and sync |
| View Logs | Access all audit and access logs |
| Backup/Restore | Create and restore backups |

### User Role

Regular users have restricted access:

| Permission | Description |
|------------|-------------|
| View Dashboard | See system overview |
| View Servers | See server list (may not connect) |
| View Applications | See deployed applications |
| Browse Marketplace | View available applications |
| Personal Settings | Change own password, preferences |
| Own Profile | Update personal information |

## Creating Users

### Admin Account Creation

The first admin is created during initial setup:

1. Navigate to the setup page
2. Enter admin username and password
3. Complete setup process

### Additional Users

*(Feature availability depends on your deployment)*

To create additional users:

1. Log in as an admin
2. Navigate to Settings > Users (if available)
3. Click **Add User**
4. Fill in user details:
   - Username
   - Email (optional)
   - Password
   - Role (Admin/User)
5. Click **Create**

### Using CLI for User Management

Admins can also use the CLI:

```bash
# Create an admin user
tomo admin create -u newadmin -p SecurePassword123!

# Reset a user's password
tomo user reset-password -u username -p NewPassword123!
```

## Managing Your Profile

### Accessing Your Profile

1. Click your avatar in the header
2. Select **Profile**, or
3. Click **Profile** in the sidebar

### Profile Information

View your account details:

- **Username** - Your login name
- **Email** - Associated email address
- **Role** - Admin or User
- **Status** - Active or Inactive
- **Last Login** - Most recent sign-in

### Changing Your Avatar

1. Hover over your avatar on the Profile page
2. Click the camera icon
3. Select an image file (PNG, JPEG, GIF, WebP)
4. Preview the image
5. Click **Save** to upload

**Avatar Requirements:**
- Maximum size: 375KB
- Supported formats: PNG, JPEG, GIF, WebP
- Recommended: Square images (1:1 ratio)

### Removing Your Avatar

1. Hover over your avatar
2. Click the trash icon
3. Confirm removal

## Changing Your Password

### From Profile Page

1. Go to your Profile
2. Scroll to "Change Password" section
3. Enter your current password
4. Enter your new password
5. Confirm the new password
6. Click **Change Password**

### Password Requirements

Passwords must meet the configured policy:

| Requirement | Minimum |
|-------------|---------|
| Length | 12 characters |
| Uppercase | At least 1 |
| Lowercase | At least 1 |
| Numbers | At least 1 |
| Special chars | At least 1 |

### Password Strength Indicator

The strength indicator helps you create secure passwords:

| Strength | Indicator |
|----------|-----------|
| Weak | Red bars |
| Fair | Orange bars |
| Good | Yellow bars |
| Strong | Blue bars |
| Very Strong | Green bars |

## Session Management

### Viewing Active Sessions

1. Go to Settings > Security
2. Find "Active Sessions" section

Session information includes:
- Device type and browser
- IP address
- Session start time
- Last activity
- Status (Active/Idle/Expired)

### Understanding Session Status

| Status | Description |
|--------|-------------|
| Active | Currently in use |
| Idle | No recent activity |
| Expired | Session timed out |
| Terminated | Manually ended |

### Terminating Sessions

To end a session:

1. Find the session in the list
2. Click **Terminate**
3. Confirm the action

**Use cases:**
- Lost device
- Shared computer
- Suspicious activity
- Too many sessions

### Current Session

Your current session is marked and cannot be terminated from the session list (you would log yourself out).

## Security Best Practices

### Password Security

1. **Use unique passwords** - Don't reuse passwords from other services
2. **Use a password manager** - Generate and store complex passwords
3. **Don't share passwords** - Each user should have their own account
4. **Change passwords regularly** - At least every 90 days for shared accounts

### Account Security

1. **Review sessions regularly** - Check for unknown sessions
2. **Log out on shared devices** - Don't stay logged in on public computers
3. **Use "Remember me" wisely** - Only on personal, secured devices
4. **Report suspicious activity** - Contact admin if you notice issues

### Access Control

1. **Principle of least privilege** - Give users only needed permissions
2. **Separate admin accounts** - Don't use admin for daily tasks
3. **Audit user list** - Regularly review and remove unused accounts
4. **Document access** - Keep records of who has admin access

## Audit Logging

### What's Logged

Tomo logs security-relevant events:

| Event Type | Examples |
|------------|----------|
| Authentication | Login, logout, failed attempts |
| Authorization | Permission denied |
| User Management | User created, deleted, modified |
| Settings Changes | Security policy updates |
| Server Access | Connections, commands |

### Viewing Audit Logs

1. Navigate to **Logs** in the sidebar
2. Select **Audit Logs** tab
3. Filter by:
   - Date range
   - Event type
   - User
   - Severity

### Log Retention

Audit logs are retained based on system settings:
- Default: 90 days
- Configurable: 30-365 days

## Account Recovery

### Forgot Password

If you forget your password:

1. Contact your system administrator
2. Admin can reset password via CLI:
   ```bash
   tomo user reset-password -u yourname -p NewPassword123!
   ```

### Locked Out

If your account is locked:

1. Wait for lockout period to expire (15 minutes default)
2. Contact admin to unlock manually
3. Admin checks for brute-force attempts

### Lost Admin Access

If all admin accounts are inaccessible:

1. Use CLI with database access:
   ```bash
   tomo admin create -u newadmin -p SecurePassword123!
   ```
2. This requires server access

## Multi-User Scenarios

### Family Tomo

Recommended setup:
- 1 admin account (you)
- User accounts for family members
- Shared view access to applications

### Team Environment

Recommended setup:
- 2+ admin accounts (for redundancy)
- User accounts for team members
- Document who has admin access

### Personal Use

Recommended setup:
- 1 admin account
- Optional: separate user account for daily use
- Admin account for maintenance only

## Troubleshooting

### "Invalid Username or Password"

1. Check caps lock is off
2. Verify username spelling
3. Try password reset if forgotten
4. Check if account is locked

### "Account Locked"

1. Wait 15 minutes (default lockout)
2. Contact admin to unlock
3. Reset password after unlocking

### "Session Expired"

1. Log in again
2. Check session timeout settings
3. Enable "Remember me" for longer sessions

### "Permission Denied"

1. Verify you have the required role
2. Contact admin for access
3. Check if feature requires admin

---

**Related Guides:**
- [Quick Start Guide](./QUICK_START.md)
- [Settings & Configuration Guide](./SETTINGS_CONFIGURATION.md)
- [Troubleshooting](../TROUBLESHOOTING.md)
