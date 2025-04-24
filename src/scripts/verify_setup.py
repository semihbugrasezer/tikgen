#!/usr/bin/env python3
"""
Setup verification script for AutoPinner Pro.
This script checks all components of the system and verifies their configuration.
"""

import os
import sys
import logging
import requests
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from src.utils.config import get_config

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class SetupVerifier:
    """Class to verify all components of the system."""

    def __init__(self):
        """Initialize the verifier with environment variables."""
        load_dotenv()
        self.config = get_config()

    def verify_env_file(self):
        """Verify .env file exists and contains required variables."""
        required_vars = [
            "OPENAI_API_KEY",
            "PINTEREST_ACCESS_TOKEN",
            "PINTEREST_APP_ID",
            "PINTEREST_APP_SECRET",
            "DATABASE_URL",
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return False

        logger.info("Environment variables verified successfully")
        return True

    def verify_database(self):
        """Verify database connection and structure."""
        try:
            db_url = os.getenv("DATABASE_URL", "sqlite:///autopinner.db")
            engine = create_engine(db_url)

            with engine.connect() as conn:
                # Check if tables exist
                tables = engine.table_names()
                required_tables = [
                    "settings",
                    "tasks",
                    "content",
                    "pins",
                    "analytics",
                    "logs",
                ]

                missing_tables = [
                    table for table in required_tables if table not in tables
                ]

                if missing_tables:
                    logger.error(f"Missing required tables: {missing_tables}")
                    return False

            logger.info("Database verification passed")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Database verification failed: {e}")
            return False

    def verify_openai_api(self):
        """Verify OpenAI API connection."""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("OpenAI API key not found")
                return False

            # Test API connection
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            response = requests.get("https://api.openai.com/v1/models", headers=headers)

            if response.status_code != 200:
                logger.error(f"OpenAI API verification failed: {response.text}")
                return False

            logger.info("OpenAI API verification passed")
            return True

        except Exception as e:
            logger.error(f"OpenAI API verification failed: {e}")
            return False

    def verify_pinterest_api(self):
        """Verify Pinterest API connection."""
        try:
            access_token = os.getenv("PINTEREST_ACCESS_TOKEN")
            if not access_token:
                logger.error("Pinterest access token not found")
                return False

            # Test API connection
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            response = requests.get(
                "https://api.pinterest.com/v5/user_account", headers=headers
            )

            if response.status_code != 200:
                logger.error(f"Pinterest API verification failed: {response.text}")
                return False

            logger.info("Pinterest API verification passed")
            return True

        except Exception as e:
            logger.error(f"Pinterest API verification failed: {e}")
            return False

    def verify_directories(self):
        """Verify required directories exist."""
        required_dirs = [
            "data",
            "data/images",
            "data/exports",
            "logs",
            "templates",
            "templates/content",
        ]

        missing_dirs = []
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_path)

        if missing_dirs:
            logger.error(f"Missing required directories: {missing_dirs}")
            return False

        logger.info("Directory structure verification passed")
        return True

    def verify_all(self):
        """Verify all components of the system."""
        verifications = {
            "Environment Variables": self.verify_env_file,
            "Database": self.verify_database,
            "OpenAI API": self.verify_openai_api,
            "Pinterest API": self.verify_pinterest_api,
            "Directory Structure": self.verify_directories,
        }

        results = {}
        all_passed = True

        for name, verify_func in verifications.items():
            logger.info(f"Verifying {name}...")
            result = verify_func()
            results[name] = result
            if not result:
                all_passed = False

        # Print summary
        logger.info("\nVerification Summary:")
        for name, result in results.items():
            status = "✓ PASSED" if result else "✗ FAILED"
            logger.info(f"{name}: {status}")

        return all_passed


if __name__ == "__main__":
    verifier = SetupVerifier()

    if verifier.verify_all():
        logger.info("\nAll verifications passed successfully!")
        sys.exit(0)
    else:
        logger.error("\nSome verifications failed. Please check the logs above.")
        sys.exit(1)
