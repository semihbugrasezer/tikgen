from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QProgressBar,
)
from PyQt5.QtCore import Qt, pyqtSignal
import logging
from src.utils.license_manager import LicenseManager

logger = logging.getLogger(__name__)


class LicenseDialog(QDialog):
    """Dialog for license activation"""

    license_activated = pyqtSignal()  # Signal emitted when license is activated

    def __init__(self, parent=None):
        super().__init__(parent)
        self.license_manager = LicenseManager()
        self.init_ui()
        self.load_current_license()

    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("TikGen License Activation")
        self.setMinimumWidth(400)
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Current license info
        self.license_info = QLabel()
        self.license_info.setWordWrap(True)
        layout.addWidget(self.license_info)

        # License key input
        key_layout = QHBoxLayout()
        key_label = QLabel("License Key:")
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Enter your license key")
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_input)
        layout.addLayout(key_layout)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Buttons
        button_layout = QHBoxLayout()
        self.activate_button = QPushButton("Activate")
        self.activate_button.clicked.connect(self.activate_license)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.activate_button)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_current_license(self):
        """Load and display current license information"""
        try:
            license_info = self.license_manager.get_license_info()
            if license_info:
                status_color = "green" if license_info["status"] == "valid" else "red"
                self.license_info.setText(
                    f"""
                    <b>Current License:</b><br>
                    Key: {license_info['license_key']}<br>
                    Expires: {license_info['expires_at']}<br>
                    Status: <span style='color: {status_color}'>{license_info['status']}</span><br>
                    Features: {', '.join(license_info['features'])}
                    """
                )
            else:
                self.license_info.setText("No license activated")
        except Exception as e:
            logger.error(f"Error loading license info: {e}")
            self.license_info.setText("Error loading license information")

    def activate_license(self):
        """Activate the entered license key"""
        try:
            license_key = self.key_input.text().strip()
            if not license_key:
                QMessageBox.warning(self, "Error", "Please enter a license key")
                return

            # Show progress
            self.progress.setVisible(True)
            self.progress.setValue(0)
            self.activate_button.setEnabled(False)

            # Activate license
            if self.license_manager.activate_license(license_key):
                self.progress.setValue(100)
                QMessageBox.information(
                    self, "Success", "License activated successfully!"
                )
                self.license_activated.emit()
                self.load_current_license()
            else:
                QMessageBox.critical(
                    self, "Error", "Failed to activate license. Please check your key."
                )

        except Exception as e:
            logger.error(f"Error activating license: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            self.progress.setVisible(False)
            self.activate_button.setEnabled(True)
