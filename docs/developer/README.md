# Developer Documentation

Welcome to the Homelab Assistant Developer Documentation. This guide provides comprehensive information for developers working on or extending the Homelab Assistant project.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Structure](#project-structure)
3. [Development Setup](#development-setup)
4. [Architecture Overview](#architecture-overview)
5. [API Reference](#api-reference)
6. [Contributing Guidelines](#contributing-guidelines)
7. [Testing](#testing)
8. [Deployment](#deployment)

## Quick Start

### Prerequisites

- Node.js 18+ with Yarn
- Python 3.11+
- Docker and Docker Compose
- Git

### Get Started in 5 Minutes

```bash
# Clone the repository
git clone <repository-url>
cd homelab

# Start development environment
make setup
make dev

# Open browser to http://localhost:3000
```

## Project Structure

```
homelab/
├── frontend/                    # React + Vite + TypeScript
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── layout/          # Layout components (AppLayout, Header, Navigation)
│   │   │   └── ui/              # Reusable UI components
│   │   ├── services/            # MCP client & business logic
│   │   ├── providers/           # React context providers
│   │   ├── pages/               # Page components
│   │   ├── types/               # TypeScript definitions
│   │   └── utils/               # Frontend utility helpers
│   ├── package.json
│   ├── vite.config.ts
│   └── vitest.config.ts
├── backend/                     # Python + fastmcp
│   ├── src/
│   │   ├── main.py              # FastMCP server entry point
│   │   ├── tools/               # MCP tool implementations
│   │   ├── services/            # Business logic services
│   │   ├── models/              # Data models and schemas
│   │   └── lib/                 # Shared backend helpers
│   ├── tests/                   # Test suite
│   ├── requirements.txt
│   └── pyproject.toml
├── docs/                        # Documentation
│   ├── developer/               # Developer documentation (this folder)
│   ├── user/                    # User guides and manuals
│   ├── technical/               # Technical architecture and design
│   └── api/                     # API documentation
├── docker/                      # Docker configuration files
└── scripts/                     # Build and deployment scripts
```

## Development Setup

### Development Environment

The project uses a containerized development environment for consistency:

```bash
# Development setup
make setup          # Initialize project and install dependencies
make dev            # Start development servers (frontend + backend)
make test           # Run test suite
make lint           # Run code quality checks
make clean          # Clean up development environment
```

### Manual Setup

If you prefer to run services manually:

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start development server
python src/main.py
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
yarn install

# Start development server
yarn dev
```

### Environment Variables

Create `.env` files for configuration:

#### Backend (.env)

```env
# Server Configuration
MCP_LOG_LEVEL=DEBUG
SSH_CONNECTION_TIMEOUT=30
MAX_CONCURRENT_CONNECTIONS=10

# Security
HOMELAB_MASTER_KEY=your-secure-master-key-here
HOMELAB_SALT=your-unique-salt-here

# Development
PYTHON_ENV=development
```

#### Frontend (.env)

```env
# API Configuration
VITE_MCP_SERVER_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Development
NODE_ENV=development
```

## Architecture Overview

### System Design

The Homelab Assistant follows a modern three-tier architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React UI      │    │   MCP Server    │    │  Remote Server  │
│   (Frontend)    │◄──►│   (Backend)     │◄──►│   (Target)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
    Vite Dev Server         FastMCP + uvicorn        SSH + Docker
    TypeScript              Python 3.11+             Linux Systems
    React 18+               paramiko, docker          
```

### Key Technologies

**Frontend:**
- **React 18+**: Modern functional components with hooks
- **TypeScript**: Type safety and better developer experience
- **Vite**: Fast development and optimized builds
- **TailwindCSS**: Utility-first CSS framework
- **Vitest**: Unit and integration testing

**Backend:**
- **FastMCP**: Model Context Protocol server framework
- **Python 3.11+**: Modern Python with performance improvements
- **paramiko**: SSH client library for secure connections
- **Docker SDK**: Container management
- **structlog**: Structured JSON logging

**Infrastructure:**
- **Docker**: Containerization for consistent deployment
- **nginx**: Reverse proxy and static file serving
- **Docker Compose**: Development orchestration

### MCP Protocol Integration

The application uses the Model Context Protocol (MCP) for frontend-backend communication instead of traditional REST APIs. This provides:

- **Type-safe tool definitions**: Tools are defined with strict schemas
- **Real-time capabilities**: Built-in support for events and subscriptions  
- **Extensibility**: Easy to add new tools and capabilities
- **Error handling**: Standardized error responses across all tools

## API Reference

### MCP Tools

The backend exposes functionality through MCP tools. Each tool follows a consistent pattern:

```python
@tool
async def tool_name(param1: str, param2: int = 10) -> dict:
    """
    Tool description.
    
    Args:
        param1: Parameter description
        param2: Optional parameter with default
        
    Returns:
        Standardized response with success, data, message fields
    """
```

### Core Tools

#### Health Tools

**`get_health_status()`**
- **Description**: Get comprehensive health status of the MCP server
- **Parameters**: None
- **Returns**: System health information

**`ping()`** 
- **Description**: Simple connectivity test
- **Parameters**: None
- **Returns**: Basic pong response with timestamp

#### SSH Tools (Planned)

**`test_server_connection(host, port, username, auth_type, credentials)`**
- **Description**: Test SSH connection to a remote server
- **Parameters**:
  - `host` (string): Server hostname or IP
  - `port` (int, default=22): SSH port
  - `username` (string): SSH username
  - `auth_type` (string): "password" or "key"
  - `credentials` (dict): Authentication data
- **Returns**: Connection test results with system info

**`prepare_server(host, port, username, auth_type, credentials, server_name?)`**
- **Description**: Prepare remote server with Docker and dependencies
- **Parameters**: Connection details plus optional server name
- **Returns**: Preparation results and server ID

#### Application Tools (Planned)

**`install_app(server_id, app_id, configuration?, custom_ports?, environment_variables?)`**
- **Description**: Install containerized application on server
- **Parameters**: 
  - `server_id` (string): Target server identifier
  - `app_id` (string): Application from catalog
  - `configuration` (dict, optional): App-specific config
  - `custom_ports` (array, optional): Custom port mappings
  - `environment_variables` (dict, optional): Additional env vars
- **Returns**: Installation results with container info

**`uninstall_app(server_id, app_name, remove_data?)`**
- **Description**: Remove application and optionally its data
- **Parameters**:
  - `server_id` (string): Target server
  - `app_name` (string): Installed application name  
  - `remove_data` (bool, default=false): Remove persistent volumes
- **Returns**: Cleanup results

### Frontend MCP Client

#### Usage

```typescript
import { useMCP } from '@/providers/MCPProvider'

function MyComponent() {
  const mcp = useMCP()
  
  const handleAction = async () => {
    try {
      const result = await mcp.callTool('get_health_status', {})
      if (result.success) {
        console.log('Health status:', result.data)
      } else {
        console.error('Error:', result.error)
      }
    } catch (error) {
      console.error('MCP call failed:', error)
    }
  }
}
```

#### Types

```typescript
interface MCPResponse<T = unknown> {
  success: boolean
  data?: T
  message?: string
  error?: string
  metadata?: {
    execution_time_ms: number
    request_id: string
    timestamp: string
  }
}
```

## Contributing Guidelines

### Code Style

**TypeScript/JavaScript:**
- Use Prettier for formatting
- Follow ESLint rules (extends @typescript-eslint/recommended)
- Use functional components with hooks
- Prefer explicit types over `any`

**Python:**
- Use Black for formatting
- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Document with docstrings

### Git Workflow

1. **Branch Naming**: Use descriptive names like `feature/server-preparation` or `fix/ssh-connection-timeout`

2. **Commit Messages**: Follow conventional commits:
   ```
   feat: add server connection testing
   fix: resolve SSH timeout issues
   docs: update API documentation
   test: add unit tests for MCP client
   ```

3. **Pull Requests**: 
   - Include tests for new functionality
   - Update documentation as needed
   - Ensure CI checks pass

### Adding New MCP Tools

1. **Backend Tool Definition**:
   ```python
   # backend/src/tools/my_tools.py
   from fastmcp import tool
   
   @tool
   async def my_new_tool(param: str) -> dict:
       """Tool description for documentation."""
       try:
           # Tool implementation
           return {
               "success": True,
               "data": {"result": param},
               "message": "Operation completed"
           }
       except Exception as e:
           return {
               "success": False,
               "error": str(e),
               "message": "Operation failed"
           }
   ```

2. **Register Tool**:
   ```python
   # backend/src/main.py
   from tools.my_tools import MyTools
   
   app.include_tools(MyTools())
   ```

3. **Frontend Types** (optional):
   ```typescript
   // frontend/src/types/tools.ts
   export interface MyToolResponse {
     result: string
   }
   ```

4. **Usage in Frontend**:
   ```typescript
   const result = await mcp.callTool<MyToolResponse>('my_new_tool', {
     param: 'value'
   })
   ```

## Testing

### Running Tests

```bash
# All tests
make test

# Frontend tests only
cd frontend && yarn test

# Backend tests only  
cd backend && python -m pytest

# Test coverage
make test-coverage
```

### Test Structure

**Frontend Tests:**
- **Unit Tests**: Component logic and utilities (`*.test.tsx`)
- **Integration Tests**: MCP client and provider interactions
- **Setup**: Uses Vitest with React Testing Library

**Backend Tests:**
- **Unit Tests**: Individual module testing (`test_*.py`)
- **Integration Tests**: MCP server and tool testing
- **Setup**: Uses pytest with async support

### Writing Tests

**Frontend Component Test:**
```typescript
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MyComponent } from './MyComponent'

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Expected Text')).toBeInTheDocument()
  })
})
```

**Backend Tool Test:**
```python
import pytest
from tools.my_tools import MyTools

@pytest.mark.asyncio
async def test_my_tool():
    tools = MyTools()
    result = await tools.my_new_tool("test")
    
    assert result["success"] is True
    assert result["data"]["result"] == "test"
```

## Deployment

### Development Deployment

```bash
# Start development environment
make dev

# Access services:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - Health check: http://localhost:8000/health
```

### Production Build

```bash
# Build production Docker image
make build

# Run production container
make run-prod
```

### Docker Deployment

```bash
# Using Docker Compose
docker-compose up -d

# Using Docker directly
docker build -t homelab-assistant .
docker run -p 80:80 -v homelab_data:/app/data homelab-assistant
```

For detailed deployment instructions, see [Technical Documentation](../technical/deployment.md).

## Debug and Troubleshooting

### Common Issues

**"MCP connection failed"**
- Check backend server is running on port 8000
- Verify CORS configuration in development
- Check network connectivity

**"SSH connection timeout"**  
- Verify target server is accessible
- Check SSH port (default 22) is open
- Validate credentials and authentication method

**"Tool not found"**
- Ensure tool is properly registered in main.py
- Check tool name spelling matches exactly
- Verify backend server restarted after changes

### Debug Logs

**Frontend:**
```bash
# Browser developer console
# Network tab shows MCP requests/responses
```

**Backend:**
```bash
# Development logs
tail -f backend/logs/app.log

# Or direct output when running:
cd backend && python src/main.py
```

### Development Tools

- **Frontend**: React Developer Tools browser extension
- **Backend**: Python debugger (pdb) and structlog output
- **Network**: Browser Network tab for MCP communication
- **Container**: Docker logs and exec for troubleshooting

---

For more specific documentation, see:
- [API Reference](../api/) - Detailed API documentation
- [User Guide](../user/) - End-user documentation  
- [Technical Docs](../technical/) - Architecture and deployment
- [Architecture Overview](../ARCHITECTURE.md) - System design details
