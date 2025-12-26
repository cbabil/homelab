# Homelab Assistant

A modern web application for managing homelab servers and applications using the Model Context Protocol (MCP).

## Phase 1 Implementation Status ✅

This repository contains the Phase 1 foundation implementation as defined in the implementation plan:

### ✅ Completed Phase 1 Tasks

- **Project Structure**: Clean monorepo with `frontend/` and `backend/` directories
- **Backend Foundation**: Python 3.11+ with fastmcp MCP server framework
- **Dependencies**: Complete `requirements.txt` with all architectural dependencies
- **MCP Server**: Basic server structure with health check tools
- **SSH Manager**: Paramiko-based SSH connection management with security
- **Frontend Foundation**: React 18+ with Vite, TypeScript, and modern tooling
- **MCP Client**: Type-safe MCP protocol client for frontend-backend communication
- **Project Standards**: 100-line file limits, ESLint configuration, structured logging

### 🏗️ Architecture Highlights

- **MCP Protocol**: Uses Model Context Protocol for frontend-backend communication
- **Security-First**: AES-256 credential encryption, secure SSH practices
- **Type Safety**: Full TypeScript coverage with Pydantic backend models
- **Modern Stack**: React 18+, Python 3.11+, Vite, TailwindCSS
- **Development Ready**: Hot reload, linting, structured logging

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ and Yarn (for local frontend development)
- Python 3.11+ (for local backend development)

### Development Setup

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd homelab
   ./scripts/setup.sh
   ```

2. **Start development environment**:
   ```bash
   docker-compose -f docker-compose.dev.yml up
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Health Check: http://localhost:8000/health

### Local Development

For faster development with hot reload:

```bash
# Terminal 1 - Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=$(pwd)/src
python -m uvicorn src.main:app --reload

# Terminal 2 - Frontend  
cd frontend
yarn install
yarn dev
```

## Project Structure

```
homelab/
├── frontend/                    # React TypeScript frontend
│   ├── src/
│   │   ├── components/         # UI components
│   │   ├── services/           # MCP client & services
│   │   ├── providers/          # React context providers
│   │   ├── types/              # TypeScript definitions
│   │   └── pages/              # Application pages
│   └── package.json
├── backend/                     # Python MCP server
│   ├── src/
│   │   ├── main.py            # FastMCP server entry
│   │   ├── tools/             # MCP tool implementations
│   │   ├── services/          # Business logic services
│   │   ├── models/            # Pydantic data models
│   │   └── lib/               # Shared backend helpers
│   └── requirements.txt
├── docker/                      # Container configurations
├── scripts/                     # Setup and build scripts
└── docs/                       # Architecture documentation
```

## Technology Stack

### Frontend
- **React 18+** - Modern functional components with hooks
- **TypeScript** - Type safety and developer experience
- **Vite** - Fast development server and optimized builds
- **TailwindCSS** - Utility-first styling
- **React Query** - Server state management

### Backend
- **Python 3.11+** - Modern Python with performance improvements
- **fastmcp** - Model Context Protocol server framework
- **paramiko** - Pure Python SSH client library
- **Pydantic** - Data validation and settings management
- **structlog** - Structured logging with JSON output

### Development
- **Docker** - Containerized development environment
- **ESLint** - Code linting with 100-line limits enforced
- **Vitest** - Unit testing framework

## Development Guidelines

### Mandatory Rules (Phase 1 Implementation)

1. **Testing & Documentation**: All changes must include tests and documentation
2. **100-Line Limit**: Maximum 100 lines per file AND function (enforced by ESLint)
3. **Agent Usage**: Development tasks must use specialized agents
4. **Security Review**: Security-related changes require security review

### Code Quality

- **TypeScript Strict Mode**: All frontend code uses strict TypeScript
- **Pydantic Models**: All backend data uses validated Pydantic models  
- **Structured Logging**: JSON-formatted logs with sensitive data filtering
- **Error Handling**: Comprehensive error handling with user-friendly messages

## Next Steps (Phase 2+)

The Phase 1 foundation is now complete and ready for Phase 2 implementation:

- **Server Management**: Complete server preparation and configuration
- **Application Catalog**: Browse and install containerized applications
- **Real-time Monitoring**: System resource and application monitoring
- **Advanced Features**: Backup, cleanup, and maintenance automation

## Security Notes

- Credentials are encrypted with AES-256 encryption
- SSH connections use secure paramiko configuration
- No sensitive data in logs (automatically filtered)
- Environment-based configuration for production secrets

## Support

For issues and questions:
1. Check the architecture documentation in `docs/`
2. Review the implementation plan for feature details
3. Check logs for troubleshooting information

---

**Status**: Phase 1 Complete ✅  
**Next Phase**: Server Management (Phase 2)  
**Architecture**: MCP Protocol + React + Python + Docker
