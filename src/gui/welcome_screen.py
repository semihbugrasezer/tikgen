from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QFrame,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QFont, QColor, QPalette, QLinearGradient, QGradient
import os
import logging

logger = logging.getLogger(__name__)


class WelcomeScreen(QWidget):
    """Welcome screen with start button"""

    start_clicked = pyqtSignal()  # Signal emitted when start button is clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # Logo
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_pixmap = QPixmap(logo_path)
            logo_label.setPixmap(
                logo_pixmap.scaled(
                    200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)

        # Welcome text
        welcome_label = QLabel("Welcome to TikGen")
        welcome_label.setFont(QFont("Arial", 24, QFont.Bold))
        welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_label)

        # Description
        desc_label = QLabel(
            "Your AI-powered content creation and automation platform.\n"
            "Create, schedule, and publish content across multiple platforms."
        )
        desc_label.setFont(QFont("Arial", 12))
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Start button
        start_button = QPushButton("Get Started")
        start_button.setFont(QFont("Arial", 14, QFont.Bold))
        start_button.setMinimumSize(200, 50)
        start_button.clicked.connect(self.start_clicked.emit)
        layout.addWidget(start_button, alignment=Qt.AlignCenter)

        # Version and credits
        version_label = QLabel("Version 2.0.0")
        version_label.setFont(QFont("Arial", 10))
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        credits_label = QLabel("© 2025 TikGen. All rights reserved.")
        credits_label.setFont(QFont("Arial", 10))
        credits_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(credits_label)

        self.setLayout(layout)

    def animate_entrance(self, widget):
        """Add entrance animation to the container"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(1000)
        animation.setEasingCurve(QEasingCurve.OutBack)

        # Start position (slightly below and smaller)
        start_geometry = widget.geometry()
        start_geometry.setY(start_geometry.y() + 50)
        start_geometry.setHeight(start_geometry.height() * 0.9)

        # End position (normal size and position)
        end_geometry = widget.geometry()

        animation.setStartValue(start_geometry)
        animation.setEndValue(end_geometry)
        animation.start()
