# Application Deployment

This guide covers deploying containerized applications to your servers.

---

## Overview

Tomo deploys applications as Docker containers. Each application:
- Runs in an isolated container
- Has configurable environment variables
- Can expose ports to the network
- Persists data in Docker volumes

---

## Deploying an Application

### Step 1: Choose an Application

1. Go to **Marketplace** page
2. Browse or search for applications
3. Click on an application to see details

### Step 2: Click Install

On the application details page, click **Install**.

### Step 3: Select Target Server

Choose which server to deploy to:
- Only servers with Docker installed are shown
- Server status is displayed (Online/Offline)

### Step 4: Configure Settings

| Section | Description |
|---------|-------------|
| **Basic** | Application name, description |
| **Ports** | Map container ports to host ports |
| **Environment** | Set environment variables |
| **Volumes** | Configure persistent storage |
| **Network** | Network mode and settings |

### Step 5: Deploy

Click **Deploy** to start the deployment.

### Step 6: Monitor Progress

Watch the deployment progress:
1. Pulling image
2. Creating container
3. Starting container
4. Health check

---

## Configuration Options

### Port Mapping

Map container ports to host ports:

| Container Port | Host Port | Description |
|----------------|-----------|-------------|
| 80 | 8080 | Web interface |
| 443 | 8443 | HTTPS |

**Example:** Container port 80 → Host port 8080 means access via `http://server:8080`

### Environment Variables

Set application-specific configuration:

```
DATABASE_URL=postgresql://user:pass@db:5432/app
ADMIN_EMAIL=admin@example.com
TZ=America/New_York
```

### Volumes

Persist data across container restarts:

| Volume Name | Container Path | Purpose |
|-------------|----------------|---------|
| app_data | /data | Application data |
| app_config | /config | Configuration files |

### Network Modes

| Mode | Description |
|------|-------------|
| **Bridge** | Default, isolated network |
| **Host** | Share host network |
| **None** | No networking |

---

## Managing Deployed Applications

### View Applications

Go to **Applications** page to see all deployed applications.

### Application Status

| Status | Meaning |
|--------|---------|
| **Running** | Container is running normally |
| **Stopped** | Container is stopped |
| **Restarting** | Container is restarting |
| **Error** | Container has errors |
| **Deploying** | Deployment in progress |

### Start/Stop/Restart

1. Go to **Applications** page
2. Find the application
3. Click the action button (play/stop/restart)

### View Logs

1. Click on an application
2. Go to **Logs** tab
3. View real-time container logs

### Update Application

1. Click on the application
2. Click **Update**
3. Choose update options:
   - Pull latest image
   - Keep current settings

### Delete Application

1. Click on the application
2. Click **Delete**
3. Choose:
   - **Keep data** - Preserve volumes
   - **Delete all** - Remove volumes too

---

## Deployment Presets

Some applications have deployment presets:

| Preset | Description |
|--------|-------------|
| **Minimal** | Basic configuration |
| **Recommended** | Optimal settings |
| **Advanced** | All options exposed |

---

## Multi-Container Applications

Some applications require multiple containers (e.g., app + database):

1. The marketplace handles dependencies automatically
2. All containers are deployed together
3. Internal networking is configured

**Example: WordPress**
- WordPress container
- MySQL container
- Internal network connecting them

---

## Custom Applications

### Deploy Custom Image

1. Go to **Applications** > **Deploy Custom**
2. Enter image details:

| Field | Example |
|-------|---------|
| Image | `nginx:latest` |
| Name | `my-nginx` |
| Ports | `80:80` |

### Compose Files

For complex applications, you can deploy from a docker-compose.yml:

1. Go to **Applications** > **Deploy Compose**
2. Upload or paste your compose file
3. Review and deploy

---

## Health Checks

Applications can have health checks:

| Status | Meaning |
|--------|---------|
| **Healthy** | Health check passing |
| **Unhealthy** | Health check failing |
| **Starting** | Health check not yet run |
| **None** | No health check configured |

---

## Resource Limits

Set resource constraints:

| Limit | Description |
|-------|-------------|
| **CPU** | CPU cores/shares |
| **Memory** | RAM limit |
| **Restart** | Restart policy |

---

## Troubleshooting

### Deployment Fails

| Issue | Solution |
|-------|----------|
| Image not found | Check image name and tag |
| Port in use | Change host port |
| Permission denied | Check Docker permissions |
| Out of disk | Free up space on server |

### Application Won't Start

1. Check container logs
2. Verify environment variables
3. Check port conflicts
4. Verify volume permissions

### Network Issues

| Issue | Solution |
|-------|----------|
| Can't access app | Check port mapping, firewall |
| Containers can't communicate | Check network configuration |
| DNS issues | Use container names, not IPs |

---

## CLI Reference

```bash
# List deployed applications
tomo app list

# Deploy from marketplace
tomo app deploy <app-id> --server <server-id>

# Start/stop/restart
tomo app start <app-id>
tomo app stop <app-id>
tomo app restart <app-id>

# View logs
tomo app logs <app-id>

# Delete application
tomo app delete <app-id>
```

---

## Best Practices

1. **Use specific image tags** - Avoid `latest` in production
2. **Set resource limits** - Prevent runaway containers
3. **Use volumes for data** - Don't store data in containers
4. **Configure health checks** - Monitor application health
5. **Set restart policies** - Auto-recover from crashes

---

## Next Steps

- [[Marketplace]] - Browse more applications
- [[Backup-and-Restore]] - Backup your applications
- [[Troubleshooting]] - Solve common problems
