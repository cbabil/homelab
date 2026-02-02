# Marketplace

The Marketplace provides a catalog of pre-configured Docker applications ready to deploy.

---

## Overview

The Marketplace is a Git-based application catalog that provides:
- Pre-configured Docker applications
- One-click deployment
- Customizable settings
- Regular updates

---

## Browsing Applications

### Categories

Applications are organized into categories:

| Category | Examples |
|----------|----------|
| **Media** | Jellyfin, Plex, Emby |
| **Productivity** | Nextcloud, Paperless-ngx |
| **Development** | GitLab, Gitea, Code Server |
| **Monitoring** | Grafana, Uptime Kuma, Prometheus |
| **Networking** | Pi-hole, AdGuard, Traefik |
| **Home Automation** | Home Assistant, Node-RED |
| **Databases** | PostgreSQL, MariaDB, Redis |
| **Utilities** | Portainer, Watchtower |

### Search

Use the search bar to find applications by:
- Name
- Description
- Tags

### Filters

Filter applications by:
- Category
- Popularity
- Recently added

---

## Application Details

Click on any application to see:

| Section | Description |
|---------|-------------|
| **Overview** | Description, screenshots |
| **Requirements** | CPU, RAM, storage needs |
| **Configuration** | Available settings |
| **Documentation** | Links to official docs |
| **Reviews** | Community ratings |

---

## Installing Applications

1. Click on an application
2. Click **Install**
3. Select target server
4. Configure settings
5. Click **Deploy**

See [[Application-Deployment]] for detailed instructions.

---

## Featured Applications

### Portainer

**Category:** Utilities
**Description:** Docker management UI

Portainer provides a web interface for managing Docker containers, images, networks, and volumes.

### Nginx Proxy Manager

**Category:** Networking
**Description:** Reverse proxy with SSL

Easy-to-use reverse proxy with Let's Encrypt SSL certificate management.

### Nextcloud

**Category:** Productivity
**Description:** File sync and collaboration

Self-hosted file storage, calendar, contacts, and collaboration platform.

### Jellyfin

**Category:** Media
**Description:** Media server

Free and open-source media server for movies, TV shows, music, and photos.

### Uptime Kuma

**Category:** Monitoring
**Description:** Uptime monitoring

Self-hosted monitoring tool for websites, APIs, and services.

### Home Assistant

**Category:** Home Automation
**Description:** Home automation platform

Open-source home automation that puts local control and privacy first.

---

## Managing Catalog Sources

### Default Catalog

Tomo comes with a default catalog hosted on GitHub.

### Add Custom Catalog

Add your own or third-party catalogs:

1. Go to **Settings** > **Marketplace**
2. Click **Add Catalog**
3. Enter the Git repository URL
4. Click **Add**

**Catalog URL format:**
```
https://github.com/username/tomo-catalog.git
```

### Refresh Catalog

Catalogs are refreshed automatically. To force refresh:

1. Go to **Settings** > **Marketplace**
2. Click **Refresh** next to a catalog

### Remove Catalog

1. Go to **Settings** > **Marketplace**
2. Click **Remove** next to the catalog

---

## Creating Custom Catalogs

### Catalog Structure

```
catalog/
├── apps/
│   ├── nginx/
│   │   ├── app.json
│   │   ├── docker-compose.yml
│   │   └── README.md
│   ├── postgres/
│   │   ├── app.json
│   │   ├── docker-compose.yml
│   │   └── README.md
│   └── ...
├── catalog.json
└── README.md
```

### app.json Format

```json
{
  "id": "nginx",
  "name": "Nginx",
  "version": "1.25",
  "description": "High-performance web server",
  "category": "networking",
  "tags": ["web", "proxy", "server"],
  "image": "nginx:1.25-alpine",
  "ports": [
    {"container": 80, "host": 80, "protocol": "tcp"}
  ],
  "volumes": [
    {"name": "nginx_html", "path": "/usr/share/nginx/html"}
  ],
  "env": [
    {"name": "TZ", "default": "UTC", "description": "Timezone"}
  ],
  "requirements": {
    "cpu": 1,
    "memory": 128,
    "storage": 100
  }
}
```

### Hosting Your Catalog

1. Create a Git repository
2. Add your applications
3. Push to GitHub/GitLab/etc.
4. Add the repository URL in Tomo

---

## Catalog Updates

### Automatic Updates

Catalogs check for updates periodically (configurable).

### Manual Update

1. Go to **Marketplace**
2. Click **Check for Updates**

### Update Notifications

You'll be notified when:
- New applications are available
- Existing applications have updates

---

## Application Requests

### Request New Application

1. Go to **Marketplace**
2. Click **Request Application**
3. Provide details:
   - Application name
   - Official website
   - Docker image (if known)
   - Use case

### Community Contributions

Contribute applications to the default catalog:
1. Fork the catalog repository
2. Add your application
3. Submit a pull request

---

## Troubleshooting

### Catalog Won't Load

| Issue | Solution |
|-------|----------|
| Network error | Check internet connectivity |
| Invalid URL | Verify repository URL |
| Private repo | Add authentication token |
| Rate limited | Wait or use authenticated access |

### Application Missing

| Issue | Solution |
|-------|----------|
| Not in catalog | Request the application |
| Wrong category | Use search instead |
| Deprecated | Check for replacement |

---

## CLI Reference

```bash
# List catalogs
tomo marketplace catalogs

# Refresh catalogs
tomo marketplace refresh

# Search applications
tomo marketplace search <query>

# Show application details
tomo marketplace info <app-id>

# Add catalog
tomo marketplace add-catalog <url>

# Remove catalog
tomo marketplace remove-catalog <catalog-id>
```

---

## Next Steps

- [[Application-Deployment]] - Deploy applications
- [[Configuration]] - Configure settings
- [[Troubleshooting]] - Solve problems
