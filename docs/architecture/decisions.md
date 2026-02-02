# Architectural Decision Records (ADRs)

This document captures the key architectural decisions made for the Tomo project, along with their context, rationale, and consequences.

## ADR-001: MCP Protocol for Frontend-Backend Communication

**Date**: 2025-09-05  
**Status**: Accepted  
**Context**: Need to choose communication protocol between React frontend and Python backend

### Decision

We will use the Model Context Protocol (MCP) with fastmcp library for frontend-backend communication instead of traditional REST APIs.

### Rationale

**Advantages:**
- **Modern Protocol**: MCP provides structured, typed communication patterns
- **Tool-Based Architecture**: Natural fit for our tool-oriented operations (server preparation, app installation)
- **Real-time Support**: Built-in support for streaming and real-time updates
- **Type Safety**: Strong typing across frontend/backend boundaries
- **Extensibility**: Easy to add new tools without API versioning issues

**Alternatives Considered:**
- **REST API**: Traditional approach but requires custom streaming solutions
- **GraphQL**: Overkill for our use case, adds complexity
- **WebSocket**: Too low-level, would need custom protocol design

### Consequences

**Positive:**
- Clear separation of concerns with tool-based operations
- Built-in real-time capabilities for progress tracking
- Strong typing reduces runtime errors
- Future-proof architecture aligned with modern AI/automation trends

**Negative:**
- Less familiar to developers compared to REST
- Smaller ecosystem and community
- Additional abstraction layer to learn

### Implementation Details

```typescript
// Frontend MCP Client Interface
interface MCPClient {
  callTool<T>(name: string, params: object): Promise<MCPResponse<T>>;
  subscribe(events: string[]): EventSource;
}

// Example tool call
const result = await mcp.callTool('prepare_server', {
  host: '192.168.1.100',
  credentials: { /* encrypted */ }
});
```

---

## ADR-002: Single Container Deployment Architecture

**Date**: 2025-09-05  
**Status**: Accepted  
**Context**: Need to choose deployment architecture for production

### Decision

We will package the application as a single Docker container with nginx proxy, Python backend, and React frontend, managed by supervisord.

### Rationale

**Advantages:**
- **Simplicity**: Single container deployment reduces operational complexity
- **Self-Contained**: All dependencies bundled, no external service requirements
- **Easy Distribution**: Single image to distribute and deploy
- **Resource Efficiency**: Shared container resources, no inter-container networking overhead
- **Consistent Environment**: Identical development and production environments

**Alternatives Considered:**
- **Multi-Container with Docker Compose**: More complex deployment, multiple images
- **Kubernetes**: Overkill for single-application deployment
- **Separate Nginx Container**: Additional networking complexity

### Consequences

**Positive:**
- Simplified deployment and distribution
- Reduced infrastructure requirements
- Easier troubleshooting and monitoring
- Lower resource usage

**Negative:**
- Less flexibility for individual component scaling
- Mixing concerns in single container
- More complex multi-process management

### Implementation Details

```dockerfile
# Multi-stage build for optimized production image
FROM node:18-alpine AS frontend-build
# Frontend build stage

FROM python:3.11-alpine AS backend-build  
# Backend preparation stage

FROM nginx:alpine AS production
# Install supervisord for process management
# Copy built frontend to nginx directory
# Copy backend Python application
# Configure nginx proxy to backend
# Use supervisord to manage nginx + Python processes
```

---

## ADR-003: Paramiko for SSH Management

**Date**: 2025-09-05  
**Status**: Accepted  
**Context**: Need to choose SSH library for remote server management

### Decision

We will use paramiko (pure Python SSH client) for all SSH operations to remote servers.

### Rationale

**Advantages:**
- **Pure Python**: No system dependencies, works in any Python environment
- **Full Feature Set**: Supports all SSH features we need (auth, exec, SFTP)
- **Platform Independent**: Works on Windows, macOS, and Linux
- **Active Development**: Well-maintained with regular updates
- **Security**: Modern cryptographic implementations

**Alternatives Considered:**
- **System SSH Client**: Would require shell execution, harder to manage
- **Fabric**: Higher-level but adds unnecessary abstraction
- **asyncssh**: Good but less mature ecosystem

### Consequences

**Positive:**
- No external system dependencies
- Consistent behavior across platforms
- Rich API for SSH operations
- Easy credential management integration

**Negative:**
- Pure Python implementation may be slower than native SSH
- Additional Python dependency

### Implementation Details

```python
class SSHService:
    def create_ssh_client(self) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        # Security: Only allow known hosts
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        return client
    
    async def establish_connection(self, host, port, username, credentials):
        # Connection implementation with security best practices
```

---

## ADR-004: Encrypted JSON File Storage

**Date**: 2025-09-05  
**Status**: Accepted  
**Context**: Need to choose data persistence strategy for server configurations and credentials

### Decision

We will use encrypted JSON files for storing server configurations and credentials, with AES-256 encryption for sensitive data.

