from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QComboBox,
    QGroupBox,
    QHeaderView,
)
from PyQt5.QtCore import Qt, pyqtSignal
import json
import os
import logging
import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ReportsTab(QWidget):
    """Tab for viewing application reports"""

    def __init__(self, parent=None):
        """Initialize the reports tab"""
        super().__init__(parent)
        self.parent_window = parent
        self.reports = []
        self.current_page = 0
        self.page_size = 10  # Number of reports to show per page
        self.init_ui()
        self.load_reports()

    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout()

        # Report Type Selection
        type_group = QGroupBox("Report Type")
        type_layout = QHBoxLayout()

        self.report_type = QComboBox()
        self.report_type.addItems(
            [
                "Content Performance",
                "WordPress Stats",
                "Pinterest Stats",
                "Automation Status",
            ]
        )
        self.report_type.currentTextChanged.connect(self.update_report)
        type_layout.addWidget(self.report_type)

        # Date Range Selection
        self.date_range = QComboBox()
        self.date_range.addItems(
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom Range"]
        )
        self.date_range.currentTextChanged.connect(self.update_report)
        type_layout.addWidget(self.date_range)

        # Generate Report Button
        generate_button = QPushButton("Generate Report")
        generate_button.clicked.connect(self.generate_report)
        type_layout.addWidget(generate_button)

        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Report Table
        table_group = QGroupBox("Report Results")
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

        self.report_table = QTableWidget()
        self.report_table.setColumnCount(5)
        self.report_table.setHorizontalHeaderLabels(
            ["Date", "Type", "Status", "Details", "Actions"]
        )
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_layout.addWidget(self.report_table)

        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        self.setLayout(layout)

    def load_reports(self):
        """Load reports from config"""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    self.reports = config.get("reports", [])
                    self.update_table()
        except Exception as e:
            logger.error(f"Error loading reports: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load reports: {str(e)}\n\n"
                "Please check the logs for more details.",
            )

    def save_reports(self):
        """Save reports to config"""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)

                config["reports"] = self.reports

                with open(config_path, "w") as f:
                    json.dump(config, f, indent=4)

        except Exception as e:
            logger.error(f"Error saving reports: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save reports: {str(e)}\n\n"
                "Please check the logs for more details.",
            )

    def update_table(self):
        """Update the reports table with pagination"""
        if not self.reports:
            self.report_table.setRowCount(0)
            return

        # Calculate pagination
        total_pages = (len(self.reports) + self.page_size - 1) // self.page_size
        self.current_page = min(self.current_page, total_pages - 1)

        # Update pagination controls
        self.page_label.setText(f"Page {self.current_page + 1} of {total_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)

        # Get current page data
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.reports))
        current_reports = self.reports[start_idx:end_idx]

        # Update table
        self.report_table.setRowCount(len(current_reports))
        for i, report in enumerate(current_reports):
            # Date
            date_item = QTableWidgetItem(report.get("date", ""))
            self.report_table.setItem(i, 0, date_item)

            # Type
            type_item = QTableWidgetItem(report.get("type", ""))
            self.report_table.setItem(i, 1, type_item)

            # Status
            status_item = QTableWidgetItem(report.get("status", ""))
            status_item.setForeground(
                Qt.green if report.get("status") == "Success" else Qt.red
            )
            self.report_table.setItem(i, 2, status_item)

            # Details
            details_item = QTableWidgetItem(report.get("details", ""))
            self.report_table.setItem(i, 3, details_item)

            # View button
            view_btn = QPushButton("View")
            view_btn.clicked.connect(
                lambda checked, row=start_idx + i: self.view_report(row)
            )
            self.report_table.setCellWidget(i, 4, view_btn)

    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_table()

    def next_page(self):
        """Go to next page"""
        if (self.current_page + 1) * self.page_size < len(self.reports):
            self.current_page += 1
            self.update_table()

    def generate_report(self):
        """Generate a new report"""
        report_type = self.report_type.currentText()
        date_range = self.date_range.currentText()

        # Show progress dialog
        progress = QMessageBox(self)
        progress.setWindowTitle("Generating Report")
        progress.setText("Generating report...")
        progress.setStandardButtons(QMessageBox.NoButton)
        progress.show()

        try:
            # Generate report data
            report_data = {
                "date": datetime.datetime.now().isoformat(),
                "type": report_type,
                "status": "Success",
                "details": f"Report generated for {date_range}",
            }

            # Add to reports list
            self.reports.append(report_data)
            self.save_reports()
            self.update_table()

            progress.close()
            QMessageBox.information(self, "Success", "Report generated successfully!")

        except Exception as e:
            progress.close()
            logger.error(f"Error generating report: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate report: {str(e)}\n\n"
                "Please check the logs for more details.",
            )

    def view_report(self, row):
        """View a specific report"""
        if row < 0 or row >= len(self.reports):
            return

        report = self.reports[row]

        # Show report details
        QMessageBox.information(
            self,
            f"Report Details - {report['type']}",
            f"Date: {report['date']}\n"
            f"Type: {report['type']}\n"
            f"Status: {report['status']}\n"
            f"Details: {report['details']}",
        )

    def update_report(self):
        """Update the report based on selected type and date range"""
        # Implementation will be added later
        pass
