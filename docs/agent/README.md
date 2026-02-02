# Agent Documentation

This directory contains documentation specific to the Tomo Agent component.

## Documents

| Document | Description |
|----------|-------------|
| [Validation Refactor Plan](validation-refactor-plan.md) | Analysis and design for splitting validation.py |
| [Validation Refactor Implementation](validation-refactor-implementation.md) | Step-by-step implementation guide |
| [Validation Refactor Tasks](validation-refactor-tasks.md) | Checkbox task list for tracking progress |

## Related Documentation

- [Agent Architecture](../architecture/agent.md) - Overall agent architecture and design
- [Developer Guide: Agents](../developer/agents.md) - Developer guide for working with agents

## Agent Overview

The Tomo Agent is a Python daemon that runs on managed servers, providing:

- **WebSocket Communication**: Real-time bidirectional communication with the backend
- **Docker Operations**: Container lifecycle management via Docker SDK
- **System Commands**: Secure command execution with allowlist validation
- **Health Monitoring**: Periodic health checks and metrics collection
- **Security**: Token-based authentication, replay protection, audit logging

## Quick Links

```
agent/
├── src/
│   ├── agent.py           # Main agent class
│   ├── connection.py      # WebSocket connection management
│   ├── handler_setup.py   # RPC method registration
│   ├── security.py        # Security middleware
│   ├── auth.py            # Authentication
│   ├── config.py          # Configuration
│   ├── lib/               # Utility libraries
│   │   ├── validation.py  # Command/Docker validation (to be split)
│   │   ├── audit.py       # Audit logging
│   │   ├── encryption.py  # Token encryption
│   │   └── ...
│   └── collectors/        # Background collectors
└── tests/                 # Test suite
```
