from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QColor, QPalette


class WelcomeScreen(QWidget):
    """Welcome screen with application information"""

    start_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize the welcome screen UI"""
        # Set background color
        self.setStyleSheet(
            """
            QWidget {
                background-color: #f5f5f5;
            }
        """
        )

        # Main layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # Container frame
        container = QFrame()
        container.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
            }
        """
        )
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)

        # Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap("assets/logo.png")
        if not logo_pixmap.isNull():
            logo_label.setPixmap(
                logo_pixmap.scaled(
                    200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
        logo_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(logo_label)

        # Welcome text
        welcome_label = QLabel("Welcome to TikGen")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet(
            """
            font-size: 36px;
            font-weight: bold;
            color: #2196F3;
            margin: 20px 0;
        """
        )
        container_layout.addWidget(welcome_label)

        # Description
        desc_label = QLabel(
            "Your all-in-one solution for automated content generation\n"
            "and social media management"
        )
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet(
            """
            font-size: 18px;
            color: #666666;
            margin: 10px 0;
            line-height: 1.5;
        """
        )
        container_layout.addWidget(desc_label)

        # Start button
        start_button = QPushButton("Start")
        start_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 15px 40px;
                font-size: 20px;
                border-radius: 5px;
                margin: 20px 0;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """
        )
        start_button.clicked.connect(self.start_clicked.emit)
        container_layout.addWidget(start_button, alignment=Qt.AlignCenter)

        # Version and credits
        info_layout = QHBoxLayout()

        version_label = QLabel("Version 1.0.0")
        version_label.setStyleSheet(
            """
            color: #666666;
            font-size: 14px;
        """
        )
        info_layout.addWidget(version_label)

        info_layout.addStretch()

        credits_label = QLabel("Created by Semih Bugra Sezer")
        credits_label.setStyleSheet(
            """
            color: #666666;
            font-size: 14px;
        """
        )
        info_layout.addWidget(credits_label)

        container_layout.addLayout(info_layout)

        # Add container to main layout
        layout.addWidget(container)
        self.setLayout(layout)