### Rationale

**Advantages:**
- **Simplicity**: No database setup or management required
- **Portability**: Easy backup, export, and migration
- **Version Control Friendly**: Human-readable configuration files
- **Security**: Sensitive data encrypted with strong cryptography
- **Self-Contained**: No external database dependencies

**Alternatives Considered:**
- **SQLite**: Would add database complexity for simple data
- **PostgreSQL/MySQL**: Overkill for our data volume and complexity
- **Plain JSON**: Not secure for credential storage

### Consequences

**Positive:**
- Simple to implement and maintain
- Easy backup and restore procedures
- No database administration overhead
- Strong security for sensitive data

**Negative:**
- Not suitable for high-concurrency scenarios
- No built-in query capabilities
- Manual file locking needed for concurrent access

### Implementation Details

```python
# Encrypted credential storage
class CredentialManager:
    def __init__(self, master_password: str):
        self.cipher = Fernet(self._derive_key(master_password))
    
    def encrypt_credentials(self, credentials: dict) -> str:
        return self.cipher.encrypt(json.dumps(credentials).encode())
```

---

## ADR-005: React Context for State Management

**Date**: 2025-09-05  
**Status**: Accepted  
**Context**: Need to choose state management solution for React frontend

### Decision

We will use React Context API with useReducer for global state management instead of external libraries.

### Rationale

**Advantages:**
- **Built-in Solution**: No additional dependencies
- **Sufficient Complexity**: Adequate for our application's state complexity
- **Type Safety**: Works well with TypeScript
- **Performance**: Acceptable performance with proper context splitting

**Alternatives Considered:**
- **Redux Toolkit**: Overkill for our state complexity
- **Zustand**: Good option but adds dependency
- **Jotai**: Too granular for our use case

### Consequences

**Positive:**
- No external state management dependencies
- Simpler application architecture
- Good TypeScript integration
- Familiar to most React developers

**Negative:**
- Manual optimization needed for performance
- More boilerplate for complex state updates
- Less sophisticated developer tools

### Implementation Details

```typescript
// State management structure
interface AppState {
  servers: ServerConnection[];
  applications: InstalledApplication[];
  mcp: { connected: boolean; error?: string };
}

const AppContext = createContext<{
  state: AppState;
  dispatch: Dispatch<AppAction>;
} | null>(null);
```

---

## ADR-006: shadcn/ui Component Library

**Date**: 2025-09-05  
**Status**: Accepted  
**Context**: Need to choose UI component library for React frontend

### Decision

We will use shadcn/ui component library with Radix UI primitives and TailwindCSS.

### Rationale

**Advantages:**
- **Copy-Paste Components**: Components are copied into codebase, full control
- **Accessibility**: Built on Radix UI primitives with excellent a11y
- **Customizable**: Easy to modify components for specific needs
- **Modern Design**: Clean, professional appearance
- **TypeScript Native**: Excellent TypeScript support

**Alternatives Considered:**
- **Material-UI**: Too opinionated, harder to customize
- **Ant Design**: Good but heavy bundle size
- **Custom Components**: Too much development overhead

### Consequences

**Positive:**
- Full control over component implementation
- Excellent accessibility out of the box
- Easy customization and theming
- No runtime dependency on external component library

**Negative:**
- More files to maintain in codebase
- Manual updates needed for component improvements
- Initial setup more complex than npm install

### Implementation Details

```typescript
// Example component usage
import { Button } from '@/components/ui/button';
import { Dialog } from '@/components/ui/dialog';

export function ServerForm() {
  return (
    <Dialog>
      <Button variant="outline">Add Server</Button>
      {/* Component implementation */}
    </Dialog>
  );
}
```

---

## ADR-007: Application Catalog Design

**Date**: 2025-09-05  
**Status**: Accepted  
**Context**: Need to design application catalog and installation system

### Decision

We will use a JSON-based application catalog with Docker container definitions and support for custom applications.

### Rationale

**Advantages:**
- **Version Control**: Easy to track changes to application definitions
- **Extensible**: Easy to add new applications
- **Portable**: Catalog can be shared and distributed
- **Validation**: JSON schema validation for application definitions

**Alternatives Considered:**
- **Database Storage**: Adds complexity for static data
- **YAML Format**: JSON provides better tooling and validation
- **Hard-coded Applications**: Not extensible

### Consequences

**Positive:**
- Easy to add new applications
- Version controllable application definitions
- Supports custom applications
- Easy backup and sharing of catalogs

**Negative:**
- Manual process for adding applications
- No automatic application discovery
- Requires validation for custom applications

### Implementation Details

```json
{
  "applications": [
    {
      "id": "portainer",
      "name": "portainer",
      "display_name": "Portainer",
      "docker_image": "portainer/portainer-ce:latest",
      "default_ports": [{"container_port": 9000, "host_port": 9000}],
      "volume_mounts": [
        {"container_path": "/data", "host_path": "/var/lib/portainer"}
      ]
    }
  ]
}
```

