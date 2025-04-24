#!/usr/bin/env python3
"""
Directory creation script for AutoPinner Pro.
This script creates all required directories for the application.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Required directories
REQUIRED_DIRS = [
    "data",
    "data/images",
    "data/exports",
    "logs",
    "templates",
    "templates/content",
    "config",
    "scripts",
    "docs",
    "docs/working-memory",
    "docs/working-memory/open",
    "docs/working-memory/done",
    "docs/templates",
    "docs/templates/feature",
]


def create_directories():
    """Create all required directories."""
    base_path = Path(__file__).parent.parent
    created_dirs = []
    failed_dirs = []

    for dir_path in REQUIRED_DIRS:
        full_path = base_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            logger.info(f"Created directory: {dir_path}")
        except Exception as e:
            failed_dirs.append((dir_path, str(e)))
            logger.error(f"Failed to create directory {dir_path}: {e}")

    return created_dirs, failed_dirs


def create_initial_files():
    """Create initial files in the directories."""
    base_path = Path(__file__).parent.parent

    # Create .gitkeep files in empty directories
    for dir_path in REQUIRED_DIRS:
        gitkeep_path = base_path / dir_path / ".gitkeep"
        if not any((base_path / dir_path).iterdir()):
            gitkeep_path.touch()
            logger.info(f"Created .gitkeep in {dir_path}")

    # Create initial README files
    readme_paths = {
        "docs": "# AutoPinner Pro Documentation\n\nThis directory contains all documentation for the AutoPinner Pro project.",
        "docs/working-memory": "# Working Memory\n\nThis directory contains active and completed tasks.",
        "docs/templates": "# Templates\n\nThis directory contains templates for various project components.",
        "docs/templates/feature": "# Feature Templates\n\nThis directory contains templates for feature documentation.",
    }

    for path, content in readme_paths.items():
        readme_file = base_path / path / "README.md"
        if not readme_file.exists():
            readme_file.write_text(content)
            logger.info(f"Created README.md in {path}")


def main():
    """Main function to create directories and initial files."""
    logger.info("Starting directory creation...")

    created_dirs, failed_dirs = create_directories()

    if created_dirs:
        logger.info("\nSuccessfully created directories:")
        for dir_path in created_dirs:
            logger.info(f"  ✓ {dir_path}")

    if failed_dirs:
        logger.error("\nFailed to create directories:")
        for dir_path, error in failed_dirs:
            logger.error(f"  ✗ {dir_path}: {error}")

    logger.info("\nCreating initial files...")
    create_initial_files()

    if not failed_dirs:
        logger.info("\nDirectory setup completed successfully!")
        return 0
    else:
        logger.error(
            "\nDirectory setup completed with errors. Please check the logs above."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
