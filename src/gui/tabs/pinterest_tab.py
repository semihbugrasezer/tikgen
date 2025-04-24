from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFormLayout,
    QSpinBox,
    QComboBox,
    QGroupBox,
    QHeaderView,
)
from PyQt5.QtCore import Qt, pyqtSignal
import json
import os
import logging
import requests
from typing import Dict, List, Optional
import datetime

logger = logging.getLogger(__name__)


class PinterestTab(QWidget):
    """Tab for managing Pinterest accounts"""

    # Signal for account updates
    accounts_updated = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize the Pinterest tab"""
        super().__init__(parent)
        self.parent_window = parent
        self.accounts = []
        self.current_page = 0
        self.page_size = 10  # Number of accounts to show per page
        self.init_ui()
        self.load_accounts()

    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout()

        # Form for adding new accounts
        form_group = QGroupBox("Add New Pinterest Account")
        form_layout = QFormLayout()

        # Access Token input
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Enter your Pinterest access token")
        form_layout.addRow("Access Token:", self.token_input)

        # Board selection
        self.board_input = QComboBox()
        self.board_input.setEnabled(False)  # Will be enabled after token validation
        form_layout.addRow("Default Board:", self.board_input)

        # Pin interval
        self.pin_interval_input = QSpinBox()
        self.pin_interval_input.setRange(1, 24)
        self.pin_interval_input.setValue(4)
        self.pin_interval_input.setSuffix(" hours")
        form_layout.addRow("Pin Interval:", self.pin_interval_input)

        # Max pins per day
        self.max_pins_input = QSpinBox()
        self.max_pins_input.setRange(1, 50)
        self.max_pins_input.setValue(10)
        form_layout.addRow("Max Pins/Day:", self.max_pins_input)

        # Test connection button
        test_button = QPushButton("Test Connection")
        test_button.clicked.connect(self.test_connection)
        form_layout.addRow("", test_button)

        # Add account button
        add_button = QPushButton("Add Account")
        add_button.clicked.connect(self.add_account)
        form_layout.addRow("", add_button)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Table for existing accounts
        table_group = QGroupBox("Pinterest Accounts")
        table_layout = QVBoxLayout()

        # Pagination controls
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.prev_page)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_page)
        self.page_label = QLabel("Page 1")
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_button)
        table_layout.addLayout(pagination_layout)

        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(6)
        self.accounts_table.setHorizontalHeaderLabels(
            ["Access Token", "Board", "Interval", "Max Pins", "Status", "Actions"]
        )
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_layout.addWidget(self.accounts_table)

        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        self.setLayout(layout)

    def load_accounts(self):
        """Load Pinterest accounts from config"""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    self.accounts = config.get("pinterest", {}).get("accounts", [])
                    self.update_table()
        except Exception as e:
            logger.error(f"Error loading Pinterest accounts: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load Pinterest accounts: {str(e)}\n\n"
                "Please check the logs for more details.",
            )

    def save_accounts(self):
        """Save Pinterest accounts to config"""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)

                if "pinterest" not in config:
                    config["pinterest"] = {}
                config["pinterest"]["accounts"] = self.accounts

                with open(config_path, "w") as f:
                    json.dump(config, f, indent=4)

                # Emit signal for account updates
                self.accounts_updated.emit()
        except Exception as e:
            logger.error(f"Error saving Pinterest accounts: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save Pinterest accounts: {str(e)}\n\n"
                "Please check the logs for more details.",
            )

    def update_table(self):
        """Update the accounts table with pagination"""
        if not self.accounts:
            self.accounts_table.setRowCount(0)
            return

        # Calculate pagination
        total_pages = (len(self.accounts) + self.page_size - 1) // self.page_size
        self.current_page = min(self.current_page, total_pages - 1)

        # Update pagination controls
        self.page_label.setText(f"Page {self.current_page + 1} of {total_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)

        # Get current page data
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.accounts))
        current_accounts = self.accounts[start_idx:end_idx]

        # Update table
        self.accounts_table.setRowCount(len(current_accounts))
        for i, account in enumerate(current_accounts):
            # Show only first 10 characters of token for security
            token = (
                account["access_token"][:10] + "..."
                if len(account["access_token"]) > 10
                else account["access_token"]
            )
            self.accounts_table.setItem(i, 0, QTableWidgetItem(token))
            self.accounts_table.setItem(i, 1, QTableWidgetItem(account["board"]))
            self.accounts_table.setItem(
                i, 2, QTableWidgetItem(str(account["pin_interval"]))
            )
            self.accounts_table.setItem(
                i, 3, QTableWidgetItem(str(account["max_pins_per_day"]))
            )

            # Status
            status_item = QTableWidgetItem(
                "Connected" if account.get("is_connected", False) else "Disconnected"
            )
            status_item.setForeground(
                Qt.green if account.get("is_connected", False) else Qt.red
            )
            self.accounts_table.setItem(i, 4, status_item)

            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(
                lambda checked, row=start_idx + i: self.remove_account(row)
            )
            self.accounts_table.setCellWidget(i, 5, remove_btn)

    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_table()

    def next_page(self):
        """Go to next page"""
        if (self.current_page + 1) * self.page_size < len(self.accounts):
            self.current_page += 1
            self.update_table()

    def test_connection(self):
        """Test connection to Pinterest API"""
        token = self.token_input.text().strip()

        if not token:
            QMessageBox.warning(self, "Error", "Please enter an access token")
            return False

        # Show progress dialog
        progress = QMessageBox(self)
        progress.setWindowTitle("Testing Connection")
        progress.setText("Testing Pinterest connection...")
        progress.setStandardButtons(QMessageBox.NoButton)
        progress.show()

        try:
            # Test Pinterest API connection
            response = requests.get(
                "https://api.pinterest.com/v5/user_account",
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )

            if response.status_code == 200:
                # Get user info
                user_info = response.json()

                # Get boards
                boards_response = requests.get(
                    "https://api.pinterest.com/v5/boards",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30,
                )

                if boards_response.status_code == 200:
                    boards = boards_response.json().get("items", [])

                    # Update board selection
                    self.board_input.clear()
                    self.board_input.addItems([board["name"] for board in boards])
                    self.board_input.setEnabled(True)

                    # Close progress dialog
                    progress.close()

                    # Show success message
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Connection successful!\n\n"
                        f"Username: {user_info.get('username', 'Unknown')}\n"
                        f"Boards Found: {len(boards)}",
                    )

                    return True
                else:
                    progress.close()
                    QMessageBox.warning(
                        self,
                        "Error",
                        f"Failed to get boards: {boards_response.status_code}\n"
                        f"Response: {boards_response.text[:200]}...",
                    )
                    return False
            else:
                progress.close()
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Connection failed with status code: {response.status_code}\n"
                    f"Response: {response.text[:200]}...",
                )
                return False

        except Exception as e:
            progress.close()
            logger.error(f"Error testing Pinterest connection: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to test connection: {str(e)}\n\n"
                "Please check the logs for more details.",
            )
            return False

    def add_account(self):
        """Add a new Pinterest account"""
        token = self.token_input.text().strip()
        board = self.board_input.currentText()
        pin_interval = self.pin_interval_input.value()
        max_pins = self.max_pins_input.value()

        if not all([token, board]):
            QMessageBox.warning(self, "Error", "Please fill in all required fields")
            return

        # Check if account already exists
        if any(account["access_token"] == token for account in self.accounts):
            QMessageBox.warning(self, "Error", "This account is already added")
            return

        # Show progress dialog
        progress = QMessageBox(self)
        progress.setWindowTitle("Adding Account")
        progress.setText("Adding Pinterest account...")
        progress.setStandardButtons(QMessageBox.NoButton)
        progress.show()

        try:
            # Test connection before adding
            if not self.test_connection():
                progress.close()
                return

            # Add new account
            new_account = {
                "access_token": token,
                "board": board,
                "pin_interval": pin_interval,
                "max_pins_per_day": max_pins,
                "is_connected": True,
                "last_checked": datetime.datetime.now().isoformat(),
            }

            self.accounts.append(new_account)
            self.save_accounts()
            self.update_table()

            # Clear form
            self.token_input.clear()
            self.board_input.clear()
            self.board_input.setEnabled(False)

            progress.close()
            QMessageBox.information(self, "Success", "Account added successfully!")

        except Exception as e:
            progress.close()
            logger.error(f"Error adding Pinterest account: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to add account: {str(e)}\n\n"
                "Please check the logs for more details.",
            )

    def remove_account(self, row):
        """Remove a Pinterest account"""
        if row < 0 or row >= len(self.accounts):
            return

        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            "Are you sure you want to remove this account?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.accounts.pop(row)
            self.save_accounts()
            self.update_table()
