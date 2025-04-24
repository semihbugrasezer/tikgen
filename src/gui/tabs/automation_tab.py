from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QTextEdit,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QScrollArea,
    QFrame,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QFormLayout,
    QCalendarWidget,
    QTimeEdit,
    QDialogButtonBox,
    QSplitter,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class TaskConfigDialog(QDialog):
    """Dialog for configuring task settings"""

    def __init__(self, task_name, task_config, parent=None):
        super().__init__(parent)
        self.task_name = task_name
        self.task_config = task_config
        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle(f"Configure {self.task_name}")
        layout = QVBoxLayout()

        # Schedule configuration
        schedule_group = QGroupBox("Schedule")
        schedule_layout = QVBoxLayout()

        # Days of week
        days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        self.day_checkboxes = {}
        for day in days:
            cb = QCheckBox(day)
            cb.setChecked(self.task_config.schedule.get(day.lower(), True))
            self.day_checkboxes[day.lower()] = cb
            schedule_layout.addWidget(cb)

        schedule_group.setLayout(schedule_layout)

        # Task configuration
        config_group = QGroupBox("Configuration")
        config_layout = QFormLayout()

        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 10)
        self.retry_spin.setValue(self.task_config.retry_count)
        config_layout.addRow("Retry Count:", self.retry_spin)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(30, 3600)
        self.timeout_spin.setValue(self.task_config.timeout)
        config_layout.addRow("Timeout (seconds):", self.timeout_spin)

        config_group.setLayout(config_layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(schedule_group)
        layout.addWidget(config_group)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_config(self):
        """Get the updated configuration"""
        return {
            "schedule": {
                day: cb.isChecked() for day, cb in self.day_checkboxes.items()
            },
            "retry_count": self.retry_spin.value(),
            "timeout": self.timeout_spin.value(),
        }


class TaskWidget(QFrame):
    """Widget for displaying and controlling individual automation tasks"""

    def __init__(
        self, task_name: str, description: str, parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.task_name = task_name
        self.description = description
        self.enabled = False
        self.status = "Disabled"  # Add status attribute
        self.init_ui()

    def init_ui(self):
        """Initialize the UI for this task widget"""
        # Set frame style
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet(
            """
            QFrame {
                background-color: #f5f5f5;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }
            QFrame:hover {
                background-color: #e9e9e9;
            }
        """
        )

        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Task name label
        self.name_label = QLabel(self.task_name)
        self.name_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.name_label)

        # Status indicator
        self.status_label = QLabel(self.status)
        self.status_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.status_label)

        # Stats label
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #666666;")
        layout.addWidget(self.stats_label)

        # Enable/disable checkbox
        self.enable_cb = QCheckBox("Enable")
        self.enable_cb.setChecked(self.enabled)
        self.enable_cb.stateChanged.connect(self.toggle_enabled)
        layout.addWidget(self.enable_cb)

        # Run now button
        self.run_btn = QPushButton("Run Now")
        self.run_btn.setEnabled(self.enabled)
        self.run_btn.clicked.connect(self.run_now)
        layout.addWidget(self.run_btn)

        # Configure button
        self.config_btn = QPushButton("Configure")
        self.config_btn.setEnabled(self.enabled)
        layout.addWidget(self.config_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumWidth(100)
        layout.addWidget(self.progress_bar)

        # Add stretch to push everything to the left
        layout.addStretch()

    def toggle_enabled(self, state):
        """Toggle the enabled state of this task"""
        self.enabled = state == Qt.Checked
        self.run_btn.setEnabled(self.enabled)
        self.config_btn.setEnabled(self.enabled)
        self.update_status("Disabled" if not self.enabled else "Ready")

    def run_now(self):
        """Run this task immediately"""
        if hasattr(self.parent(), "run_task"):
            self.update_status("Running...")
            self.progress_bar.setValue(50)  # Indicate progress
            self.parent().run_task(self.task_name)

    def update_status(self, status: str, color: str = None):
        """Update the status display"""
        self.status = status
        self.status_label.setText(status)

        # Update status color based on state
        if color:
            self.status_label.setStyleSheet(f"color: {color};")
        elif status == "Running...":
            self.status_label.setStyleSheet("color: #0078D7; font-weight: bold;")
        elif status == "Completed":
            self.status_label.setStyleSheet("color: #107C10;")
        elif status == "Failed":
            self.status_label.setStyleSheet("color: #D83B01;")
        elif status == "Ready":
            self.status_label.setStyleSheet("color: #107C10;")
        else:
            self.status_label.setStyleSheet("color: #888888;")

    def update_progress(self, progress: int, message: str):
        """Update task progress"""
        self.progress = progress
        self.progress_bar.setValue(progress)
        self.progress_bar.setVisible(progress > 0)
        if message:
            self.status_label.setText(f"{self.status} - {message}")

    def update_stats(self, stats: dict):
        """Update task statistics"""
        if not stats:
            self.stats_label.setText("")
            return

        success_rate = stats.get("success_rate", 0)
        avg_runtime = stats.get("avg_runtime", 0)
        total_runs = stats.get("total_runs", 0)
        failures = stats.get("failures", 0)

        stats_text = (
            f"Success Rate: {success_rate:.1f}% | "
            f"Avg Runtime: {avg_runtime:.1f}s | "
            f"Total Runs: {total_runs} | "
            f"Failures: {failures}"
        )
        self.stats_label.setText(stats_text)


class AutomationTab(QWidget):
    """Tab for managing automation tasks"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.worker = None
        self.tasks = {}
        self.init_ui()
        self.load_tasks()

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # Update every second

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Task Schedule Group
        schedule_group = QGroupBox("Task Schedule")
        schedule_layout = QFormLayout()

        # Content Generation Schedule
        self.content_schedule = QComboBox()
        self.content_schedule.addItems(["Daily", "Every 2 Days", "Weekly", "Custom"])
        schedule_layout.addRow("Content Generation:", self.content_schedule)

        # WordPress Posting Schedule
        self.wordpress_schedule = QComboBox()
        self.wordpress_schedule.addItems(["Daily", "Every 2 Days", "Weekly", "Custom"])
        schedule_layout.addRow("WordPress Posting:", self.wordpress_schedule)

        # Pinterest Pinning Schedule
        self.pinterest_schedule = QComboBox()
        self.pinterest_schedule.addItems(["Daily", "Every 2 Days", "Weekly", "Custom"])
        schedule_layout.addRow("Pinterest Pinning:", self.pinterest_schedule)

        schedule_group.setLayout(schedule_layout)
        layout.addWidget(schedule_group)

        # Task Limits Group
        limits_group = QGroupBox("Task Limits")
        limits_layout = QFormLayout()

        # Max Posts per Day
        self.max_posts = QSpinBox()
        self.max_posts.setRange(1, 50)
        self.max_posts.setValue(10)
        limits_layout.addRow("Max Posts per Day:", self.max_posts)

        # Max Images per Post
        self.max_images = QSpinBox()
        self.max_images.setRange(1, 10)
        self.max_images.setValue(3)
        limits_layout.addRow("Max Images per Post:", self.max_images)

        # Post Interval
        self.post_interval = QSpinBox()
        self.post_interval.setRange(1, 24)
        self.post_interval.setValue(4)
        self.post_interval.setSuffix(" hours")
        limits_layout.addRow("Post Interval:", self.post_interval)

        limits_group.setLayout(limits_layout)
        layout.addWidget(limits_group)

        # Task Status Group
        status_group = QGroupBox("Task Status")
        status_layout = QVBoxLayout()

        # Task Table
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(5)
        self.task_table.setHorizontalHeaderLabels(
            ["Task", "Status", "Last Run", "Next Run", "Actions"]
        )
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        status_layout.addWidget(self.task_table)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Control Buttons
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("Start Automation")
        self.start_button.clicked.connect(self.start_automation)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Automation")
        self.stop_button.clicked.connect(self.stop_automation)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_automation)
        self.pause_button.setEnabled(False)
        button_layout.addWidget(self.pause_button)

        layout.addLayout(button_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def load_tasks(self):
        """Load task configurations"""
        try:
            # Load tasks from config
            config = self.parent.config.get("automation", {})

            # Update UI with loaded settings
            self.content_schedule.setCurrentText(
                config.get("content_schedule", "Daily")
            )
            self.wordpress_schedule.setCurrentText(
                config.get("wordpress_schedule", "Daily")
            )
            self.pinterest_schedule.setCurrentText(
                config.get("pinterest_schedule", "Daily")
            )
            self.max_posts.setValue(config.get("max_posts_per_day", 10))
            self.max_images.setValue(config.get("max_images_per_post", 3))
            self.post_interval.setValue(config.get("post_interval", 4))

            # Update task table
            self.update_task_table()

        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load tasks: {str(e)}")

    def update_task_table(self):
        """Update the task table with current status"""
        try:
            # Clear table
            self.task_table.setRowCount(0)

            # Add tasks
            tasks = [
                {
                    "name": "Content Generation",
                    "status": "Scheduled",
                    "last_run": "2024-03-20 10:00",
                    "next_run": "2024-03-21 10:00",
                },
                {
                    "name": "WordPress Posting",
                    "status": "Scheduled",
                    "last_run": "2024-03-20 11:00",
                    "next_run": "2024-03-21 11:00",
                },
                {
                    "name": "Pinterest Pinning",
                    "status": "Scheduled",
                    "last_run": "2024-03-20 12:00",
                    "next_run": "2024-03-21 12:00",
                },
            ]

            for task in tasks:
                row = self.task_table.rowCount()
                self.task_table.insertRow(row)

                # Task name
                name_item = QTableWidgetItem(task["name"])
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                self.task_table.setItem(row, 0, name_item)

                # Status
                status_item = QTableWidgetItem(task["status"])
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                self.task_table.setItem(row, 1, status_item)

                # Last run
                last_run_item = QTableWidgetItem(task["last_run"])
                last_run_item.setFlags(last_run_item.flags() & ~Qt.ItemIsEditable)
                self.task_table.setItem(row, 2, last_run_item)

                # Next run
                next_run_item = QTableWidgetItem(task["next_run"])
                next_run_item.setFlags(next_run_item.flags() & ~Qt.ItemIsEditable)
                self.task_table.setItem(row, 3, next_run_item)

                # Action buttons
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(0, 0, 0, 0)

                run_button = QPushButton("Run Now")
                run_button.clicked.connect(lambda: self.run_task(task["name"]))
                action_layout.addWidget(run_button)

                self.task_table.setCellWidget(row, 4, action_widget)

        except Exception as e:
            logger.error(f"Error updating task table: {e}")
            QMessageBox.warning(self, "Error", f"Failed to update task table: {str(e)}")

    def start_automation(self):
        """Start automation tasks"""
        try:
            # Update UI
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.pause_button.setEnabled(True)
            self.progress_bar.setVisible(True)

            # Start worker
            if self.worker:
                self.worker.start()

            QMessageBox.information(self, "Success", "Automation started successfully")

        except Exception as e:
            logger.error(f"Error starting automation: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start automation: {str(e)}")

    def stop_automation(self):
        """Stop automation tasks"""
        try:
            # Update UI
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.pause_button.setEnabled(False)
            self.progress_bar.setVisible(False)

            # Stop worker
            if self.worker:
                self.worker.stop()

            QMessageBox.information(self, "Success", "Automation stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping automation: {e}")
            QMessageBox.critical(self, "Error", f"Failed to stop automation: {str(e)}")

    def pause_automation(self):
        """Pause automation tasks"""
        try:
            # Update UI
            self.pause_button.setText("Resume")
            self.pause_button.clicked.disconnect()
            self.pause_button.clicked.connect(self.resume_automation)

            # Pause worker
            if self.worker:
                self.worker.pause()

            QMessageBox.information(self, "Success", "Automation paused successfully")

        except Exception as e:
            logger.error(f"Error pausing automation: {e}")
            QMessageBox.critical(self, "Error", f"Failed to pause automation: {str(e)}")

    def resume_automation(self):
        """Resume automation tasks"""
        try:
            # Update UI
            self.pause_button.setText("Pause")
            self.pause_button.clicked.disconnect()
            self.pause_button.clicked.connect(self.pause_automation)

            # Resume worker
            if self.worker:
                self.worker.resume()

            QMessageBox.information(self, "Success", "Automation resumed successfully")

        except Exception as e:
            logger.error(f"Error resuming automation: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to resume automation: {str(e)}"
            )

    def run_task(self, task_name: str):
        """Run a specific task immediately"""
        try:
            # Update task status
            for row in range(self.task_table.rowCount()):
                if self.task_table.item(row, 0).text() == task_name:
                    self.task_table.item(row, 1).setText("Running")
                    break

            # Run task
            if self.worker:
                self.worker.run_task(task_name)

            QMessageBox.information(
                self, "Success", f"Task {task_name} started successfully"
            )

        except Exception as e:
            logger.error(f"Error running task: {e}")
            QMessageBox.critical(self, "Error", f"Failed to run task: {str(e)}")

    def update_status(self):
        """Update status displays"""
        if self.worker:
            # Update worker status
            status = self.worker.get_status()
            self.start_button.setEnabled(status != "Running")
            self.stop_button.setEnabled(status == "Running")
            self.pause_button.setEnabled(status == "Running")
            self.progress_bar.setVisible(status == "Running")

            # Update task statistics
            for task_name, task_widget in self.tasks.items():
                stats = self.worker.get_task_stats(task_name)
                task_widget.update_stats(stats)

    def set_worker(self, worker):
        """Set the automation worker and connect signals"""
        self.worker = worker
        if worker:
            # Connect worker signals
            worker.status_changed.connect(self.on_worker_status_changed)
            worker.task_completed.connect(self.on_task_completed)
            worker.task_progress.connect(self.on_task_progress)
            worker.error_occurred.connect(self.on_error)
            worker.queue_updated.connect(self.on_queue_updated)

            # Connect task controls
            for task_widget in self.tasks.values():
                task_widget.config_btn.clicked.connect(
                    lambda checked, name=task_widget.task_name: self.configure_task(
                        name
                    )
                )

    def add_task(self, name: str, description: str):
        """Add a task to the task list"""
        task_widget = TaskWidget(name, description, self)
        self.tasks[name] = task_widget
        self.task_table.insertRow(self.task_table.rowCount())
        self.task_table.setItem(
            self.task_table.rowCount() - 1, 0, QTableWidgetItem(name)
        )
        self.task_table.setCellWidget(
            self.task_table.rowCount() - 1, 4, task_widget.run_btn
        )

    def configure_task(self, task_name):
        """Open task configuration dialog"""
        if not self.worker:
            return

        task = self.worker.tasks.get(task_name)
        if not task:
            return

        dialog = TaskConfigDialog(task_name, task, self)
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.get_config()
            self.worker.set_task_schedule(task_name, config["schedule"])
            self.worker.set_task_config(
                task_name, retry_count=config["retry_count"], timeout=config["timeout"]
            )

    def on_worker_status_changed(self, status):
        """Handle worker status changes"""
        self.start_button.setEnabled(status != "Running")
        self.stop_button.setEnabled(status == "Running")
        self.pause_button.setEnabled(status == "Running")
        self.progress_bar.setVisible(status == "Running")

    def on_task_completed(self, task_name, success, message):
        """Handle task completion"""
        if task_name in self.tasks:
            color = "green" if success else "red"
            status = "Completed" if success else "Failed"
            task_widget = self.tasks[task_name]
            task_widget.update_status(status, color)
            task_widget.progress_bar.setVisible(False)
            self.log(f"Task {task_name} {status.lower()}: {message}")

            # Update history
            self.add_history_entry(task_name, success, message)

    def on_task_progress(self, task_name, progress, message):
        """Handle task progress updates"""
        if task_name in self.tasks:
            self.tasks[task_name].update_progress(progress, message)

    def on_queue_updated(self, queue_items):
        """Handle queue updates"""
        if not queue_items:
            self.queue_label.setText("Queue: Empty")
        else:
            tasks = ", ".join(item["task"] for item in queue_items)
            self.queue_label.setText(f"Queue: {tasks}")

    def on_error(self, error_msg):
        """Handle worker errors"""
        self.log(f"Error: {error_msg}", "error")

    def add_history_entry(self, task_name, success, message):
        """Add an entry to the task history table"""
        row = self.history_table.rowCount()
        self.history_table.insertRow(row)

        # Add task details
        self.history_table.setItem(row, 0, QTableWidgetItem(task_name))
        self.history_table.setItem(
            row, 1, QTableWidgetItem(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        self.history_table.setItem(
            row, 2, QTableWidgetItem(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        self.history_table.setItem(
            row, 3, QTableWidgetItem("Success" if success else "Failed")
        )
        self.history_table.setItem(
            row, 4, QTableWidgetItem("0s")
        )  # Runtime would be calculated from actual timestamps

        # Set colors
        for col in range(self.history_table.columnCount()):
            item = self.history_table.item(row, col)
            item.setBackground(QColor("#d4edda") if success else QColor("#f8d7da"))

        # Trim history if too long
        while self.history_table.rowCount() > 100:
            self.history_table.removeRow(0)

        # Scroll to latest entry
        self.history_table.scrollToBottom()

    def log(self, message, level="info"):
        """Add a message to the log viewer"""
        color = {"info": "black", "error": "red", "warning": "orange"}.get(
            level, "black"
        )

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_viewer.append(
            f'<span style="color: gray;">[{timestamp}]</span> '
            f'<span style="color: {color};">{message}</span>'
        )
