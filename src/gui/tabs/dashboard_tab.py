from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QGridLayout,
    QProgressBar,
    QFrame,
    QScrollArea,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QColor, QPalette, QFont, QIcon
import datetime
import logging
from typing import Optional
from src.utils.database import Pin

logger = logging.getLogger(__name__)


class StatCard(QFrame):
    """A card widget for displaying statistics"""

    def __init__(self, title: str, value: str, icon: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            """
            QFrame#statCard {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
            QFrame#statCard:hover {
                border: 1px solid #0078D7;
            }
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(
            """
            color: #666666;
            font-size: 14px;
            font-weight: 500;
        """
        )
        layout.addWidget(title_label)

        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(
            """
            color: #333333;
            font-size: 24px;
            font-weight: bold;
        """
        )
        layout.addWidget(value_label)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(120)


class ChartCard(QFrame):
    """A card widget for displaying charts"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("chartCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            """
            QFrame#chartCard {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(
            """
            color: #333333;
            font-size: 16px;
            font-weight: bold;
        """
        )
        layout.addWidget(title_label)

        # Chart placeholder
        chart_placeholder = QLabel("Chart will be displayed here")
        chart_placeholder.setAlignment(Qt.AlignCenter)
        chart_placeholder.setStyleSheet(
            """
            color: #666666;
            font-size: 14px;
        """
        )
        layout.addWidget(chart_placeholder)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(300)


class DashboardTab(QWidget):
    """Dashboard tab with real-time statistics and status"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        self.setup_timer()

    def set_worker_status(self, running: bool, paused: bool = False):
        """Update the worker status display"""
        if running:
            if paused:
                self.worker_status.setText("Worker: Paused")
                self.worker_status.setStyleSheet("color: orange;")
            else:
                self.worker_status.setText("Worker: Running")
                self.worker_status.setStyleSheet("color: green;")
        else:
            self.worker_status.setText("Worker: Not Running")
            self.worker_status.setStyleSheet("color: gray;")

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Status Overview
        status_group = QGroupBox("System Status")
        status_layout = QGridLayout()

        # Worker Status
        self.worker_status = QLabel("Worker: Not Running")
        self.worker_status.setStyleSheet("color: gray;")
        status_layout.addWidget(self.worker_status, 0, 0)

        # Web Server Status
        self.server_status = QLabel("Web Server: Stopped")
        self.server_status.setStyleSheet("color: gray;")
        status_layout.addWidget(self.server_status, 0, 1)

        # Database Status
        self.db_status = QLabel("Database: Connected")
        self.db_status.setStyleSheet("color: green;")
        status_layout.addWidget(self.db_status, 0, 2)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Content Statistics
        content_group = QGroupBox("Content Statistics")
        content_layout = QGridLayout()

        # Total Posts
        self.total_posts = QLabel("0")
        self.total_posts.setFont(QFont("Arial", 24, QFont.Bold))
        content_layout.addWidget(QLabel("Total Posts:"), 0, 0)
        content_layout.addWidget(self.total_posts, 0, 1)

        # Posts Today
        self.posts_today = QLabel("0")
        self.posts_today.setFont(QFont("Arial", 24, QFont.Bold))
        content_layout.addWidget(QLabel("Posts Today:"), 1, 0)
        content_layout.addWidget(self.posts_today, 1, 1)

        # Pending Posts
        self.pending_posts = QLabel("0")
        self.pending_posts.setFont(QFont("Arial", 24, QFont.Bold))
        content_layout.addWidget(QLabel("Pending Posts:"), 2, 0)
        content_layout.addWidget(self.pending_posts, 2, 1)

        content_group.setLayout(content_layout)
        layout.addWidget(content_group)

        # Pinterest Statistics
        self.pinterest_group = QGroupBox("Pinterest Statistics")
        pinterest_layout = QGridLayout()

        # Total Pins
        self.total_pins = QLabel("0")
        self.total_pins.setFont(QFont("Arial", 24, QFont.Bold))
        pinterest_layout.addWidget(QLabel("Total Pins:"), 0, 0)
        pinterest_layout.addWidget(self.total_pins, 0, 1)

        # Pins Today
        self.pins_today = QLabel("0")
        self.pins_today.setFont(QFont("Arial", 24, QFont.Bold))
        pinterest_layout.addWidget(QLabel("Pins Today:"), 1, 0)
        pinterest_layout.addWidget(self.pins_today, 1, 1)

        # Total Saves
        self.total_saves = QLabel("0")
        self.total_saves.setFont(QFont("Arial", 24, QFont.Bold))
        pinterest_layout.addWidget(QLabel("Total Saves:"), 2, 0)
        pinterest_layout.addWidget(self.total_saves, 2, 1)

        # Total Clicks
        self.total_clicks = QLabel("0")
        self.total_clicks.setFont(QFont("Arial", 24, QFont.Bold))
        pinterest_layout.addWidget(QLabel("Total Clicks:"), 3, 0)
        pinterest_layout.addWidget(self.total_clicks, 3, 1)

        self.pinterest_group.setLayout(pinterest_layout)
        layout.addWidget(self.pinterest_group)
        self.pinterest_group.setVisible(False)  # Initially hidden

        # WordPress Statistics
        wordpress_group = QGroupBox("WordPress Statistics")
        wordpress_layout = QGridLayout()

        # Total Posts
        self.wp_total_posts = QLabel("0")
        self.wp_total_posts.setFont(QFont("Arial", 24, QFont.Bold))
        wordpress_layout.addWidget(QLabel("Total Posts:"), 0, 0)
        wordpress_layout.addWidget(self.wp_total_posts, 0, 1)

        # Posts Today
        self.wp_posts_today = QLabel("0")
        self.wp_posts_today.setFont(QFont("Arial", 24, QFont.Bold))
        wordpress_layout.addWidget(QLabel("Posts Today:"), 1, 0)
        wordpress_layout.addWidget(self.wp_posts_today, 1, 1)

        # Total Views
        self.wp_total_views = QLabel("0")
        self.wp_total_views.setFont(QFont("Arial", 24, QFont.Bold))
        wordpress_layout.addWidget(QLabel("Total Views:"), 2, 0)
        wordpress_layout.addWidget(self.wp_total_views, 2, 1)

        wordpress_group.setLayout(wordpress_layout)
        layout.addWidget(wordpress_group)

        # Refresh Button
        refresh_button = QPushButton("Refresh Statistics")
        refresh_button.clicked.connect(self.update_stats)
        layout.addWidget(refresh_button)

        self.setLayout(layout)

    def setup_timer(self):
        """Setup timer for periodic updates"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(30000)  # Update every 30 seconds

    def update_stats(self):
        """Update dashboard statistics"""
        try:
            # Update system status
            if self.parent.worker and self.parent.worker.isRunning():
                self.worker_status.setText("Worker: Running")
                self.worker_status.setStyleSheet("color: green;")
            else:
                self.worker_status.setText("Worker: Not Running")
                self.worker_status.setStyleSheet("color: gray;")

            if self.parent.api_server:
                self.server_status.setText("Web Server: Running")
                self.server_status.setStyleSheet("color: green;")
            else:
                self.server_status.setText("Web Server: Stopped")
                self.server_status.setStyleSheet("color: gray;")

            # Update content statistics
            with self.parent.db.get_session() as session:
                # Total posts
                total_posts = session.query(Pin).count()
                self.total_posts.setText(str(total_posts))

                # Posts today
                today = datetime.datetime.now().date()
                posts_today = session.query(Pin).filter(Pin.created_at >= today).count()
                self.posts_today.setText(str(posts_today))

                # Pending posts
                pending_posts = (
                    session.query(Pin).filter(Pin.status == "pending").count()
                )
                self.pending_posts.setText(str(pending_posts))

            # Update Pinterest statistics if connected
            if self.parent.config.get("pinterest", {}).get("access_token"):
                self.pinterest_group.setVisible(True)
                # Fetch Pinterest stats
                pinterest_stats = self.fetch_pinterest_stats()
                self.total_pins.setText(str(pinterest_stats.get("total_pins", 0)))
                self.pins_today.setText(str(pinterest_stats.get("pins_today", 0)))
                self.total_saves.setText(str(pinterest_stats.get("total_saves", 0)))
                self.total_clicks.setText(str(pinterest_stats.get("total_clicks", 0)))
            else:
                self.pinterest_group.setVisible(False)

            # Update WordPress statistics
            wordpress_stats = self.fetch_wordpress_stats()
            self.wp_total_posts.setText(str(wordpress_stats.get("total_posts", 0)))
            self.wp_posts_today.setText(str(wordpress_stats.get("posts_today", 0)))
            self.wp_total_views.setText(str(wordpress_stats.get("total_views", 0)))

        except Exception as e:
            logger.error(f"Error updating dashboard stats: {e}")

    def fetch_pinterest_stats(self):
        """Fetch Pinterest statistics"""
        try:
            # This would be implemented to fetch actual Pinterest stats
            # For now, return dummy data
            return {
                "total_pins": 100,
                "pins_today": 5,
                "total_saves": 500,
                "total_clicks": 1000,
            }
        except Exception as e:
            logger.error(f"Error fetching Pinterest stats: {e}")
            return {}

    def fetch_wordpress_stats(self):
        """Fetch WordPress statistics"""
        try:
            # This would be implemented to fetch actual WordPress stats
            # For now, return dummy data
            return {
                "total_posts": 50,
                "posts_today": 2,
                "total_views": 1000,
            }
        except Exception as e:
            logger.error(f"Error fetching WordPress stats: {e}")
            return {}
