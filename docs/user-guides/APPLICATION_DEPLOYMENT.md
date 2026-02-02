# Application Deployment Guide

This guide covers how to deploy applications from the Tomo marketplace to your servers.

## Overview

The Marketplace provides a curated collection of self-hosted applications that you can deploy to your servers with just a few clicks. All applications are containerized using Docker for easy management.

## Prerequisites

Before deploying applications, ensure:

1. **At least one server added** to Tomo
2. **Server is connected** (green status indicator)
3. **Docker is installed** on the target server

## Navigating the Marketplace

### Accessing the Marketplace

1. Click **Marketplace** in the left sidebar, or
2. Click **App Marketplace** from the Dashboard quick actions

### Marketplace Layout

The marketplace has two main tabs:

- **Browse Apps** - Discover and deploy applications
- **Manage Repos** - Configure application repositories

## Browsing Applications

### Search

Use the search bar to find applications by:
- Name (e.g., "Plex", "Nextcloud")
- Description keywords
- Category

### Filter by Category

Click category buttons to filter applications:

| Category | Examples |
|----------|----------|
| Media | Plex, Jellyfin, Emby |
| Storage | Nextcloud, Syncthing |
| Monitoring | Grafana, Prometheus |
| Network | Pi-hole, AdGuard |
| Development | Gitea, GitLab |
| Automation | Home Assistant, n8n |

### Application Cards

Each application card shows:

- **Icon** - Application logo
- **Name** - Application name
- **Description** - Brief overview
- **Rating** - Community rating (if available)
- **Deploy Button** - Start deployment

## Deploying an Application

### Step 1: Select an Application

1. Browse or search for the desired application
2. Click the **Deploy** button on the app card

### Step 2: Configure Deployment

The deployment dialog will open with options:

#### Target Server

1. Select from your connected servers
2. Only servers with Docker installed are available

#### Port Configuration

Some applications require port mappings:

| Field | Description | Example |
|-------|-------------|---------|
| Host Port | Port on your server | `8080` |
| Container Port | Port inside container | `80` |

> **Tip**: Use non-conflicting ports if running multiple applications.

#### Volume Mounts

Configure persistent data storage:

| Field | Description | Example |
|-------|-------------|---------|
| Host Path | Directory on server | `/srv/app/data` |
| Container Path | Path in container | `/data` |

#### Environment Variables

Some applications require configuration via environment variables:

```
PUID=1000
PGID=1000
TZ=America/New_York
```

### Step 3: Deploy

1. Review your configuration
2. Click **Deploy**
3. Wait for deployment to complete

### Deployment Progress

You'll see status updates:
- Pulling image
- Creating container
- Starting container
- Deployment complete

## Managing Deployed Applications

### Viewing Applications

Navigate to the **Applications** page to see all deployed apps.

### Application Status

| Status | Description |
|--------|-------------|
| Running | Container is active |
| Stopped | Container exists but not running |
| Error | Container failed to start |
| Pulling | Image is being downloaded |

### Application Actions

For each application, you can:

- **Start** - Start a stopped container
- **Stop** - Stop a running container
- **Restart** - Restart the container
- **Logs** - View container logs
- **Delete** - Remove the application

### Accessing Applications

Most applications provide a web interface:

1. Note the port number in the application details
2. Access via `http://server-ip:port`
3. Some apps may require initial setup

## Repository Management

### Default Repositories

Tomo comes with pre-configured repositories containing popular applications.

### Adding Custom Repositories

1. Go to **Marketplace** > **Manage Repos**
2. Click **Add Repository**
3. Enter the repository URL
4. Click **Save**

### Repository Sync

Repositories are synced automatically. To manually sync:

1. Go to **Manage Repos** tab
2. Click **Sync** on the desired repository

### Repository Format

Custom repositories should follow the Tomo catalog format:

```yaml
name: My Custom Apps
description: Personal application catalog
apps:
  - name: My App
    description: A custom application
    image: myrepo/myapp:latest
    ports:
      - "8080:80"
    volumes:
      - "/data:/app/data"
```

## Application Categories

### Media Servers

Popular media applications:

| App | Description | Default Port |
|-----|-------------|--------------|
| Plex | Media streaming server | 32400 |
| Jellyfin | Open-source media system | 8096 |
| Emby | Media server | 8096 |

### Storage & Sync

File management applications:

| App | Description | Default Port |
|-----|-------------|--------------|
| Nextcloud | File sync & share | 80/443 |
| Syncthing | P2P file sync | 8384 |
| FileBrowser | Web file manager | 80 |

### Network Tools

Network management:

| App | Description | Default Port |
|-----|-------------|--------------|
| Pi-hole | DNS ad blocker | 80 |
| Nginx Proxy Manager | Reverse proxy | 81 |
| Traefik | Reverse proxy | 80/443 |

### Monitoring

System monitoring:

| App | Description | Default Port |
|-----|-------------|--------------|
| Grafana | Dashboards & visualization | 3000 |
| Prometheus | Metrics collection | 9090 |
| Uptime Kuma | Uptime monitoring | 3001 |

## Best Practices

### Resource Planning

- Check application requirements before deployment
- Monitor server resources after deployment
- Avoid overloading a single server

### Data Persistence

- Always configure volume mounts for important data
- Use dedicated directories for each application
- Back up volume directories regularly

### Network Security

- Don't expose unnecessary ports to the internet
- Use a reverse proxy for external access
- Enable HTTPS where possible

### Updates

- Regularly check for application updates
- Test updates on non-critical deployments first
- Keep Docker images up to date

## Troubleshooting

### "Deployment Failed"

1. Check Docker is installed: Server shows Docker status
2. Check disk space: `df -h` on the server
3. Check port conflicts: `netstat -tlnp`
4. View deployment logs for specific errors

### "Container Won't Start"

1. Check container logs: Click **Logs** button
2. Verify environment variables are correct
3. Check volume paths exist on the server
4. Ensure required ports are available

### "Cannot Access Application"

1. Verify container is running
2. Check the correct port is mapped
3. Verify firewall allows the port
4. Try accessing via server IP directly

### "Image Pull Failed"

1. Check internet connectivity on server
2. Verify image name is correct
3. Check Docker Hub/registry is accessible
4. Try pulling manually: `docker pull image:tag`

## Common Deployment Configurations

### Media Server (Plex)

```yaml
ports:
  - "32400:32400"
volumes:
  - "/srv/plex/config:/config"
  - "/media/movies:/movies"
  - "/media/tv:/tv"
environment:
  - PUID=1000
  - PGID=1000
  - TZ=America/New_York
```

### File Sync (Nextcloud)

```yaml
ports:
  - "8080:80"
volumes:
  - "/srv/nextcloud/data:/var/www/html"
environment:
  - MYSQL_HOST=db
  - MYSQL_DATABASE=nextcloud
```

### Monitoring (Grafana)

```yaml
ports:
  - "3000:3000"
volumes:
  - "/srv/grafana/data:/var/lib/grafana"
environment:
  - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

**Related Guides:**
- [Quick Start Guide](./QUICK_START.md)
- [Server Management Guide](./SERVER_MANAGEMENT.md)
- [Settings & Configuration Guide](./SETTINGS_CONFIGURATION.md)
