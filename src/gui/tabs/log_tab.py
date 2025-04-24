from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
import logging

logger = logging.getLogger(__name__)


class LogTab(QWidget):
    """Log tab for viewing application logs"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()

        # Log view
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)

        # Buttons
        button_layout = QHBoxLayout()
        self.clear_btn = QPushButton("Clear Logs")
        self.clear_btn.clicked.connect(self.clear_logs)
        self.export_btn = QPushButton("Export Logs")
        self.export_btn.clicked.connect(self.export_logs)

        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addStretch()

        # Add widgets to layout
        layout.addWidget(self.log_view)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def add_log(self, message: str):
        """Add a log message to the view"""
        self.log_view.append(message)

    def clear_logs(self):
        """Clear all logs"""
        self.log_view.clear()

    def export_logs(self):
        """Export logs to a file"""
        try:
            from PyQt5.QtWidgets import QFileDialog

            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Logs", "", "Text Files (*.txt);;All Files (*)"
            )
            if filename:
                with open(filename, "w") as f:
                    f.write(self.log_view.toPlainText())
                logger.info(f"Logs exported to {filename}")
        except Exception as e:
            logger.error(f"Error exporting logs: {e}")
