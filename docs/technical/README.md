# Technical Documentation

This section contains technical specifications, schema designs, and implementation details.

## Documents

| Document | Description |
|----------|-------------|
| [Database Schema](database-schema.md) | Settings database schema design |
| [Data Retention Architecture](data-retention-architecture.md) | Data retention system design |
| [Logging Specification](../logging-specification.md) | Logging standards and configuration |

## Overview

These documents provide deep technical details for developers implementing or extending the Tomo system.

### Database Schema

The [database schema](database-schema.md) document covers:
- Settings management tables (`system_settings`, `user_settings`, `settings_audit`)
- Schema architecture decisions
- Integration patterns for backend and frontend

### Data Retention

The [data retention architecture](data-retention-architecture.md) describes:
- Data lifecycle management
- Cleanup policies and scheduling
- Compliance considerations

### Logging

The [logging specification](../logging-specification.md) defines:
- Structured logging format
- Log levels and categories
- Security considerations (credential masking)

## Related Documentation

- [Architecture](../architecture/README.md) - System architecture overview
- [Developer Guide](../developer/README.md) - Development setup
- [API Reference](../api/README.md) - MCP tools documentation
