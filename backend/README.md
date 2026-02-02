# Tomo Backend

Python FastMCP server for tomo management and automation.

## Quick Start

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server
python src/main.py
```

## Project Structure

```
backend/
├── src/
│   ├── main.py          # FastMCP server entry point
│   ├── tools/           # MCP tool implementations
│   ├── services/        # Business logic services
│   ├── models/          # Pydantic data models
│   ├── lib/             # Utilities (encryption, logging)
│   ├── database/        # Database connection management
│   └── config/          # Configuration
├── tests/               # Test suite (unit, integration, security)
├── data/                # Runtime data and catalog
└── requirements.txt     # Python dependencies
```

## Configuration

Environment variables:
- `JWT_SECRET_KEY` - JWT signing key (required)
- `TOMO_MASTER_PASSWORD` - Encryption master password
- `TOMO_SALT` - Encryption salt
- `DATA_DIRECTORY` - Data storage path (default: `./data`)
- `MCP_LOG_LEVEL` - Logging level (default: `INFO`)

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run by category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/security/ -v
```

## Documentation

For comprehensive documentation, see:
- [Architecture](../docs/architecture/README.md) - System design
- [Developer Guide](../docs/developer/README.md) - Development setup
- [API Reference](../docs/api/README.md) - MCP tools documentation
- [Database Schema](../docs/technical/database-schema.md) - Schema design
- [Settings Implementation](../docs/developer/settings-implementation.md) - Settings patterns
