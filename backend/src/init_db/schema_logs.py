"""
Logs Database Schema Initialization

Creates the logs database schema and tables if they don't exist.
Simple initialization approach for SQLite database setup.
"""

from database.connection import db_manager, Base
from models.log import LogEntryTable
import structlog

logger = structlog.get_logger("schema_logs")

async def create_logs_schema():
    """Create logs database schema and tables."""
    try:
        # Initialize database manager
        await db_manager.initialize()
        
        # Create all tables defined in Base metadata
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Logs database schema created successfully")
        
    except Exception as e:
        logger.error("Failed to create logs database schema", error=str(e))
        raise


async def check_schema_exists() -> bool:
    """Check if logs schema already exists."""
    try:
        await db_manager.initialize()
        
        async with db_manager.engine.begin() as conn:
            # Check if log_entries table exists
            from sqlalchemy import text
            result = await conn.run_sync(
                lambda sync_conn: sync_conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='log_entries'")
                ).fetchone()
            )
            
            exists = result is not None
            logger.info("Schema existence check completed", exists=exists)
            return exists
            
    except Exception as e:
        logger.error("Failed to check schema existence", error=str(e))
        return False


async def initialize_logs_database():
    """Initialize logs database - create schema if needed."""
    try:
        schema_exists = await check_schema_exists()
        
        if not schema_exists:
            logger.info("Creating logs database schema")
            await create_logs_schema()
        else:
            logger.info("Logs database schema already exists")
            
    except Exception as e:
        logger.error("Failed to initialize logs database", error=str(e))
        raise
