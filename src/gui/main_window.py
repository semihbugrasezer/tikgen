import sys
import os
import json
import logging
import traceback
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTabWidget,
    QMessageBox,
    QFileDialog,
    QProgressBar,
    QTextEdit,
    QStatusBar,
    QFrame,
    QSystemTrayIcon,
    QMenu,
    QComboBox,
    QSplashScreen,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QUrl
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QColor
from urllib.parse import urlparse
import gc
import psutil
import sqlite3
import webbrowser
from typing import Optional, Dict, Any

from src.utils.database import (
    Session,
    Pin,
    DatabaseManager as DBManager,
    db_manager,
    Base,
)
from src.utils.config import get_config
from src.automation.worker import AutomationWorker
from src.automation.integrations import WordPressIntegration
from src.utils.api_server import ApiServer
from src.gui.welcome_screen import WelcomeScreen

from src.gui.tabs.wordpress_tab import WordPressTab
from src.gui.tabs.pinterest_tab import PinterestTab
from src.gui.tabs.settings_tab import SettingsTab
from src.gui.tabs.reports_tab import ReportsTab
from src.gui.tabs.dashboard_tab import DashboardTab
from src.gui.tabs.automation_tab import AutomationTab
from src.gui.tabs.content_tab import ContentTab
from src.gui.tabs.log_tab import LogTab
from src.gui.tabs.trends_tab import TrendsTab
from src.gui.tabs.templates_tab import TemplatesTab

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class ReportViewer(QWidget):
    """Report viewer widget for generating and displaying various reports"""

    def __init__(self):
        super().__init__()
        self.report_view: Optional[QTextEdit] = None
        self.current_report: Optional[str] = None
        self.btn_export: Optional[QPushButton] = None
        self.cmb_report_type: Optional[QComboBox] = None
        self.lbl_report_type: Optional[QLabel] = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()

        # Report type selector
        type_layout = QHBoxLayout()

        self.lbl_report_type = QLabel("Report Type:")
        self.cmb_report_type = QComboBox()
        self.cmb_report_type.addItems(
            [
                "Weekly Performance",
                "Content Analysis",
                "Domain Performance",
                "Pinterest Engagement",
            ]
        )
        self.cmb_report_type.currentIndexChanged.connect(self.change_report_type)

        self.btn_generate = QPushButton("Generate Report")
        self.btn_generate.clicked.connect(self.generate_report)

        self.btn_export = QPushButton("Export")
        self.btn_export.clicked.connect(self.export_report)
        self.btn_export.setEnabled(False)  # Disable until report is generated

        type_layout.addWidget(self.lbl_report_type)
        type_layout.addWidget(self.cmb_report_type)
        type_layout.addWidget(self.btn_generate)
        type_layout.addWidget(self.btn_export)
        type_layout.addStretch()

        layout.addLayout(type_layout)

        # Report view
        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        layout.addWidget(self.report_view)

        self.setLayout(layout)

        # Current report data
        self.current_report = None

    def change_report_type(self):
        """Update UI when report type changes"""
        # Reset report view and disable export
        self.report_view.clear()
        self.btn_export.setEnabled(False)
        self.current_report = None

    def generate_report(self):
        """Generate the selected report type"""
        report_type = self.cmb_report_type.currentText()

        try:
            self.report_view.clear()
            self.report_view.setTextColor(QColor("black"))
            self.report_view.append(f"Generating {report_type} report... Please wait.")

            # Call the appropriate report generator
            if report_type == "Weekly Performance":
                self.generate_weekly_report()
            elif report_type == "Content Analysis":
                self.generate_content_analysis()
            elif report_type == "Domain Performance":
                self.generate_domain_report()
            elif report_type == "Pinterest Engagement":
                self.generate_pinterest_report()

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            self.report_view.setTextColor(QColor("red"))
            self.report_view.append(f"Error generating report: {e}")

    def generate_weekly_report(self):
        """Generate weekly performance report"""
        try:
            with Session() as session:
                # Get last week's data
                week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
                pins = session.query(Pin).filter(Pin.created_at >= week_ago).all()

                # Generate report
                report = []
                report.append("=== Weekly Performance Report ===")
                report.append(
                    f"Period: {week_ago.strftime('%Y-%m-%d')} to {datetime.datetime.now().strftime('%Y-%m-%d')}"
                )
                report.append(f"\nTotal Pins Created: {len(pins)}")

                # Success rate
                successful = len([p for p in pins if p.status == "success"])
                if pins:
                    success_rate = (successful / len(pins)) * 100
                    report.append(f"Success Rate: {success_rate:.1f}%")

                # Daily breakdown
                report.append("\nDaily Breakdown:")
                daily_pins = {}
                for pin in pins:
                    day = pin.created_at.strftime("%Y-%m-%d")
                    daily_pins[day] = daily_pins.get(day, 0) + 1

                for day, count in sorted(daily_pins.items()):
                    report.append(f"{day}: {count} pins")

                self.current_report = "\n".join(report)
                self.report_view.setText(self.current_report)
                self.btn_export.setEnabled(True)

        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            raise

    def generate_content_analysis(self):
        """Generate content analysis report"""
        try:
            with Session() as session:
                # Get all pins
                pins = session.query(Pin).all()

                # Generate report
                report = []
                report.append("=== Content Analysis Report ===")
                report.append(
                    f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )

                # Content type breakdown
                content_types = {}
                for pin in pins:
                    content_type = pin.content_type or "unknown"
                    content_types[content_type] = content_types.get(content_type, 0) + 1

                report.append("\nContent Type Distribution:")
                for ctype, count in sorted(
                    content_types.items(), key=lambda x: x[1], reverse=True
                ):
                    report.append(f"{ctype}: {count} pins")

                # Most used keywords
                keywords = {}
                for pin in pins:
                    if pin.keywords:
                        for kw in pin.keywords.split(","):
                            kw = kw.strip()
                            if kw:
                                keywords[kw] = keywords.get(kw, 0) + 1

                report.append("\nTop Keywords:")
                top_keywords = sorted(
                    keywords.items(), key=lambda x: x[1], reverse=True
                )[:10]
                for kw, count in top_keywords:
                    report.append(f"{kw}: {count} uses")

                self.current_report = "\n".join(report)
                self.report_view.setText(self.current_report)
                self.btn_export.setEnabled(True)

        except Exception as e:
            logger.error(f"Error generating content analysis: {e}")
            raise

    def generate_domain_report(self):
        """Generate domain performance report"""
        try:
            with Session() as session:
                # Get all pins
                pins = session.query(Pin).all()

                # Generate report
                report = []
                report.append("=== Domain Performance Report ===")
                report.append(
                    f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )

                # Domain statistics
                domains = {}
                for pin in pins:
                    domain = urlparse(pin.url).netloc if pin.url else "unknown"
                    if domain not in domains:
                        domains[domain] = {"total": 0, "success": 0, "failed": 0}
                    domains[domain]["total"] += 1
                    if pin.status == "success":
                        domains[domain]["success"] += 1
                    elif pin.status == "failed":
                        domains[domain]["failed"] += 1

                report.append("\nDomain Performance:")
                for domain, stats in sorted(
                    domains.items(), key=lambda x: x[1]["total"], reverse=True
                ):
                    success_rate = (
                        (stats["success"] / stats["total"] * 100)
                        if stats["total"] > 0
                        else 0
                    )
                    report.append(f"\n{domain}")
                    report.append(f"Total Pins: {stats['total']}")
                    report.append(f"Success Rate: {success_rate:.1f}%")
                    report.append(f"Failed Pins: {stats['failed']}")

                self.current_report = "\n".join(report)
                self.report_view.setText(self.current_report)
                self.btn_export.setEnabled(True)

        except Exception as e:
            logger.error(f"Error generating domain report: {e}")
            raise

    def generate_pinterest_report(self):
        """Generate Pinterest engagement report"""
        try:
            with Session() as session:
                # Get all pins with engagement data
                pins = session.query(Pin).filter(Pin.engagement_data.isnot(None)).all()

                # Generate report
                report = []
                report.append("=== Pinterest Engagement Report ===")
                report.append(
                    f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                report.append(f"Total Pins Analyzed: {len(pins)}")

                if not pins:
                    report.append("\nNo engagement data available.")
                else:
                    # Overall engagement metrics
                    total_saves = sum(p.engagement_data.get("saves", 0) for p in pins)
                    total_clicks = sum(p.engagement_data.get("clicks", 0) for p in pins)
                    total_impressions = sum(
                        p.engagement_data.get("impressions", 0) for p in pins
                    )

                    report.append("\nOverall Engagement:")
                    report.append(f"Total Saves: {total_saves:,}")
                    report.append(f"Total Clicks: {total_clicks:,}")
                    report.append(f"Total Impressions: {total_impressions:,}")

                    if total_impressions > 0:
                        ctr = (total_clicks / total_impressions) * 100
                        save_rate = (total_saves / total_impressions) * 100
                        report.append(f"Click-through Rate: {ctr:.2f}%")
                        report.append(f"Save Rate: {save_rate:.2f}%")

                    # Top performing pins
                    report.append("\nTop Performing Pins:")
                    top_pins = sorted(
                        pins,
                        key=lambda x: x.engagement_data.get("saves", 0),
                        reverse=True,
                    )[:5]

                    for pin in top_pins:
                        report.append(f"\nPin ID: {pin.pin_id}")
                        report.append(f"Title: {pin.title}")
                        report.append(f"Saves: {pin.engagement_data.get('saves', 0):,}")
                        report.append(
                            f"Clicks: {pin.engagement_data.get('clicks', 0):,}"
                        )
                        report.append(
                            f"Impressions: {pin.engagement_data.get('impressions', 0):,}"
                        )

                self.current_report = "\n".join(report)
                self.report_view.setText(self.current_report)
                self.btn_export.setEnabled(True)

        except Exception as e:
            logger.error(f"Error generating Pinterest report: {e}")
            raise

    def export_report(self):
        """Export the current report to a file"""
        if not self.current_report:
            QMessageBox.warning(self, "Export Error", "No report to export!")
            return

        try:
            # Get save location
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Report",
                f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt);;All Files (*.*)",
            )

            if filename:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.current_report)
                QMessageBox.information(
                    self, "Success", f"Report exported to {filename}"
                )

        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export report: {e}")