---

## ADR-008: Security-First Credential Management

**Date**: 2025-09-05  
**Status**: Accepted  
**Context**: Need to design secure credential storage and management

### Decision

We will implement a security-first credential management system with AES-256 encryption, PBKDF2 key derivation, and no plaintext credential storage.

### Rationale

**Advantages:**
- **Strong Encryption**: AES-256 provides military-grade security
- **Key Derivation**: PBKDF2 with high iteration count prevents rainbow table attacks
- **No Plaintext**: Credentials never stored in plaintext
- **Master Password**: Single password protects all credentials

**Alternatives Considered:**
- **System Keystore**: Platform-dependent, harder to deploy
- **Environment Variables**: Not secure for long-term storage
- **Database Encryption**: Adds database complexity

### Consequences

**Positive:**
- High security for credential storage
- Compliance with security best practices
- Audit-ready credential management
- Protection against data breaches

**Negative:**
- More complex implementation
- Password management overhead
- Recovery complexity if master password lost

### Implementation Details

```python
class CredentialManager:
    def __init__(self, master_password: str):
        # PBKDF2 with 100,000 iterations
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, 
                         salt=salt, iterations=100000)
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        self.cipher = Fernet(key)
```

---

## ADR-009: Comprehensive Error Handling Strategy

**Date**: 2025-09-05  
**Status**: Accepted  
**Context**: Need to design error handling across MCP tools and UI components

### Decision

We will implement structured error handling with error codes, user-friendly messages, and detailed logging.

### Rationale

**Advantages:**
- **User Experience**: Clear, actionable error messages for users
- **Debugging**: Detailed logs for troubleshooting
- **Consistency**: Standardized error format across application
- **Recovery**: Error codes enable programmatic error handling

**Alternatives Considered:**
- **Simple String Errors**: Not structured enough for good UX
- **Exception-Only**: Doesn't provide good user feedback
- **HTTP Status Codes**: Not applicable to MCP protocol

### Consequences

**Positive:**
- Better user experience with clear error messages
- Easier debugging and support
- Consistent error handling patterns
- Programmatic error recovery possible

**Negative:**
- More complex error handling code
- Need to maintain error message catalog
- Additional testing complexity

### Implementation Details

```python
# Structured error response format
{
  "success": false,
  "message": "Connection failed: Invalid hostname",
  "error_code": "SSH_CONNECTION_ERROR",
  "details": {
    "host": "invalid-host",
    "reason": "hostname_resolution_failed"
  },
  "troubleshooting": [
    "Verify the hostname is correct",
    "Check network connectivity",
    "Ensure DNS resolution is working"
  ]
}
```

---

## ADR-010: Real-time Progress Tracking

**Date**: 2025-09-05  
**Status**: Accepted  
**Context**: Need to provide real-time feedback for long-running operations

### Decision

We will implement real-time progress tracking using Server-Sent Events (SSE) with structured progress data.

### Rationale

**Advantages:**
- **Real-time Updates**: Users see progress as it happens
- **Structured Data**: Progress, logs, and status in consistent format
- **Web Standard**: SSE is a web standard with good browser support
- **Simple Implementation**: Easier than WebSockets for one-way communication

**Alternatives Considered:**
- **Polling**: Inefficient and higher latency
- **WebSockets**: Overkill for one-way communication
- **Long Polling**: Complex implementation, resource intensive

### Consequences

**Positive:**
- Better user experience with real-time feedback
- Users can monitor long-running operations
- Early error detection and reporting
- Professional application feel

**Negative:**
- More complex implementation
- Additional server resources for SSE connections
- Need to handle connection management

### Implementation Details

```typescript
// Frontend SSE handling
const eventSource = new EventSource('/api/progress');
eventSource.onmessage = (event) => {
  const progress = JSON.parse(event.data);
  updateProgressUI(progress);
};

// Backend SSE progress data
{
  "operation": "server_preparation",
  "progress": 65,
  "step": "Installing Docker",
  "log": "✓ Repository added successfully",
  "estimated_remaining": "2 minutes"
}
```

---

## Summary

These architectural decisions form the foundation of the Tomo system. Key themes include:

1. **Modern Technologies**: MCP protocol, React 18+, Python 3.11+
2. **Security First**: Encrypted credential storage, secure SSH practices
3. **Simplicity**: Single container deployment, file-based storage
4. **User Experience**: Real-time feedback, clear error messages
5. **Extensibility**: Plugin-friendly architecture, customizable applications

Each decision balances technical requirements with practical constraints, prioritizing security, maintainability, and user experience while keeping the system simple enough for easy deployment and maintenance.

The decisions are documented here to:
- Provide context for future developers
- Enable informed changes when requirements evolve
- Ensure architectural consistency across the codebase
- Support technical reviews and audits

Future ADRs should follow the same format and be added to this document as the system evolves.