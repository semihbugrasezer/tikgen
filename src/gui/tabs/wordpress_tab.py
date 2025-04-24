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
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods import posts

logger = logging.getLogger(__name__)


class WordPressTab(QWidget):
    """Tab for managing WordPress sites"""

    # Signal for site updates
    sites_updated = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize the WordPress tab"""
        super().__init__(parent)
        self.parent_window = parent
        self.sites = []
        self.current_page = 0
        self.page_size = 10  # Number of sites to show per page
        self.init_ui()
        self.load_sites()

    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Form for adding new sites
        form_group = QGroupBox("Add New WordPress Site")
        form_layout = QFormLayout()

        # URL input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        form_layout.addRow("Site URL:", self.url_input)

        # Username input
        self.username_input = QLineEdit()
        form_layout.addRow("Username:", self.username_input)

        # Password input
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password:", self.password_input)

        # Category selection
        self.category_input = QComboBox()
        self.category_input.addItems(
            [
                "Technology",
                "Business",
                "Marketing",
                "Lifestyle",
                "Health",
                "Education",
                "Entertainment",
                "Other",
            ]
        )
        form_layout.addRow("Category:", self.category_input)

        # Post interval
        self.post_interval_input = QSpinBox()
        self.post_interval_input.setRange(1, 24)
        self.post_interval_input.setValue(4)
        self.post_interval_input.setSuffix(" hours")
        form_layout.addRow("Post Interval:", self.post_interval_input)

        # Max posts per day
        self.max_posts_input = QSpinBox()
        self.max_posts_input.setRange(1, 10)
        self.max_posts_input.setValue(2)
        form_layout.addRow("Max Posts/Day:", self.max_posts_input)

        # Buttons layout
        buttons_layout = QHBoxLayout()

        # Test connection button
        test_button = QPushButton("Test Connection")
        test_button.clicked.connect(self.test_connection)
        buttons_layout.addWidget(test_button)

        # Add site button
        add_button = QPushButton("Add Site")
        add_button.clicked.connect(self.add_site)
        buttons_layout.addWidget(add_button)

        form_layout.addRow("", buttons_layout)
        form_group.setLayout(form_layout)

        # Table for existing sites
        table_group = QGroupBox("WordPress Sites")
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

        self.sites_table = QTableWidget()
        self.sites_table.setColumnCount(7)
        self.sites_table.setHorizontalHeaderLabels(
            [
                "URL",
                "Username",
                "Category",
                "Interval",
                "Max Posts",
                "Status",
                "Actions",
            ]
        )
        self.sites_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_layout.addWidget(self.sites_table)

        table_group.setLayout(table_layout)

        # Add components to main layout
        layout.addWidget(form_group)
        layout.addWidget(table_group)
        self.setLayout(layout)

    def load_sites(self):
        """Load WordPress sites from config with pagination"""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    self.sites = config.get("wordpress", {}).get("sites", [])
                    self.update_table()
        except Exception as e:
            logger.error(f"Error loading WordPress sites: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load WordPress sites: {str(e)}\n\n"
                "Please check the logs for more details.",
            )

    def save_sites(self):
        """Save WordPress sites to config"""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)

                if "wordpress" not in config:
                    config["wordpress"] = {}
                config["wordpress"]["sites"] = self.sites

                with open(config_path, "w") as f:
                    json.dump(config, f, indent=4)

                # Emit signal for site updates
                self.sites_updated.emit()

                # Notify parent window if it exists
                if self.parent_window and hasattr(
                    self.parent_window, "reload_integrations"
                ):
                    self.parent_window.reload_integrations()
        except Exception as e:
            logger.error(f"Error saving WordPress sites: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save WordPress sites: {str(e)}\n\n"
                "Please check the logs for more details.",
            )

    def update_table(self):
        """Update the sites table with pagination"""
        if not self.sites:
            self.sites_table.setRowCount(0)
            return

        # Calculate pagination
        total_pages = (len(self.sites) + self.page_size - 1) // self.page_size
        self.current_page = min(self.current_page, total_pages - 1)

        # Update pagination controls
        self.page_label.setText(f"Page {self.current_page + 1} of {total_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)

        # Get current page data
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.sites))
        current_sites = self.sites[start_idx:end_idx]

        # Update table
        self.sites_table.setRowCount(len(current_sites))
        for i, site in enumerate(current_sites):
            self.sites_table.setItem(i, 0, QTableWidgetItem(site["url"]))
            self.sites_table.setItem(i, 1, QTableWidgetItem(site["username"]))
            self.sites_table.setItem(i, 2, QTableWidgetItem(site["category"]))
            self.sites_table.setItem(i, 3, QTableWidgetItem(str(site["post_interval"])))
            self.sites_table.setItem(
                i, 4, QTableWidgetItem(str(site["max_posts_per_day"]))
            )

            # Status
            status_item = QTableWidgetItem(
                "Connected" if site.get("is_connected", False) else "Disconnected"
            )
            status_item.setForeground(
                Qt.green if site.get("is_connected", False) else Qt.red
            )
            self.sites_table.setItem(i, 5, status_item)

            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(
                lambda checked, row=start_idx + i: self.remove_site(row)
            )
            self.sites_table.setCellWidget(i, 6, remove_btn)

    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_table()

    def next_page(self):
        """Go to next page"""
        if (self.current_page + 1) * self.page_size < len(self.sites):
            self.current_page += 1
            self.update_table()

    def add_site(self):
        """Add a new WordPress site with improved validation"""
        url = self.url_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        category = self.category_input.currentText()
        post_interval = self.post_interval_input.value()
        max_posts = self.max_posts_input.value()

        if not all([url, username, password]):
            QMessageBox.warning(self, "Error", "Please fill in all required fields")
            return

        # Validate URL format
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self.url_input.setText(url)

        # Check if site already exists
        if any(site["url"] == url for site in self.sites):
            QMessageBox.warning(self, "Error", "This site is already added")
            return

        # Show progress dialog
        progress = QMessageBox(self)
        progress.setWindowTitle("Adding Site")
        progress.setText("Adding WordPress site...")
        progress.setStandardButtons(QMessageBox.NoButton)
        progress.show()

        try:
            # Test connection before adding
            if not self.test_connection():
                progress.close()
                return

            # Add new site
            new_site = {
                "url": url,
                "username": username,
                "password": password,
                "category": category,
                "post_interval": post_interval,
                "max_posts_per_day": max_posts,
                "is_connected": True,
                "last_checked": datetime.datetime.now().isoformat(),
            }

            self.sites.append(new_site)
            self.save_sites()
            self.update_table()

            # Clear form
            self.url_input.clear()
            self.username_input.clear()
            self.password_input.clear()

            progress.close()
            QMessageBox.information(self, "Success", "Site added successfully!")

        except Exception as e:
            progress.close()
            logger.error(f"Error adding WordPress site: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to add site: {str(e)}\n\n"
                "Please check the logs for more details.",
            )

    def remove_site(self, row):
        """Remove a WordPress site"""
        if row < 0 or row >= len(self.sites):
            return

        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            "Are you sure you want to remove this site?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.sites.pop(row)
            self.save_sites()
            self.update_table()

    def test_connection(self):
        """Test connection to WordPress site with improved error handling"""
        url = self.url_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not all([url, username, password]):
            QMessageBox.warning(self, "Error", "Please fill in all required fields")
            return False

        # Show progress dialog
        progress = QMessageBox(self)
        progress.setWindowTitle("Testing Connection")
        progress.setText("Testing WordPress connection...")
        progress.setStandardButtons(QMessageBox.NoButton)
        progress.show()

        try:
            # First try REST API
            try:
                response = requests.get(
                    f"{url}/wp-json/wp/v2/posts",
                    auth=(username, password),
                    timeout=30,
                    verify=False,
                )

                if response.status_code == 200:
                    # Get WordPress version and site info
                    site_info = response.json()
                    wordpress_version = response.headers.get("X-WP-Version", "Unknown")

                    # Close progress dialog
                    progress.close()

                    # Show success message with details
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Connection successful!\n\n"
                        f"WordPress Version: {wordpress_version}\n"
                        f"Posts Found: {len(site_info)}",
                    )

                    # Update connection status in the form
                    self.update_connection_status(True)
                    return True

            except Exception as rest_error:
                logger.warning(f"REST API test failed: {str(rest_error)}")

            # If REST API fails, try XML-RPC
            try:
                client = Client(f"{url}/xmlrpc.php", username, password)
                # Test connection by getting recent posts
                client.call(posts.GetPosts({"number": 1}))

                # Close progress dialog
                progress.close()

                # Show success message
                QMessageBox.information(
                    self, "Success", "Connection successful using XML-RPC!"
                )

                # Update connection status in the form
                self.update_connection_status(True)
                return True

            except Exception as xmlrpc_error:
                logger.error(f"XML-RPC test failed: {str(xmlrpc_error)}")

                # Close progress dialog
                progress.close()

                # Show error message
                QMessageBox.warning(
                    self,
                    "Connection Error",
                    "Could not connect to WordPress site. Please check:\n"
                    "1. The site URL is correct\n"
                    "2. XML-RPC is enabled on your WordPress site\n"
                    "3. Your credentials are correct\n"
                    "4. Your site is accessible",
                )

                self.update_connection_status(False)
                return False

        except Exception as e:
            progress.close()
            logger.error(f"Error testing WordPress connection: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to test connection: {str(e)}\n\n"
                "Please check the logs for more details.",
            )
            self.update_connection_status(False)
            return False

    def update_connection_status(self, is_connected):
        """Update the connection status in the UI"""
        # Update the status in the current form
        if hasattr(self, "status_label"):
            self.status_label.setText("Connected" if is_connected else "Disconnected")
            self.status_label.setStyleSheet(
                "color: green;" if is_connected else "color: red;"
            )

        # Update the status in the sites table if this is an existing site
        for i in range(self.sites_table.rowCount()):
            if self.sites_table.item(i, 0).text() == self.url_input.text():
                status_item = QTableWidgetItem(
                    "Connected" if is_connected else "Disconnected"
                )
                status_item.setForeground(Qt.green if is_connected else Qt.red)
                self.sites_table.setItem(i, 5, status_item)
                break
