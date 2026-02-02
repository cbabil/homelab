# Settings & Configuration Guide

This guide covers all the configuration options available in Tomo settings.

## Accessing Settings

1. Click **Settings** in the left sidebar, or
2. Click **Settings** from the Dashboard quick actions, or
3. Click your user avatar and select **Settings**

## Settings Tabs Overview

| Tab | Description |
|-----|-------------|
| General | Application preferences and display options |
| Security | Security policies and session management |
| Notifications | Alert and notification preferences |
| Servers | Default server connection settings |
| Marketplaces | Repository management and sync settings |
| System | Data retention and backup options |

---

## General Settings

### Language

Select your preferred language for the interface.

- Currently supported: English
- Additional languages coming soon

### Timezone

Set your local timezone for accurate timestamps:

1. Click the timezone dropdown
2. Search or scroll to find your timezone
3. Select to apply

> **Tip**: Timestamps in logs and activity feeds will use this timezone.

### Application Name

Customize the application title shown in the header:

- Default: "Tomo"
- Useful for distinguishing multiple installations

### Session Timeout

Configure automatic logout after inactivity:

| Setting | Description |
|---------|-------------|
| 15 minutes | High security environments |
| 30 minutes | Default setting |
| 1 hour | Convenience-focused |
| 4 hours | Low-risk environments |
| Never | Not recommended |

### Docker Socket Path

Configure the Docker socket location for server connections:

- Default: `/var/run/docker.sock`
- Only change if using non-standard Docker setup

---

## Security Settings

### Password Policy

Configure password requirements for all users:

#### Minimum Length

- Range: 8-32 characters
- Recommended: 12+ characters

#### Complexity Requirements

Enable/disable requirements:

- **Uppercase letters** - At least one A-Z
- **Lowercase letters** - At least one a-z
- **Numbers** - At least one 0-9
- **Special characters** - At least one !@#$%^&*

#### Password Expiry

Set how often users must change passwords:

| Setting | Use Case |
|---------|----------|
| Never | Personal/home use |
| 90 days | Standard security |
| 60 days | Enhanced security |
| 30 days | High security environments |

### Session Management

#### Active Sessions

View all active sessions for your account:

| Column | Description |
|--------|-------------|
| Device | Browser and OS info |
| IP Address | Connection source |
| Started | Session start time |
| Last Activity | Most recent action |
| Status | Active, Idle, or Expired |

#### Terminating Sessions

1. Find the session to terminate
2. Click **Terminate** button
3. Confirm the action

> **Note**: Terminating your current session will log you out.

### Two-Factor Authentication

*(Coming Soon)*

Enable additional security with TOTP-based 2FA.

---

## Notification Settings

### Notification Types

Configure which notifications you receive:

#### System Notifications

- **Server Events** - Connection changes, errors
- **Deployment Events** - App deployment status
- **Security Alerts** - Login attempts, policy violations

#### Email Notifications

*(Requires email configuration)*

- Enable/disable email alerts
- Configure email frequency (immediate, daily digest)

### Notification Preferences

| Setting | Description |
|---------|-------------|
| Push notifications | Browser notifications |
| Sound alerts | Audio for important events |
| Desktop notifications | System-level alerts |

### Managing Notifications

1. Click the bell icon in the header
2. View all notifications
3. Mark as read or dismiss
4. Click "Clear all" to remove all

---

## Server Settings

### Default Connection Settings

Configure defaults for new server connections:

#### Default SSH Port

- Default: 22
- Change if your servers use non-standard ports

#### Default Username

- Set a default SSH username
- Can be overridden per-server

#### Connection Timeout

How long to wait for SSH connections:

| Setting | Description |
|---------|-------------|
| 10 seconds | Fast timeout |
| 30 seconds | Default |
| 60 seconds | Slow networks |
| 120 seconds | Very slow connections |

### SSH Options

#### Keep-Alive Interval

Send keep-alive packets to maintain connections:

- Default: 60 seconds
- Set to 0 to disable

#### Retry Attempts

Number of connection retries on failure:

- Default: 3 attempts
- Set to 0 for no retries

---

## Marketplace Settings

### Repository Management

#### Connected Repositories

View and manage marketplace repositories:

| Column | Description |
|--------|-------------|
| Name | Repository name |
| URL | Repository source |
| Apps | Number of applications |
| Last Sync | Most recent update |
| Status | Connected/Error |

#### Adding Repositories

1. Click **Add Repository**
2. Enter repository URL
3. Click **Connect**

#### Removing Repositories

1. Find the repository
2. Click **Remove**
3. Confirm deletion

> **Note**: Removing a repository doesn't affect already-deployed applications.

### Sync Settings

#### Auto-Sync

Enable automatic repository synchronization:

- **Enabled**: Repositories sync periodically
- **Disabled**: Manual sync only

#### Sync Interval

How often to check for updates:

| Setting | Use Case |
|---------|----------|
| 1 hour | Stay up-to-date |
| 6 hours | Default |
| 24 hours | Reduce bandwidth |
| Manual only | Full control |

---

## System Settings

### Data Retention

Configure how long to keep historical data:

#### Log Retention

| Data Type | Default | Range |
|-----------|---------|-------|
| Access Logs | 30 days | 7-365 days |
| Audit Logs | 90 days | 30-365 days |
| System Logs | 14 days | 7-90 days |

#### Cleanup Schedule

- **Automatic**: System cleans old data daily
- **Manual**: Click "Run Cleanup Now"

### Backup & Restore

#### Creating Backups

1. Go to **System** tab
2. Click **Create Backup**
3. Download the backup file

Backups include:
- Server configurations
- Application settings
- User preferences
- System settings

#### Restoring Backups

1. Click **Restore Backup**
2. Select your backup file
3. Choose what to restore:
   - All data
   - Settings only
   - Servers only
4. Confirm restoration

> **Warning**: Restoring will overwrite current data.

### System Information

View system details:

- Application version
- Backend version
- Database size
- System uptime

---

## Saving Settings

### Auto-Save

Most settings save automatically when changed.

### Manual Save

Some sections require clicking **Save Changes**:

- Look for the save button at the bottom
- Unsaved changes show a warning indicator

### Discarding Changes

Click **Cancel** or navigate away to discard unsaved changes.

---

## Settings Best Practices

### Security Recommendations

1. **Use strong password policy** - 12+ chars with complexity
2. **Enable session timeout** - 30 minutes recommended
3. **Review active sessions** - Terminate unknown sessions
4. **Regular password rotation** - 90 days for shared accounts

### Performance Recommendations

1. **Appropriate log retention** - Balance history vs. storage
2. **Reasonable sync intervals** - Don't over-sync repositories
3. **Connection timeouts** - Match your network conditions

### Backup Recommendations

1. **Regular backups** - Weekly minimum
2. **Test restores** - Verify backups work
3. **Offsite storage** - Keep copies elsewhere
4. **Before major changes** - Backup before updates

---

## Troubleshooting Settings

### "Settings Won't Save"

1. Check for validation errors (red highlights)
2. Ensure backend is connected
3. Check browser console for errors
4. Try refreshing the page

### "Session Keeps Expiring"

1. Check session timeout setting
2. Verify "Remember me" is checked on login
3. Check for cookie issues in browser

### "Notifications Not Working"

1. Check browser notification permissions
2. Verify notification settings are enabled
3. Check notification dropdown isn't filtered

---

**Related Guides:**
- [Quick Start Guide](./QUICK_START.md)
- [User Management & Security Guide](./USER_MANAGEMENT.md)
- [Backup & Restore Guide](./BACKUP_RESTORE.md)
