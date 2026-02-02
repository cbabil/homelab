# Application Deployment

This document describes the deployment workflow for installing applications from the marketplace onto servers.

## Overview

The deployment system allows users to:
1. Select an application from the marketplace or app catalog
2. Choose a target server from their connected servers
3. Configure deployment options (ports, volumes, environment variables)
4. Deploy and monitor installation progress

## Research: Industry Patterns

Before implementation, we researched how popular open-source platforms handle deployment:

| Platform | Server Selection | Configuration | Complexity |
|----------|-----------------|---------------|------------|
| **Umbrel/CasaOS** | Single server | None (auto) | Lowest |
| **Yacht** | Single server | Template-based | Low |
| **Coolify** | Multi-server dropdown | Project/Environment | Medium |
| **CapRover** | Cluster-based | Per-app config | Medium |
| **Portainer** | Environment selector | Full control | Highest |

### Key Takeaways

1. **Simple by default** (Umbrel approach) - One-click install works out of the box
2. **Optional configuration** (Coolify approach) - Advanced users can customize
3. **Server selection** (Coolify/CapRover) - Essential for multi-server setups
4. **Progress feedback** - Show deployment status in real-time

### Sources

- [Portainer](https://github.com/portainer/portainer) - Enterprise container management
- [Coolify](https://coolify.io/) - Self-hosted Heroku/Vercel alternative
- [CasaOS](https://casaos.io/) - Home cloud system with app store
- [Umbrel](https://umbrel.com/) - Beautiful home server OS
- [CapRover](https://caprover.com/) - Scalable self-hosted PaaS
- [Yacht](https://github.com/SelfhostedPro/Yacht) - Template-focused Docker UI

## Architecture

### Component Structure

```
frontend/src/
├── components/
│   └── deployment/
│       ├── DeploymentModal.tsx        # Main modal component
│       ├── DeploymentConfigForm.tsx   # Port/volume/env configuration
│       ├── DeploymentProgress.tsx     # Status tracking (future)
│       └── ServerSelector.tsx         # Server list with status
├── hooks/
│   └── useDeploymentModal.ts          # State management hook
└── pages/
    └── applications/
        └── ApplicationsPage.tsx       # Integration point
```

### Data Flow

```
User clicks Deploy
       ↓
DeploymentModal opens
       ↓
User selects server
       ↓
User configures options (optional)
       ↓
User confirms deployment
       ↓
Frontend calls MCP tool: install_app(server_id, app_id, config)
       ↓
Backend deployment service:
  1. Validates server connection
  2. Pulls Docker image
  3. Creates container with config
  4. Starts container
  5. Returns installation ID
       ↓
Frontend updates app status to "installed"
```

## UI Design

### Deployment Modal

```
┌─────────────────────────────────────────────────────┐
│  Deploy [App Name]                              ✕   │
├─────────────────────────────────────────────────────┤
│  ━━━━━━━━━━○━━━━━━━━━━  Step 1 of 2                │
│                                                     │
│  SELECT SERVER                                      │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ ● prod-server                               │   │
│  │   192.168.1.10 • Connected                  │   │
│  └─────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────┐   │
│  │ ○ dev-server                                │   │
│  │   192.168.1.11 • Connected                  │   │
│  └─────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────┐   │
│  │ ○ backup-server                    Offline  │   │
│  │   192.168.1.12 • Disconnected               │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
├─────────────────────────────────────────────────────┤
│  [Cancel]                           [Continue →]    │
└─────────────────────────────────────────────────────┘
```

### Configuration Step (Optional)

```
┌─────────────────────────────────────────────────────┐
│  Deploy [App Name]                              ✕   │
├─────────────────────────────────────────────────────┤
│  ━━━━━━━━━━━━━━━━━━━━○  Step 2 of 2                │
│                                                     │
│  CONFIGURATION                                      │
│                                                     │
│  ▾ Port Mappings                                    │
│    ┌──────────────┐    ┌──────────────┐            │
│    │ Container    │ →  │ Host         │            │
│    │ 80          │    │ 8080         │            │
│    └──────────────┘    └──────────────┘            │
│    ┌──────────────┐    ┌──────────────┐            │
│    │ 443         │ →  │ 8443         │            │
│    └──────────────┘    └──────────────┘            │
│                                                     │
│  ▸ Environment Variables (3)                        │
│  ▸ Volume Mounts (1)                                │
│                                                     │
│  ─────────────────────────────────────────────────  │
│  SUMMARY                                            │
│  Server: prod-server (192.168.1.10)                 │
│  Image: nginx:latest                                │
│  Ports: 80→8080, 443→8443                          │
│                                                     │
├─────────────────────────────────────────────────────┤
│  [← Back]    [Cancel]               [Deploy Now]    │
└─────────────────────────────────────────────────────┘
```

### Deploying State

```
┌─────────────────────────────────────────────────────┐
│  Deploying [App Name]                               │
├─────────────────────────────────────────────────────┤
│                                                     │
│              ◐  Installing...                       │
│                                                     │
│  ✓ Connecting to server                             │
│  ✓ Pulling image                                    │
│  ◐ Creating container                               │
│  ○ Starting application                             │
│                                                     │
│  This may take a few minutes depending on           │
│  image size and network speed.                      │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                        [Cancel]     │
└─────────────────────────────────────────────────────┘
```

## Backend API

### MCP Tool: install_app

```python
async def install_app(
    server_id: str,      # Target server ID
    app_id: str,         # Application ID from catalog
    config: dict = None  # Optional configuration overrides
) -> dict:
    """
    Install an application on a server.

    Config structure:
    {
        "ports": {
            "80": 8080,      # container_port: host_port
            "443": 8443
        },
        "volumes": {
            "/data": "/var/lib/app/data",  # container: host
            "/config": "/etc/app/config"
        },
        "env": {
            "DATABASE_URL": "postgres://...",
            "ADMIN_EMAIL": "admin@example.com"
        }
    }

    Returns:
    {
        "success": True,
        "data": {
            "installation_id": "uuid",
            "server_id": "server-1",
            "app_id": "nginx"
        },
        "message": "App 'nginx' installation started"
    }
    """
```

### Installation Status Flow

```
PENDING → PULLING → CREATING → RUNNING
                              ↘ ERROR
                              ↘ STOPPED
```

| Status | Description |
|--------|-------------|
| `pending` | Installation queued |
| `pulling` | Downloading Docker image |
| `creating` | Creating container |
| `running` | Container started successfully |
| `stopped` | Container stopped |
| `error` | Installation failed |

## Implementation Checklist

### Phase 1: Core Modal
- [ ] Create `DeploymentModal.tsx` component
- [ ] Create `useDeploymentModal.ts` hook
- [ ] Server selection with status indicators
- [ ] Basic deploy button integration

### Phase 2: Configuration
- [ ] Create `DeploymentConfigForm.tsx`
- [ ] Port mapping configuration
- [ ] Environment variable configuration
- [ ] Volume mount configuration

### Phase 3: Progress & Status
- [ ] Create `DeploymentProgress.tsx`
- [ ] Real-time status updates
- [ ] Success/error handling
- [ ] App status refresh after deployment

### Phase 4: Polish
- [ ] Loading states and animations
- [ ] Error recovery options
- [ ] Deployment history (future)
- [ ] Multi-app deployment (future)

## Component API

### DeploymentModal

```typescript
interface DeploymentModalProps {
  isOpen: boolean
  onClose: () => void
  app: App | null
  servers: ServerConnection[]
  onDeploy: (serverId: string, config?: DeploymentConfig) => Promise<void>
  isDeploying: boolean
  error?: string | null
}
```

### useDeploymentModal Hook

```typescript
interface UseDeploymentModalReturn {
  // Modal state
  isOpen: boolean
  openModal: (app: App) => void
  closeModal: () => void

  // Selection state
  selectedApp: App | null
  selectedServerId: string | null
  setSelectedServerId: (id: string) => void

  // Configuration
  config: DeploymentConfig
  setConfig: (config: DeploymentConfig) => void

  // Deployment
  isDeploying: boolean
  error: string | null
  deploy: () => Promise<void>
}
```

### DeploymentConfig

```typescript
interface DeploymentConfig {
  ports?: Record<string, number>      // containerPort: hostPort
  volumes?: Record<string, string>    // containerPath: hostPath
  env?: Record<string, string>        // key: value
}
```

## Testing

### Unit Tests
- Modal open/close behavior
- Server selection validation
- Configuration form validation
- Hook state management

### Integration Tests
- Full deployment flow with mock MCP
- Error handling scenarios
- Multi-server selection

### E2E Tests
- Complete deployment workflow
- Status updates during deployment
- Post-deployment app status verification
