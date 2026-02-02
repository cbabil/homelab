# Applications Marketplace User Guide

## Overview

The Applications Marketplace provides a centralized catalog for discovering, deploying, and managing containerized applications across your tomo infrastructure. Applications are deployed as Docker containers to your connected server VMs via SSH.

## Accessing the Marketplace

1. Navigate to **Applications** in the sidebar
2. Browse the application catalog
3. Use search and filters to find specific applications

## Features

### Browse Applications

The marketplace displays applications as cards with:
- **App icon** - Visual identifier
- **Name and description** - What the app does
- **Version** - Current version number
- **Category** - Application type (Networking, Automation, Media, etc.)
- **Rating** - Community star rating (if available)

### Search and Filter

- **Search bar** - Find apps by name or description
- **Category filter** - Filter by application category
- **Status filter** - Show all, available, or deployed apps

### Deploy Applications

To deploy an application to a server VM:

1. Find the application you want to deploy
2. Click the **Deploy** button (download icon) on the app card
3. Select the target server from your connected VMs
4. Configure any required settings (ports, volumes, environment variables)
5. Confirm deployment

**What happens during deployment:**
1. Docker image is pulled on the target server
2. Container is created with configured settings
3. Container is started
4. App status updates to "deployed"

### Uninstall Applications

To remove a deployed application from a server:

1. Find the deployed application (shows green checkmark)
2. Click the **Uninstall** button (trash icon) on the app card
3. Confirm the uninstall action

**What happens during uninstall:**
1. Container is stopped on the target server via SSH
2. Container is removed (`docker rm`)
3. Optionally, data volumes are removed
4. App status returns to "available"

### Bulk Actions

The bulk action bar appears when applications are in the catalog.

#### Select Applications
- Click the **checkbox** on individual app cards to select them
- Click **Select all** to select all applications
- Click the **X** next to selection count to clear selection

#### Bulk Uninstall
When deployed applications are selected:
- Orange **Uninstall (N)** button appears
- Click to uninstall all selected deployed apps at once
- Apps are marked as available (status update only for bulk operations)

#### Bulk Remove from Catalog
When non-deployed applications are selected:
- Red **Remove (N)** button appears
- Click to remove selected apps from your local catalog
- Only affects apps that are NOT currently deployed
- Deployed apps are skipped with a warning

**Note:** Bulk operations on deployed apps only update the local status. To fully remove containers from VMs, use individual uninstall or the server management tools.

## Application States

| Status | Icon | Description |
|--------|------|-------------|
| Available | Download icon | Ready to deploy |
| Deploying | Spinner | Currently being deployed |
| Deployed | Green checkmark | Running on a server |
| Error | Red indicator | Deployment or runtime error |

## Adding Custom Applications

1. Click **Add App** button in the page header
2. Fill in application details:
   - Name (required)
   - Description (required)
   - Version
   - Category
   - Docker image
   - Port mappings
   - Volume mappings
   - Environment variables
3. Click **Save** to add to your catalog

## Architecture

### Deployment Flow

```
User clicks Deploy
       │
       ▼
Frontend calls MCP tool "install_app"
       │
       ▼
Backend DeploymentService
       │
       ├─► SSH to target server
       │
       ├─► docker pull <image>
       │
       ├─► docker run -d --name <container> ...
       │
       └─► Update database with installation record
```

### Uninstall Flow

```
User clicks Uninstall
       │
       ▼
Frontend calls MCP tool "uninstall_app"
       │
       ▼
Backend DeploymentService
       │
       ├─► SSH to target server
       │
       ├─► docker stop <container>
       │
       ├─► docker rm <container>
       │
       └─► Delete installation record from database
```

## MCP Tools Reference

| Tool | Description |
|------|-------------|
| `search_apps` | Search and filter application catalog |
| `get_app_details` | Get full details for a single app |
| `install_app` | Deploy app to a server |
| `uninstall_app` | Remove app from a server (full Docker cleanup) |
| `mark_app_uninstalled` | Mark app as uninstalled (status only) |
| `mark_apps_uninstalled_bulk` | Bulk mark apps as uninstalled |
| `remove_app` | Remove non-deployed app from catalog |
| `remove_apps_bulk` | Bulk remove apps from catalog |
| `start_app` | Start a stopped container |
| `stop_app` | Stop a running container |
| `get_installed_apps` | List all apps deployed on a server |

## Troubleshooting

### App won't deploy
- Verify the target server is connected and accessible
- Check server has Docker installed and running
- Ensure required ports are not already in use
- Check server has sufficient resources (RAM, disk)

### App shows as deployed but isn't running
- Use server management to check container status
- View container logs for error messages
- Try stopping and starting the app

### Can't remove app from catalog
- Deployed apps cannot be removed from catalog
- Uninstall the app first, then remove from catalog

### Bulk uninstall skipped some apps
- Only deployed apps can be uninstalled
- Apps in "available" status are skipped
- Check the warning toast for details

## Best Practices

1. **Test deployments** on a non-production server first
2. **Back up data** before uninstalling apps with persistent volumes
3. **Monitor resources** when deploying multiple apps
4. **Use categories** to organize your application catalog
5. **Review port mappings** to avoid conflicts between apps
