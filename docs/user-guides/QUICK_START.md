# Getting Started with Tomo

Welcome to Tomo! This guide will help you get up and running quickly.

## What is Tomo?

Tomo is a web-based management platform for your home servers and applications. It provides:

- **Server Management** - Add, configure, and monitor SSH connections to your servers
- **Application Deployment** - Deploy applications from the marketplace with one click
- **Centralized Dashboard** - View all your servers and applications in one place
- **User Management** - Multi-user support with role-based access control

## First-Time Setup

### Step 1: Create Your Admin Account

When you first access Tomo, you'll be directed to the setup page.

1. Navigate to `http://localhost:5173` (or your server URL)
2. You'll see the "Welcome to Tomo" setup screen
3. Enter your desired **admin username**
4. Create a **strong password** (minimum 12 characters with uppercase, lowercase, numbers, and special characters)
5. Confirm your password
6. Click **Create Account**

> **Tip**: The password strength indicator helps you create a secure password.

### Step 2: Sign In

After creating your account:

1. You'll be redirected to the login page
2. Enter your username and password
3. Optionally check "Remember me" to stay logged in
4. Click **Sign In**

### Step 3: Explore the Dashboard

Once logged in, you'll see the main dashboard with:

- **Stats Overview** - Quick view of your servers and applications
- **Resource Usage** - Monitor system resources
- **Quick Actions** - Shortcuts to common tasks
- **Recent Activity** - See what's happening in your tomo

## Adding Your First Server

### From the Dashboard

1. Click **Manage Servers** in Quick Actions, or
2. Click **Servers** in the left sidebar

### Add Server Dialog

1. Click **Add Server** button
2. Fill in the server details:
   - **Server Name** - A friendly name (e.g., "Media Server")
   - **Hostname** - IP address or domain (e.g., `192.168.1.100`)
   - **Port** - SSH port (default: 22)
   - **Username** - SSH user (e.g., `admin`)
   - **Authentication** - Choose password or SSH key

3. Click **Save**

### Connect to Your Server

1. Find your server in the list
2. Click the **Connect** button
3. Once connected, you can:
   - View server information
   - Install Docker (if not already installed)
   - Deploy applications

## Deploying Your First Application

### Browse the Marketplace

1. Click **Marketplace** in the left sidebar
2. Browse available applications by category
3. Use the search bar to find specific apps

### Deploy an Application

1. Find an application you want to deploy
2. Click the **Deploy** button on the app card
3. Select a target server from your connected servers
4. Configure deployment options (if any)
5. Click **Deploy**

### Monitor Deployment

- Check the **Applications** page to see deployment status
- View logs for troubleshooting if needed

## Key Features Overview

### Dashboard
Your central hub showing server stats, resource usage, and quick actions.

### Servers
Manage all your SSH connections. Add, edit, connect, and monitor servers.

### Applications
View and manage deployed applications across all your servers.

### Marketplace
Browse and deploy applications from curated repositories.

### Logs
View access logs and audit trails for security monitoring.

### Settings
Configure system settings, security options, and user preferences.

### Profile
Manage your account, change password, and update avatar.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | Open quick search |
| `Ctrl/Cmd + /` | Show keyboard shortcuts |
| `Esc` | Close dialogs/modals |

## Getting Help

- **Troubleshooting**: See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **CLI Reference**: See [CLI_REFERENCE.md](./CLI_REFERENCE.md)
- **Environment Variables**: See [ENV_REFERENCE.md](./ENV_REFERENCE.md)

## Next Steps

Now that you're set up:

1. **Add more servers** - Connect all your tomo machines
2. **Explore the marketplace** - Find useful applications to deploy
3. **Configure settings** - Customize themes, notifications, and security
4. **Set up additional users** - Create accounts for family members or team

---

**Need more help?** Check the detailed guides:
- [Server Management Guide](./SERVER_MANAGEMENT.md)
- [Application Deployment Guide](./APPLICATION_DEPLOYMENT.md)
- [Settings & Configuration Guide](./SETTINGS_CONFIGURATION.md)
