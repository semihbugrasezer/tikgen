#!/usr/bin/env python3
"""
Database initialization script for AutoPinner Pro.
This script creates the necessary database tables and initializes default settings.
"""

import os
import sys
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.database import db_manager, Base, Pin
from src.utils.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize the database with required tables"""
    try:
        # Get database configuration from config file
        config = get_config()
        db_config = config.get("database", {})

        # Create database engine with default SQLite if no config
        engine = create_engine(
            db_config.get("url", "sqlite:///app.db"),
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
        )

        # Create tables
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")

        # Initialize database manager
        db_manager.init(engine)
        logger.info("Database manager initialized")

        return True

    except SQLAlchemyError as e:
        logger.error(f"Database initialization failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}")
        return False


def verify_database():
    """Verify database connection and table structure."""
    try:
        # Test database connection
        with db_manager.get_session() as session:
            # Try to query the pins table
            session.query(Pin).first()
            logger.info("Database verification successful")
            return True
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False


if __name__ == "__main__":
    if init_database():
        logger.info("Database initialization completed successfully")

        if verify_database():
            logger.info("Database verification completed successfully")
        else:
            logger.error("Database verification failed")
            sys.exit(1)
    else:
        logger.error("Database initialization failed")
        sys.exit(1)
