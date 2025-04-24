import json
import os
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def get_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Load configuration from file or return default config"""
    default_config = {
        "ENABLE_WEB_SERVER": "False",
        "WEB_SERVER_PORT": "5000",
        "DB_PATH": "autopinner.db",
        "LOG_LEVEL": "INFO",
        "AUTO_START": "False",
        "CHECK_UPDATES": "True",
        "BACKUP_ENABLED": "True",
        "BACKUP_INTERVAL": "24",  # hours
    }

    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                # Merge with default config to ensure all keys exist
                return {**default_config, **config}
        else:
            # Create default config file
            with open(config_path, "w") as f:
                json.dump(default_config, f, indent=4)
            return default_config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return default_config


class ConfigManager:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    self.config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self.config = self.get_default_config()
                self.save_config()
                logger.info(f"Default configuration created at {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config = self.get_default_config()

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set a configuration value"""
        self.config[key] = value
        self.save_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "app": {"name": "TikGen", "version": "1.0.0", "debug": False},
            "database": {"path": "autopinner.db", "backup_path": "backups"},
            "wordpress": {"sites": []},
            "pinterest": {"api_key": "", "api_secret": ""},
            "content": {"templates_dir": "templates", "output_dir": "output"},
            "logging": {"level": "INFO", "file": "app.log"},
        }