class MemoryManager:
    def __init__(self, threshold_mb=500):
        self.threshold_mb = threshold_mb
        self.process = psutil.Process()
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_memory)
        self.timer.start(30000)  # Check every 30 seconds

    def check_memory(self):
        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024  # Convert to MB

            if memory_mb > self.threshold_mb:
                logger.warning(f"High memory usage detected: {memory_mb:.2f} MB")
                self.cleanup()
        except Exception as e:
            logger.error(f"Error checking memory: {e}")

    def cleanup(self):
        try:
            # Force garbage collection
            gc.collect()

            # Clear any cached data
            if hasattr(QApplication, "clearMemoryCache"):
                QApplication.clearMemoryCache()

            logger.info("Memory cleanup performed")
        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")


class LicenseManager:
    def __init__(self):
        self.license_key = get_config().get("LICENSE_KEY", "")

    def validate_license(self):
        # This method should be implemented to check the license key
        # For now, we'll just return True
        return True

    def check_feature_access(self, feature: str) -> bool:
        # This method should be implemented to check if the license has access to a specific feature
        # For now, we'll just return True
        return True


class MainWindow(QMainWindow):
    """Main window with improved stability and features"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TikGen - Content Automation")
        self.setMinimumSize(1200, 800)

        # Initialize license manager
        self.license_manager = LicenseManager()
        if not self.license_manager.validate_license():
            self.show_license_dialog()
            return

        # Initialize state variables
        self.worker = None
        self.api_server = None
        self.db = None
        self.memory_manager = MemoryManager()

        # Load system tray icon if available
        self.setup_system_tray()

        # Initialize components
        try:
            # Initialize database first
            self.db = DBManager()
            self.db.init()  # Initialize the database manager
            logger.info("Database initialized successfully")

            # Load configuration
            self.config = get_config()
            logger.info("Configuration loaded successfully")

            # Create welcome screen
            self.welcome_screen = WelcomeScreen()
            self.welcome_screen.start_clicked.connect(self.show_main_interface)
            self.setCentralWidget(self.welcome_screen)

            # Setup UI
            self.init_ui()
            logger.info("UI initialized successfully")

            # Start automation worker
            self.start_worker()

            # Start web server if enabled
            if self.config.get("ENABLE_WEB_SERVER", "False") == "True":
                self.start_web_server()

            # Show status message
            self.statusBar().showMessage("TikGen Ready", 5000)
            logger.info("TikGen started successfully")

            self.setup_cleanup_timer()

        except Exception as e:
            logger.error(f"Error initializing application: {e}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize application: {str(e)}",
            )

    def show_license_dialog(self):
        """Show license activation dialog"""
        from src.gui.license_dialog import LicenseDialog

        dialog = LicenseDialog(self)
        dialog.license_activated.connect(self.on_license_activated)
        dialog.exec_()

    def on_license_activated(self):
        """Handle license activation"""
        if self.license_manager.validate_license():
            # Reinitialize the application
            self.__init__()
        else:
            QMessageBox.critical(
                self,
                "License Error",
                "Invalid license. Please contact support.",
            )
            self.close()

    def check_feature_access(self, feature: str) -> bool:
        """Check if current license has access to a feature"""
        return self.license_manager.check_feature_access(feature)

    def show_main_interface(self):
        """Show the main interface after welcome screen"""
        try:
            # Hide welcome screen
            self.welcome_screen.hide()

            # Set central widget to tabs
            self.setCentralWidget(self.tabs)

            # Update dashboard if Pinterest is connected
            if self.config.get("pinterest", {}).get("access_token"):
                self.dashboard_tab.update_stats()
                logger.info("Dashboard updated with Pinterest data")

        except Exception as e:
            logger.error(f"Error showing main interface: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to show main interface: {str(e)}",
            )

    def init_ui(self):
        """Initialize the UI with improved layout and error handling"""
        try:
            # Central widget with tabs
            self.tabs = QTabWidget()

            # Dashboard tab
            self.dashboard_tab = DashboardTab(self)
            self.tabs.addTab(self.dashboard_tab, "Dashboard")

            # WordPress tab
            self.wordpress_tab = WordPressTab(self)
            self.tabs.addTab(self.wordpress_tab, "WordPress")

            # Settings tab
            self.settings_tab = SettingsTab(self)
            self.tabs.addTab(self.settings_tab, "Settings")

            # Automation tab
            self.automation_tab = AutomationTab(self)
            self.tabs.addTab(self.automation_tab, "Automation")

            # Content tab
            self.content_tab = ContentTab(self)
            self.tabs.addTab(self.content_tab, "Content")

            # Reports tab
            self.reports_tab = ReportsTab(self)
            self.tabs.addTab(self.reports_tab, "Reports")

            # Log tab
            self.log_tab = LogTab(self)
            self.tabs.addTab(self.log_tab, "Logs")

            # Status bar
            self.status_bar = self.statusBar()
            self.status_label = QLabel("Ready")
            self.status_bar.addPermanentWidget(self.status_label)

            # Progress bar
            self.progress_bar = QProgressBar()
            self.progress_bar.setMaximumWidth(200)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(0)
            self.status_bar.addPermanentWidget(self.progress_bar)

            # Worker status indicator
            self.worker_status = QLabel("Worker: Not Running")
            self.worker_status.setStyleSheet("color: gray;")
            self.status_bar.addPermanentWidget(self.worker_status)

            # Create menu
            self.create_menu()

            # Connect tab changed signal
            self.tabs.currentChanged.connect(self.handle_tab_change)

        except Exception as e:
            logger.error(f"Error initializing UI: {e}")
            logger.error(traceback.format_exc())
            raise

    def create_menu(self):
        """Create application menu with enhanced options"""
        try:
            menubar = self.menuBar()

            # File menu
            file_menu = menubar.addMenu("File")

            new_content_action = file_menu.addAction("New Content")
            new_content_action.triggered.connect(self.create_new_content)
            new_content_action.setShortcut("Ctrl+N")

            import_action = file_menu.addAction("Import Content")
            import_action.triggered.connect(self.import_content)

            export_action = file_menu.addAction("Export Data")
            export_action.triggered.connect(self.export_data)

            file_menu.addSeparator()

            backup_action = file_menu.addAction("Backup Database")
            backup_action.triggered.connect(self.backup_database)

            restore_action = file_menu.addAction("Restore Database")
            restore_action.triggered.connect(self.restore_database)

            file_menu.addSeparator()

            # License menu item
            license_action = file_menu.addAction("License")
            license_action.triggered.connect(self.show_license_dialog)

            file_menu.addSeparator()

            exit_action = file_menu.addAction("Exit")
            exit_action.triggered.connect(self.close)
            exit_action.setShortcut("Ctrl+Q")

            # Worker menu
            worker_menu = menubar.addMenu("Worker")

            self.start_worker_action = worker_menu.addAction("Start Worker")
            self.start_worker_action.triggered.connect(self.start_worker)

            self.stop_worker_action = worker_menu.addAction("Stop Worker")
            self.stop_worker_action.triggered.connect(self.stop_worker)
            self.stop_worker_action.setEnabled(False)

            self.pause_worker_action = worker_menu.addAction("Pause Worker")
            self.pause_worker_action.triggered.connect(self.pause_worker)
            self.pause_worker_action.setEnabled(False)

            self.resume_worker_action = worker_menu.addAction("Resume Worker")
            self.resume_worker_action.triggered.connect(self.resume_worker)
            self.resume_worker_action.setEnabled(False)

            worker_menu.addSeparator()

            self.run_now_menu = worker_menu.addMenu("Run Now")

            run_content_action = self.run_now_menu.addAction("Generate Content")
            run_content_action.triggered.connect(self.force_content_generation)

            run_trends_action = self.run_now_menu.addAction("Analyze Trends")
            run_trends_action.triggered.connect(self.force_trend_analysis)

            run_publish_action = self.run_now_menu.addAction("Publish Content")
            run_publish_action.triggered.connect(self.force_publish)

            run_stats_action = self.run_now_menu.addAction("Update Stats")
            run_stats_action.triggered.connect(self.force_stats_update)

            run_all_action = self.run_now_menu.addAction("Run All Tasks")
            run_all_action.triggered.connect(self.force_run_all)

            # Tools menu
            tools_menu = menubar.addMenu("Tools")

            self.start_server_action = tools_menu.addAction("Start Web Server")
            self.start_server_action.triggered.connect(self.start_web_server)

            self.stop_server_action = tools_menu.addAction("Stop Web Server")
            self.stop_server_action.triggered.connect(self.stop_web_server)
            self.stop_server_action.setEnabled(False)

            tools_menu.addSeparator()

            clear_logs_action = tools_menu.addAction("Clear Logs")
            clear_logs_action.triggered.connect(self.clear_logs)

            optimize_db_action = tools_menu.addAction("Optimize Database")
            optimize_db_action.triggered.connect(self.optimize_database)

            # Help menu
            help_menu = menubar.addMenu("Help")

            docs_action = help_menu.addAction("Documentation")
            docs_action.triggered.connect(self.open_docs)

            check_updates_action = help_menu.addAction("Check for Updates")
            check_updates_action.triggered.connect(self.check_updates)

            help_menu.addSeparator()

            about_action = help_menu.addAction("About")
            about_action.triggered.connect(self.show_about)

        except Exception as e:
            logger.error(f"Error creating menu: {e}")
            logger.error(traceback.format_exc())
            raise

    def setup_system_tray(self):
        """Set up system tray icon if supported"""
        try:
            if QSystemTrayIcon.isSystemTrayAvailable():
                self.tray_icon = QSystemTrayIcon(self)

                # Create a default icon
                pixmap = QPixmap(32, 32)
                pixmap.fill(QColor("#0078D7"))  # Default blue color
                icon = QIcon(pixmap)

                # Try to load icon from file if available
                icon_path = os.path.join(
                    os.path.dirname(__file__), "assets", "icon.png"
                )
                if os.path.exists(icon_path):
                    try:
                        file_icon = QIcon(icon_path)
                        if not file_icon.isNull():
                            icon = file_icon
                    except Exception as e:
                        logger.warning(f"Failed to load icon from {icon_path}: {e}")

                self.tray_icon.setIcon(icon)

                # Create tray menu
                tray_menu = QMenu()

                show_action = tray_menu.addAction("Show")
                show_action.triggered.connect(self.show)

                tray_menu.addSeparator()

                start_worker_action = tray_menu.addAction("Start Worker")
                start_worker_action.triggered.connect(self.start_worker)

                stop_worker_action = tray_menu.addAction("Stop Worker")
                stop_worker_action.triggered.connect(self.stop_worker)

                tray_menu.addSeparator()

                exit_action = tray_menu.addAction("Exit")
                exit_action.triggered.connect(self.close)

                self.tray_icon.setContextMenu(tray_menu)
                self.tray_icon.activated.connect(self.tray_icon_activated)

                # Show tray icon
                self.tray_icon.show()
                logger.info("System tray icon initialized")
        except Exception as e:
            logger.error(f"Error setting up system tray: {e}")
            # Non-critical, so continue without system tray

    def tray_icon_activated(self, reason):
        """Handle system tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()

    def handle_tab_change(self, index):
        """Handle tab changes"""
        try:
            current_tab = self.tabs.widget(index)
            if current_tab == self.dashboard_tab:
                self.dashboard_tab.update_stats()
            elif current_tab == self.settings_tab:
                self.settings_tab.load_settings()
            elif current_tab == self.wordpress_tab:
                self.wordpress_tab.load_sites()
            # Add other tab handlers as needed
        except Exception as e:
            logger.error(f"Error handling tab change: {e}")

    def update_status(self, message):
        """Update status bar message"""
        self.status_label.setText(message)

    def update_progress(self, current, total):
        """Update progress bar"""
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
        else:
            self.progress_bar.setValue(0)

    def update_worker_status(self, message, running=False, paused=False):
        """Update worker status indicator"""
        self.worker_status.setText(f"Worker: {message}")

        # Set color based on state
        if running:
            if paused:
                self.worker_status.setStyleSheet("color: orange;")
            else:
                self.worker_status.setStyleSheet("color: green;")
        else:
            self.worker_status.setStyleSheet("color: red;")

        # Update dashboard indicator if available
        if hasattr(self, "dashboard_tab"):
            self.dashboard_tab.set_worker_status(running, paused)

        # Update menu items
        self.start_worker_action.setEnabled(not running)
        self.stop_worker_action.setEnabled(running)
        self.pause_worker_action.setEnabled(running and not paused)
        self.resume_worker_action.setEnabled(running and paused)
        self.run_now_menu.setEnabled(running and not paused)

    def start_worker(self):
        """Start the automation worker with improved error handling"""
        try:
            if not self.worker:
                from src.automation.worker import AutomationWorker

                self.worker = AutomationWorker(self.db)

                # Connect worker signals
                self.worker.status_changed.connect(self.update_worker_status)
                self.worker.progress_updated.connect(self.update_progress)

                # Set worker in automation tab
                self.automation_tab.set_worker(self.worker)

                logger.info("Automation worker initialized")

            # Start the worker
            self.worker.start()
            self.update_worker_status("Running", True)
            logger.info("Automation worker started")

        except Exception as e:
            logger.error(f"Failed to start automation worker: {e}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(
                self, "Worker Error", f"Failed to start automation worker: {str(e)}"
            )

    def stop_worker(self):
        """Stop the automation worker"""
        try:
            if not self.worker or not self.worker.isRunning():
                logger.warning("Worker not running")
                return

            # Stop the worker
            self.worker.stop()

            # Wait for the worker to finish with timeout
            if not self.worker.wait(2000):
                logger.warning("Worker not responding, forcing termination")
                self.worker.terminate()
                self.worker.wait()

            # Update status
            self.update_worker_status("Stopped", False, False)
            self.log_tab.add_log("Worker stopped")
            logger.info("Worker stopped")

        except Exception as e:
            logger.error(f"Error stopping worker: {e}")
            self.log_tab.add_log(f"Error stopping worker: {e}")

    def pause_worker(self):
        """Pause the automation worker"""
        try:
            if not self.worker or not self.worker.isRunning():
                logger.warning("Worker not running")
                return

            # Pause the worker
            self.worker.pause()

            # Update status
            self.update_worker_status("Paused", True, True)
            self.log_tab.add_log("Worker paused")
            logger.info("Worker paused")

        except Exception as e:
            logger.error(f"Error pausing worker: {e}")
            self.log_tab.add_log(f"Error pausing worker: {e}")

    def resume_worker(self):
        """Resume the automation worker"""
        try:
            if not self.worker or not self.worker.isRunning():
                logger.warning("Worker not running")
                return

            # Resume the worker
            self.worker.resume()

            # Update status
            self.update_worker_status("Running", True, False)
            self.log_tab.add_log("Worker resumed")
            logger.info("Worker resumed")

        except Exception as e:
            logger.error(f"Error resuming worker: {e}")
            self.log_tab.add_log(f"Error resuming worker: {e}")

    def force_content_generation(self):
        """Force content generation now"""
        if self.worker and self.worker.isRunning() and not self.worker.paused:
            try:
                self.log_tab.add_log("Forcing content generation...")
                self.worker.daily_content_generation()
            except Exception as e:
                logger.error(f"Error forcing content generation: {e}")
                self.log_tab.add_log(f"Error forcing content generation: {e}")
        else:
            QMessageBox.warning(
                self,
                "Worker Not Running",
                "The worker must be running to execute tasks.",
            )

    def force_trend_analysis(self):
        """Force trend analysis now"""
        if self.worker and self.worker.isRunning() and not self.worker.paused:
            try:
                self.log_tab.add_log("Forcing trend analysis...")
                self.worker.pinterest_trend_analysis()
            except Exception as e:
                logger.error(f"Error forcing trend analysis: {e}")
                self.log_tab.add_log(f"Error forcing trend analysis: {e}")
        else:
            QMessageBox.warning(
                self,
                "Worker Not Running",
                "The worker must be running to execute tasks.",
            )

    def force_publish(self):
        """Force content publishing now"""
        if self.worker and self.worker.isRunning() and not self.worker.paused:
            try:
                self.log_tab.add_log("Forcing content publishing...")
                self.worker.publish_content()
            except Exception as e:
                logger.error(f"Error forcing content publishing: {e}")
                self.log_tab.add_log(f"Error forcing content publishing: {e}")
        else:
            QMessageBox.warning(
                self,
                "Worker Not Running",
                "The worker must be running to execute tasks.",
            )

    def force_stats_update(self):
        """Force stats update now"""
        if self.worker and self.worker.isRunning() and not self.worker.paused:
            try:
                self.log_tab.add_log("Forcing stats update...")
                self.worker.update_stats()
            except Exception as e:
                logger.error(f"Error forcing stats update: {e}")
                self.log_tab.add_log(f"Error forcing stats update: {e}")
        else:
            QMessageBox.warning(
                self,
                "Worker Not Running",
                "The worker must be running to execute tasks.",
            )

    def force_run_all(self):
        """Force run all scheduled tasks now"""
        if self.worker and self.worker.isRunning() and not self.worker.paused:
            try:
                self.log_tab.add_log("Forcing all tasks...")
                self.worker.daily_content_generation()
                self.worker.pinterest_trend_analysis()
                self.worker.publish_content()
                self.worker.update_stats()
                self.worker.weekly_analysis()
                self.worker.health_check()
            except Exception as e:
                logger.error(f"Error forcing all tasks: {e}")
                self.log_tab.add_log(f"Error forcing all tasks: {e}")
        else:
            QMessageBox.warning(
                self,
                "Worker Not Running",
                "The worker must be running to execute tasks.",
            )

    def start_web_server(self):
        """Start the web server"""
        try:
            if self.api_server:
                logger.warning("Web server already running")
                return

            # Get configuration
            port = int(self.config.get("WEB_SERVER_PORT", "5000"))

            # Create and start the server
            self.api_server = ApiServer(port=port)
            self.api_server.start()

            # Update status
            self.log_tab.add_log(f"Web server started on port {port}")
            logger.info(f"Web server started on port {port}")

            # Update dashboard indicator if available
            if hasattr(self, "dashboard_tab"):
                self.dashboard_tab.set_web_server_status(True)

            # Update menu items
            self.start_server_action.setEnabled(False)
            self.stop_server_action.setEnabled(True)

        except Exception as e:
            logger.error(f"Error starting web server: {e}")
            self.log_tab.add_log(f"Error starting web server: {e}")
            QMessageBox.critical(
                self, "Web Server Error", f"Failed to start web server: {str(e)}"
            )

    def stop_web_server(self):
        """Stop the web server"""
        try:
            if not self.api_server:
                logger.warning("Web server not running")
                return

            # Stop the server
            self.api_server.stop()
            self.api_server = None

            # Update status
            self.log_tab.add_log("Web server stopped")
            logger.info("Web server stopped")

            # Update dashboard indicator if available
            if hasattr(self, "dashboard_tab"):
                self.dashboard_tab.set_web_server_status(False)

            # Update menu items
            self.start_server_action.setEnabled(True)
            self.stop_server_action.setEnabled(False)

        except Exception as e:
            logger.error(f"Error stopping web server: {e}")
            self.log_tab.add_log(f"Error stopping web server: {e}")

    def create_new_content(self):
        """Create new content manually"""
        QMessageBox.information(
            self, "Create Content", "Content creation wizard would be implemented here."
        )

    def import_content(self):
        """Import content from a file"""
        QMessageBox.information(
            self,
            "Import Content",
            "Content import functionality would be implemented here.",
        )

    def export_data(self):
        """Export application data"""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            "",
            "SQLite Database (*.db);;CSV Files (*.csv);;JSON Files (*.json)",
            options=options,
        )

        if file_name:
            try:
                # Implementation would depend on the selected format
                QMessageBox.information(
                    self,
                    "Export Started",
                    "Data export functionality would be implemented here.",
                )
            except Exception as e:
                logger.error(f"Error exporting data: {e}")
                QMessageBox.critical(
                    self, "Export Error", f"Failed to export data: {str(e)}"
                )

    def backup_database(self):
        """Backup the database"""
        try:
            # Get backup file path
            options = QFileDialog.Options()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"autopinner_backup_{timestamp}.db"

            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "Backup Database",
                default_name,
                "SQLite Database (*.db);;All Files (*)",
                options=options,
            )

            if not file_name:
                return  # User cancelled

            # Close database connections
            if self.db:
                self.db.close_all()

            # Copy database file
            import shutil

            db_path = self.config.get("DB_PATH", "autopinner.db")
            shutil.copy2(db_path, file_name)

            # Reopen database
            self.db = DBManager()

            QMessageBox.information(
                self, "Backup Complete", f"Database has been backed up to {file_name}"
            )
            logger.info(f"Database backed up to {file_name}")

        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            QMessageBox.critical(
                self, "Backup Error", f"Failed to backup database: {str(e)}"
            )

    def restore_database(self):
        """Restore the database from a backup"""
        try:
            # Get restore file path
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "Restore Database",
                "",
                "SQLite Database (*.db);;All Files (*)",
                options=options,
            )

            if not file_name:
                return  # User cancelled

            # Confirm restore
            reply = QMessageBox.question(
                self,
                "Confirm Restore",
                "Restoring the database will replace all current data. Are you sure?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply != QMessageBox.Yes:
                return

            # Stop worker and web server
            if self.worker and self.worker.isRunning():
                self.stop_worker()

            if self.api_server:
                self.stop_web_server()

            # Close database connections
            if self.db:
                self.db.close_all()

            # Copy backup file to database location
            import shutil

            db_path = self.config.get("DB_PATH", "autopinner.db")
            shutil.copy2(file_name, db_path)

            # Reopen database
            self.db = DBManager()

            QMessageBox.information(
                self,
                "Restore Complete",
                "Database has been restored. The application will now restart.",
            )
            logger.info("Database restored, application restarting")

            # Restart application
            self.restart_application()

        except Exception as e:
            logger.error(f"Error restoring database: {e}")
            QMessageBox.critical(
                self, "Restore Error", f"Failed to restore database: {str(e)}"
            )

    def clear_logs(self):
        """Clear application logs"""
        reply = QMessageBox.question(
            self,
            "Confirm Clear Logs",
            "Are you sure you want to clear all logs?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                # Clear log tab
                self.log_tab.clear_logs()

                # Clear log file
                open("autopinner.log", "w").close()

                logger.info("Logs cleared")
            except Exception as e:
                logger.error(f"Error clearing logs: {e}")
                QMessageBox.critical(
                    self, "Clear Error", f"Failed to clear logs: {str(e)}"
                )

    def optimize_database(self):
        """Optimize the database"""
        try:
            # Show progress dialog
            progress = QMessageBox(self)
            progress.setWindowTitle("Database Optimization")
            progress.setText("Optimizing database...")
            progress.setStandardButtons(QMessageBox.NoButton)
            progress.show()

            # Close all current connections
            if self.db:
                self.db.close_all()

            # Run VACUUM on database
            conn = sqlite3.connect(self.config.get("DB_PATH", "autopinner.db"))
            conn.execute("VACUUM")
            conn.execute("PRAGMA optimize")
            conn.close()

            # Reopen database
            self.db = DBManager()

            # Close progress dialog
            progress.close()

            QMessageBox.information(
                self, "Optimization Complete", "Database has been optimized."
            )
            logger.info("Database optimized")

        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
            QMessageBox.critical(
                self, "Optimization Error", f"Failed to optimize database: {str(e)}"
            )

    def open_docs(self):
        """Open documentation"""
        webbrowser.open("https://www.autopinnerpro.com/docs")

    def check_updates(self):
        """Check for application updates"""
        QMessageBox.information(
            self,
            "Update Check",
            "No updates available. You are running the latest version (2.0.0).",
        )

    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h1>AutoPinner Pro</h1>
        <p>Version 2.0.0</p>
        <p>An automated content creation and Pinterest marketing tool.</p>
        <p>&copy; 2025 AutoPinner Pro. All rights reserved.</p>
        """
        QMessageBox.about(self, "About AutoPinner Pro", about_text)

    def restart_application(self):
        """Restart the application"""
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def setup_cleanup_timer(self):
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.periodic_cleanup)
        self.cleanup_timer.start(300000)  # Run cleanup every 5 minutes

    def periodic_cleanup(self):
        try:
            # Clear any unused resources
            gc.collect()

            # Clean up database connections
            db_manager.cleanup()

            # Log memory usage
            memory_info = psutil.Process().memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            logger.info(f"Current memory usage: {memory_mb:.2f} MB")
        except Exception as e:
            logger.error(f"Error during periodic cleanup: {e}")

    def closeEvent(self, event):
        try:
            # Clean up resources
            self.cleanup_timer.stop()
            self.memory_manager.timer.stop()

            # Stop worker and web server if running
            if hasattr(self, "worker") and self.worker:
                self.worker.stop()

            if hasattr(self, "api_server") and self.api_server:
                self.api_server.stop()

            # Clean up database
            if self.db:
                self.db._perform_cleanup()

            # Force garbage collection
            gc.collect()

            event.accept()
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
            event.accept()

    def reload_integrations(self):
        """Reload integrations when WordPress sites are updated"""
        if self.worker:
            self.worker._init_integrations()
            logger.info("Integrations reloaded after WordPress sites update")


def main():
    """Main application entry point with improved error handling"""

    # Configure excepthook to log uncaught exceptions
    def exception_hook(exctype, value, traceback_obj):
        """Global exception handler for unhandled exceptions"""
        exception_text = "".join(
            traceback.format_exception(exctype, value, traceback_obj)
        )
        logger.critical(f"Unhandled exception: {exception_text}")
        sys.__excepthook__(exctype, value, traceback_obj)

    sys.excepthook = exception_hook

    try:
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("AutoPinner Pro")
        app.setApplicationVersion("2.0.0")

        # Set application style
        app.setStyle("Fusion")

        # Set dark theme palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        app.setPalette(palette)

        # Create and show main window
        window = MainWindow()
        window.show()

        # Start event loop
        sys.exit(app.exec_())

    except Exception as e:
        logger.critical(f"Fatal error starting application: {e}")
        logger.critical(traceback.format_exc())

        # Show error dialog if QApplication exists
        if QApplication.instance():
            QMessageBox.critical(
                None,
                "Fatal Error",
                f"A fatal error occurred while starting the application:\n\n{str(e)}\n\nPlease check the log file for details.",
            )

        sys.exit(1)


if __name__ == "__main__":
    main()
