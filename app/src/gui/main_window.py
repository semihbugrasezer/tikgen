from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QMessageBox,
    QApplication,
    QSplashScreen,
    QFileDialog,
    QProgressBar,
    QTextEdit,
    QStatusBar,
    QFrame,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QColor
import sys
import os
import json
import logging
from datetime import datetime
from src.automation.worker import AutomationWorker
from src.automation.integrations import WordPressIntegration
from src.gui.tabs.wordpress_tab import WordPressTab
from src.gui.tabs.pinterest_tab import PinterestTab
from src.gui.tabs.settings_tab import SettingsTab
from src.gui.tabs.reports_tab import ReportsTab
from src.utils.database import db_manager
from src.gui.welcome_screen import WelcomeScreen

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window with improved styling"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TikGen - Content Automation")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: #ffffff;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom-color: #ffffff;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QLineEdit, QTextEdit, QComboBox {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                margin-top: 16px;
                font-weight: bold;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 4px;
            }
            QTableWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: 1px solid #cccccc;
                font-weight: bold;
            }
            QStatusBar {
                background-color: #f5f5f5;
                color: #333333;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
                background-color: #f5f5f5;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 4px;
            }
        """
        )

        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Show welcome screen first
        self.welcome_screen = WelcomeScreen(self)
        self.welcome_screen.start_clicked.connect(self.show_main_window)
        self.setCentralWidget(self.welcome_screen)

        # Initialize worker
        self.init_worker()

    def show_main_window(self):
        """Show the main application window"""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Create header
        header_layout = QHBoxLayout()
        title_label = QLabel("TikGen - Content Automation")
        title_label.setStyleSheet(
            """
            font-size: 24px;
            font-weight: bold;
            color: #2196F3;
            margin-bottom: 16px;
        """
        )
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setMovable(False)
        main_layout.addWidget(self.tab_widget)

        # Add tabs
        self.wordpress_tab = WordPressTab(self)
        self.pinterest_tab = PinterestTab(self)
        self.settings_tab = SettingsTab(self)
        self.reports_tab = ReportsTab(self)

        self.tab_widget.addTab(self.wordpress_tab, "WordPress")
        self.tab_widget.addTab(self.pinterest_tab, "Pinterest")
        self.tab_widget.addTab(self.settings_tab, "Settings")
        self.tab_widget.addTab(self.reports_tab, "Reports")

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def init_worker(self):
        """Initialize the automation worker"""
        try:
            self.worker = AutomationWorker(db_manager)
            self.worker.status_changed.connect(self.update_status)
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.error_occurred.connect(self.show_error)
            self.worker.start()
        except Exception as e:
            logger.error(f"Error initializing worker: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to initialize worker: {str(e)}"
            )

    def update_status(self, message: str, running: bool, paused: bool):
        """Update status bar with current state"""
        status_text = f"{message} {'(Paused)' if paused else ''}"
        self.status_bar.showMessage(status_text)
        self.progress_bar.setVisible(running)

    def update_progress(self, current: int, total: int):
        """Update progress bar"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)

    def show_error(self, message: str):
        """Show error message"""
        QMessageBox.critical(self, "Error", message)

    def closeEvent(self, event):
        """Handle window close event"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "The automation is still running. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.worker.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    # Create and show splash screen
    splash_pixmap = QPixmap("assets/splash.png")
    if not splash_pixmap.isNull():
        splash = QSplashScreen(splash_pixmap)
        splash.show()
        app.processEvents()

        # Show splash for 2 seconds
        QTimer.singleShot(2000, splash.close)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
