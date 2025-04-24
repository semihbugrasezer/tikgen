from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFormLayout,
    QSpinBox,
    QComboBox,
    QGroupBox,
    QCheckBox,
    QTabWidget,
)
from PyQt5.QtCore import Qt, pyqtSignal
import json
import os
import logging

logger = logging.getLogger(__name__)


class SettingsTab(QWidget):
    """Settings tab for managing application settings"""

    # Signal for settings updates
    settings_updated = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize the settings tab"""
        super().__init__(parent)
        self.parent_window = parent
        self.settings = {}
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Create tab widget
        tab_widget = QTabWidget()

        # Content Generation Tab
        content_tab = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)

        # OpenRouter Settings
        openrouter_group = QGroupBox("OpenRouter Settings")
        openrouter_layout = QFormLayout()

        # OpenRouter API Key
        self.openrouter_key = QLineEdit()
        self.openrouter_key.setEchoMode(QLineEdit.Password)
        openrouter_layout.addRow("OpenRouter API Key:", self.openrouter_key)

        # Model Selection
        self.model_combo = QComboBox()
        self.model_combo.addItems(
            [
                "gpt-3.5-turbo",
                "gpt-4",
                "claude-3-opus",
                "claude-3-sonnet",
                "claude-3-haiku",
                "google/gemini-2.5-pro-exp-03-25:free",
            ]
        )
        openrouter_layout.addRow("AI Model:", self.model_combo)

        # Model Description
        self.model_description = QLabel("")
        self.model_description.setWordWrap(True)
        self.model_description.setStyleSheet("color: gray;")
        openrouter_layout.addRow("", self.model_description)

        # Connect model change signal
        self.model_combo.currentTextChanged.connect(self.update_model_description)

        openrouter_group.setLayout(openrouter_layout)
        content_layout.addWidget(openrouter_group)

        # Image Generation Settings
        image_group = QGroupBox("Image Generation Settings")
        image_layout = QFormLayout()

        # Image Generation API Selection
        self.image_api = QComboBox()
        self.image_api.addItems(
            ["Stable Diffusion API", "Leonardo AI", "DALL-E Mini", "Hugging Face"]
        )
        image_layout.addRow("Image Generation API:", self.image_api)

        # API Key for selected service
        self.image_api_key = QLineEdit()
        self.image_api_key.setEchoMode(QLineEdit.Password)
        image_layout.addRow("API Key:", self.image_api_key)

        # Image Style
        self.image_style = QComboBox()
        self.image_style.addItems(
            [
                "Realistic",
                "Artistic",
                "Cartoon",
                "Minimalist",
                "3D Render",
                "Watercolor",
            ]
        )
        image_layout.addRow("Image Style:", self.image_style)

        # Image Size
        self.image_size = QComboBox()
        self.image_size.addItems(
            [
                "512x512",
                "768x768",
                "1024x1024",
                "1024x1792 (Portrait)",
                "1792x1024 (Landscape)",
            ]
        )
        image_layout.addRow("Image Size:", self.image_size)

        # Max Images per Article
        self.max_images = QSpinBox()
        self.max_images.setRange(1, 5)
        self.max_images.setValue(3)
        image_layout.addRow("Max Images per Article:", self.max_images)

        image_group.setLayout(image_layout)
        content_layout.addWidget(image_group)

        # Content Settings
        content_settings_group = QGroupBox("Content Settings")
        content_settings_layout = QFormLayout()

        # Article Length
        self.article_length = QComboBox()
        self.article_length.addItems(
            [
                "Short (500-750 words)",
                "Medium (750-1000 words)",
                "Long (1000-1500 words)",
            ]
        )
        content_settings_layout.addRow("Article Length:", self.article_length)

        # Keywords per Article
        self.keywords_count = QSpinBox()
        self.keywords_count.setRange(3, 10)
        self.keywords_count.setValue(5)
        content_settings_layout.addRow("Keywords per Article:", self.keywords_count)

        content_settings_group.setLayout(content_settings_layout)
        content_layout.addWidget(content_settings_group)

        content_tab.setLayout(content_layout)
        tab_widget.addTab(content_tab, "Content Generation")

        # Pinterest Tab
        pinterest_tab = QWidget()
        pinterest_layout = QVBoxLayout()
        pinterest_layout.setSpacing(20)

        # Pinterest API Settings
        pinterest_api_group = QGroupBox("Pinterest API Settings")
        pinterest_api_layout = QFormLayout()

        self.pinterest_access_token = QLineEdit()
        self.pinterest_access_token.setEchoMode(QLineEdit.Password)
        pinterest_api_layout.addRow("Access Token:", self.pinterest_access_token)

        self.pinterest_app_id = QLineEdit()
        pinterest_api_layout.addRow("App ID:", self.pinterest_app_id)

        self.pinterest_app_secret = QLineEdit()
        self.pinterest_app_secret.setEchoMode(QLineEdit.Password)
        pinterest_api_layout.addRow("App Secret:", self.pinterest_app_secret)

        pinterest_api_group.setLayout(pinterest_api_layout)
        pinterest_layout.addWidget(pinterest_api_group)

        # Pinterest Pinning Settings
        pinning_group = QGroupBox("Pinning Settings")
        pinning_layout = QFormLayout()

        self.default_board = QLineEdit()
        pinning_layout.addRow("Default Board:", self.default_board)

        self.pin_interval = QSpinBox()
        self.pin_interval.setRange(1, 24)
        self.pin_interval.setValue(4)
        self.pin_interval.setSuffix(" hours")
        pinning_layout.addRow("Pin Interval:", self.pin_interval)

        self.max_pins_per_day = QSpinBox()
        self.max_pins_per_day.setRange(1, 50)
        self.max_pins_per_day.setValue(10)
        pinning_layout.addRow("Max Pins per Day:", self.max_pins_per_day)

        self.avoid_spam = QCheckBox("Enable Spam Avoidance")
        pinning_layout.addRow("", self.avoid_spam)

        pinning_group.setLayout(pinning_layout)
        pinterest_layout.addWidget(pinning_group)

        pinterest_tab.setLayout(pinterest_layout)
        tab_widget.addTab(pinterest_tab, "Pinterest")

        # Automation Tab
        automation_tab = QWidget()
        automation_layout = QVBoxLayout()
        automation_layout.setSpacing(20)

        # General Automation Settings
        automation_group = QGroupBox("Automation Settings")
        automation_layout_form = QFormLayout()

        self.enable_automation = QCheckBox()
        automation_layout_form.addRow("Enable Automation:", self.enable_automation)

        # Content Generation Schedule
        self.content_schedule = QComboBox()
        self.content_schedule.addItems(["Daily", "Every 2 Days", "Weekly", "Custom"])
        automation_layout_form.addRow(
            "Content Generation Schedule:", self.content_schedule
        )

        # WordPress Posting Schedule
        self.wordpress_schedule = QComboBox()
        self.wordpress_schedule.addItems(["Daily", "Every 2 Days", "Weekly", "Custom"])
        automation_layout_form.addRow(
            "WordPress Posting Schedule:", self.wordpress_schedule
        )

        automation_group.setLayout(automation_layout_form)
        automation_layout.addWidget(automation_group)

        automation_tab.setLayout(automation_layout)
        tab_widget.addTab(automation_tab, "Automation")

        # Add tab widget to main layout
        layout.addWidget(tab_widget)

        # Save Button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def load_settings(self):
        """Load settings from config"""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    self.settings = config.get("settings", {})

                    # Update UI with loaded settings
                    self.openrouter_key.setText(
                        self.settings.get("openrouter_api_key", "")
                    )
                    self.model_combo.setCurrentText(
                        self.settings.get("model", "gpt-3.5-turbo")
                    )
                    self.article_length.setCurrentText(
                        self.settings.get("article_length", "Medium (750-1000 words)")
                    )
                    self.image_style.setCurrentText(
                        self.settings.get("image_style", "Realistic")
                    )
                    self.max_images.setValue(
                        self.settings.get("max_images_per_article", 3)
                    )
                    self.keywords_count.setValue(
                        self.settings.get("keywords_per_article", 5)
                    )
                    self.enable_automation.setChecked(
                        self.settings.get("automation", {}).get("enabled", False)
                    )
                    self.content_schedule.setCurrentText(
                        self.settings.get("automation", {}).get(
                            "content_schedule", "Daily"
                        )
                    )
                    self.wordpress_schedule.setCurrentText(
                        self.settings.get("automation", {}).get(
                            "wordpress_schedule", "Daily"
                        )
                    )

                    # Load image generation settings
                    image_config = self.settings.get("image_generation", {})
                    self.image_api.setCurrentText(
                        image_config.get("provider", "Stable Diffusion API")
                    )
                    self.image_api_key.setText(image_config.get("api_key", ""))
                    self.image_size.setCurrentText(
                        image_config.get("size", "1024x1024")
                    )

                    # Load Pinterest settings
                    pinterest_config = self.settings.get("pinterest", {})
                    self.pinterest_access_token.setText(
                        pinterest_config.get("access_token", "")
                    )
                    self.pinterest_app_id.setText(pinterest_config.get("app_id", ""))
                    self.pinterest_app_secret.setText(
                        pinterest_config.get("app_secret", "")
                    )
                    self.default_board.setText(
                        pinterest_config.get("default_board", "")
                    )
                    self.pin_interval.setValue(pinterest_config.get("pin_interval", 4))
                    self.max_pins_per_day.setValue(
                        pinterest_config.get("max_pins_per_day", 10)
                    )
                    self.avoid_spam.setChecked(
                        pinterest_config.get("avoid_spam", {}).get("enabled", True)
                    )

        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load settings: {str(e)}")

    def save_settings(self):
        """Save settings to config"""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)

                # Update settings
                config["settings"] = {
                    "openrouter_api_key": self.openrouter_key.text(),
                    "model": self.model_combo.currentText(),
                    "article_length": self.article_length.currentText(),
                    "image_style": self.image_style.currentText(),
                    "max_images_per_article": self.max_images.value(),
                    "keywords_per_article": self.keywords_count.value(),
                    "automation": {
                        "enabled": self.enable_automation.isChecked(),
                        "content_schedule": self.content_schedule.currentText(),
                        "wordpress_schedule": self.wordpress_schedule.currentText(),
                    },
                    "image_generation": {
                        "provider": self.image_api.currentText(),
                        "api_key": self.image_api_key.text(),
                        "style": self.image_style.currentText(),
                        "size": self.image_size.currentText(),
                    },
                    "pinterest": {
                        "access_token": self.pinterest_access_token.text(),
                        "app_id": self.pinterest_app_id.text(),
                        "app_secret": self.pinterest_app_secret.text(),
                        "default_board": self.default_board.text(),
                        "pin_interval": self.pin_interval.value(),
                        "max_pins_per_day": self.max_pins_per_day.value(),
                        "avoid_spam": {
                            "enabled": self.avoid_spam.isChecked(),
                            "min_interval": 300,
                            "max_pins_per_day": self.max_pins_per_day.value(),
                            "random_delay": True,
                        },
                    },
                }

                with open(config_path, "w") as f:
                    json.dump(config, f, indent=4)

                # Emit signal for settings updates
                self.settings_updated.emit()

                QMessageBox.information(self, "Success", "Settings saved successfully!")

        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save settings: {str(e)}\n\n"
                "Please check the logs for more details.",
            )

    def update_model_description(self, model_name):
        """Update model description based on selection"""
        descriptions = {
            "gpt-3.5-turbo": "Fast and efficient model for general text generation",
            "gpt-4": "Most capable model for complex tasks and high-quality content",
            "claude-3-opus": "Advanced model with strong reasoning capabilities",
            "claude-3-sonnet": "Balanced model for most content generation tasks",
            "claude-3-haiku": "Lightweight model for quick responses",
            "google/gemini-2.5-pro-exp-03-25:free": "Google's latest Gemini model with advanced capabilities",
        }
        self.model_description.setText(descriptions.get(model_name, ""))
