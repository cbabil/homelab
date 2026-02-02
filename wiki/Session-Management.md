# Session Management

This guide covers viewing and managing user sessions in Tomo.

---

## Overview

Sessions track active user logins. Each session includes:

| Field | Description |
|-------|-------------|
| **User** | Who is logged in |
| **Device** | Browser/client information |
| **IP Address** | Connection source |
| **Login Time** | When session started |
| **Last Activity** | Most recent action |
| **Expires** | When session will timeout |

---

## Viewing Sessions

### Your Sessions

1. Click your username (top right)
2. Go to **Profile** > **Sessions**
3. See all your active sessions

### All Sessions (Admin)

1. Go to **Settings** > **Sessions**
2. See all user sessions
3. Filter by user, IP, or date

### Session Details

Click on any session to see:
- Full device information
- Login method
- Activity timeline
- Geographic location (if available)

---

## Session Security

### Session Tokens

Sessions use JWT tokens with:

| Property | Value |
|----------|-------|
| Algorithm | HS256 |
| Expiry | Configurable (default: 60 min) |
| Storage | HttpOnly cookie |
| Protection | CSRF token required |

### Automatic Timeout

Sessions expire after inactivity:

| Setting | Default | Configure |
|---------|---------|-----------|
| Timeout | 60 minutes | Settings > Security |

Activity resets the timer:
- Page navigation
- API calls
- User interactions

### Session Cookie Attributes

| Attribute | Value | Purpose |
|-----------|-------|---------|
| HttpOnly | Yes | Prevents XSS access |
| Secure | Yes* | HTTPS only |
| SameSite | Strict | Prevents CSRF |
| Path | / | All routes |

*Secure flag active when using HTTPS

---

## Revoking Sessions

### Revoke Single Session

**Your own session:**
1. Go to **Profile** > **Sessions**
2. Find the session
3. Click **Revoke**

**Another user's session (admin):**
1. Go to **Settings** > **Sessions**
2. Find the session
3. Click **Revoke**

### Revoke All User Sessions

1. Go to **Settings** > **Users**
2. Click on the user
3. Click **Revoke All Sessions**

Or from the sessions page:
1. Go to **Settings** > **Sessions**
2. Filter by user
3. Click **Revoke All**

### Revoke All Sessions

Force logout everyone:

1. Go to **Settings** > **Sessions**
2. Click **Revoke All Sessions**
3. Confirm the action

**Warning:** This logs out all users including yourself.

---

## Session Limits

### Maximum Sessions Per User

Configure how many simultaneous sessions a user can have:

1. Go to **Settings** > **Security**
2. Set **Max Sessions Per User**

| Setting | Behavior |
|---------|----------|
| 0 | Unlimited sessions |
| 1 | Single session (new login revokes old) |
| 5 | Max 5 concurrent sessions |

### When Limit Reached

Options when user exceeds session limit:
- **Deny new login** - Block new session
- **Revoke oldest** - Remove oldest session

---

## Session Activity

### Activity Tracking

Each session records:
- Pages visited
- Actions performed
- Time of each action

### View Activity

1. Click on a session
2. Go to **Activity** tab
3. See chronological list

### Activity Retention

Activity data follows data retention settings. See [[Data-Retention]].

---

## Device Recognition

### Known Devices

Sessions identify devices by:
- Browser user agent
- Screen resolution
- Timezone
- Other fingerprinting

### New Device Alerts

Configure alerts for new devices:

1. Go to **Settings** > **Security**
2. Enable **New Device Alerts**
3. Get notified when you log in from new device

---

## Geographic Information

### IP Geolocation

Sessions can show:
- Country
- Region/State
- City
- ISP

**Note:** Requires geolocation service. May not be 100% accurate.

### Suspicious Location Alerts

Enable alerts for logins from unusual locations:

1. Go to **Settings** > **Security**
2. Enable **Location Alerts**

---

## Session Timeout Configuration

### Configure Timeout

**Via Web UI:**
1. Go to **Settings** > **Security**
2. Set **Session Timeout** (minutes)
3. Click **Save**

**Via Environment:**
```bash
SESSION_TIMEOUT=60  # minutes
```

### Recommended Settings

| Use Case | Timeout |
|----------|---------|
| Personal server | 480 min (8 hours) |
| Shared workstation | 30 min |
| High security | 15 min |
| Kiosk/public | 5 min |

### Remember Me

If "Remember Me" is implemented:
- Regular session: Short timeout
- Remember Me: Extended timeout (e.g., 30 days)

---

## CLI Reference

```bash
# List all sessions
tomo session list

# List sessions for user
tomo session list --user admin

# View session details
tomo session show <session-id>

# Revoke session
tomo session revoke <session-id>

# Revoke all sessions for user
tomo session revoke-user <username>

# Revoke all sessions
tomo session revoke-all

# Clean expired sessions
tomo session cleanup
```

---

## Troubleshooting

### Session Expires Too Quickly

1. Check `SESSION_TIMEOUT` setting
2. Verify server time is correct
3. Check if user is being idle
4. Review activity logs

### Cannot Revoke Session

| Issue | Solution |
|-------|----------|
| Session not found | May already be expired |
| Permission denied | Need admin role |
| Database error | Check logs |

### Duplicate Sessions

If user has many duplicate sessions:
1. Review login patterns
2. Check for automation/scripts
3. Consider setting session limits

### Session Not Persisting

| Issue | Solution |
|-------|----------|
| Cookies blocked | Enable cookies in browser |
| HTTPS mismatch | Ensure consistent protocol |
| Clock skew | Sync server time |

---

## Security Considerations

### Session Hijacking Prevention

- HttpOnly cookies prevent JavaScript access
- Secure flag requires HTTPS
- CSRF tokens protect state-changing requests
- Short timeouts limit exposure

### Session Fixation Prevention

- New session ID generated on login
- Old sessions invalidated

### Monitoring Recommendations

1. Review sessions regularly
2. Investigate unknown devices
3. Set up location alerts
4. Enable login notifications

---

## Next Steps

- [[Security-Settings]] - Configure security
- [[User-Management]] - Manage users
- [[Troubleshooting]] - Solve problems
