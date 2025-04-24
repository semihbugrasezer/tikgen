import hashlib
import json
import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import jwt
from cryptography.fernet import Fernet
import platform
import uuid

logger = logging.getLogger(__name__)


class LicenseManager:
    """Manages software licensing and access control"""

    def __init__(self):
        self.license_file = "license.key"
        self.license_data = None
        self.fernet = None
        self._init_encryption()
        self.load_license()

    def _init_encryption(self):
        """Initialize encryption key"""
        try:
            # Generate or load encryption key
            key_file = ".encryption_key"
            if os.path.exists(key_file):
                with open(key_file, "rb") as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                with open(key_file, "wb") as f:
                    f.write(key)
            self.fernet = Fernet(key)
        except Exception as e:
            logger.error(f"Error initializing encryption: {e}")
            raise

    def _get_hardware_id(self) -> str:
        """Generate unique hardware ID"""
        try:
            # Get system information
            system_info = {
                "platform": platform.system(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "mac": uuid.getnode(),
            }

            # Create hash of system info
            hardware_id = hashlib.sha256(
                json.dumps(system_info, sort_keys=True).encode()
            ).hexdigest()

            return hardware_id
        except Exception as e:
            logger.error(f"Error generating hardware ID: {e}")
            raise

    def _encrypt_license(self, data: Dict[str, Any]) -> str:
        """Encrypt license data"""
        try:
            json_data = json.dumps(data)
            return self.fernet.encrypt(json_data.encode()).decode()
        except Exception as e:
            logger.error(f"Error encrypting license: {e}")
            raise

    def _decrypt_license(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt license data"""
        try:
            decrypted_data = self.fernet.decrypt(encrypted_data.encode())
            return json.loads(decrypted_data)
        except Exception as e:
            logger.error(f"Error decrypting license: {e}")
            raise

    def load_license(self) -> bool:
        """Load license from file"""
        try:
            if os.path.exists(self.license_file):
                with open(self.license_file, "r") as f:
                    encrypted_data = f.read()
                self.license_data = self._decrypt_license(encrypted_data)
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading license: {e}")
            return False

    def save_license(self, license_data: Dict[str, Any]) -> bool:
        """Save license to file"""
        try:
            encrypted_data = self._encrypt_license(license_data)
            with open(self.license_file, "w") as f:
                f.write(encrypted_data)
            self.license_data = license_data
            return True
        except Exception as e:
            logger.error(f"Error saving license: {e}")
            return False

    def validate_license(self) -> bool:
        """Validate current license"""
        try:
            if not self.license_data:
                return False

            # Check expiration
            if datetime.fromisoformat(self.license_data["expires_at"]) < datetime.now():
                logger.warning("License has expired")
                return False

            # Check hardware ID
            if self.license_data["hardware_id"] != self._get_hardware_id():
                logger.warning("Hardware ID mismatch")
                return False

            # Validate with server
            response = requests.post(
                "https://api.tikgen.com/v1/validate-license",
                json={
                    "license_key": self.license_data["license_key"],
                    "hardware_id": self._get_hardware_id(),
                },
                headers={
                    "Authorization": f"Bearer {self.license_data['access_token']}"
                },
            )

            if response.status_code != 200:
                logger.warning("License validation failed on server")
                return False

            return True
        except Exception as e:
            logger.error(f"Error validating license: {e}")
            return False

    def activate_license(self, license_key: str) -> bool:
        """Activate license with key"""
        try:
            # Get hardware ID
            hardware_id = self._get_hardware_id()

            # Validate with server
            response = requests.post(
                "https://api.tikgen.com/v1/activate-license",
                json={"license_key": license_key, "hardware_id": hardware_id},
            )

            if response.status_code != 200:
                logger.error("License activation failed")
                return False

            # Save license data
            license_data = response.json()
            license_data["hardware_id"] = hardware_id
            return self.save_license(license_data)

        except Exception as e:
            logger.error(f"Error activating license: {e}")
            return False

    def get_license_info(self) -> Optional[Dict[str, Any]]:
        """Get current license information"""
        if not self.license_data:
            return None

        return {
            "license_key": self.license_data["license_key"],
            "expires_at": self.license_data["expires_at"],
            "features": self.license_data.get("features", []),
            "status": "valid" if self.validate_license() else "invalid",
        }

    def check_feature_access(self, feature: str) -> bool:
        """Check if current license has access to a feature"""
        try:
            if not self.validate_license():
                return False

            return feature in self.license_data.get("features", [])
        except Exception as e:
            logger.error(f"Error checking feature access: {e}")
            return False
