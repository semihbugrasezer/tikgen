from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QLineEdit,
    QComboBox,
    QListWidget,
    QMessageBox,
)
from PyQt5.QtCore import Qt
import logging

logger = logging.getLogger(__name__)


class ContentTab(QWidget):
    """Content tab for managing and creating content"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QHBoxLayout()

        # Left panel - Content list
        left_panel = QVBoxLayout()
        self.content_list = QListWidget()
        self.content_list.itemClicked.connect(self.load_content)

        # Content list buttons
        list_buttons = QHBoxLayout()
        self.new_btn = QPushButton("New")
        self.new_btn.clicked.connect(self.new_content)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_content)

        list_buttons.addWidget(self.new_btn)
        list_buttons.addWidget(self.delete_btn)

        left_panel.addWidget(QLabel("Content List"))
        left_panel.addWidget(self.content_list)
        left_panel.addLayout(list_buttons)

        # Right panel - Content editor
        right_panel = QVBoxLayout()

        # Title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit()
        title_layout.addWidget(self.title_edit)

        # Content type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Article", "Image", "Video"])
        type_layout.addWidget(self.type_combo)

        # Content editor
        self.content_edit = QTextEdit()

        # Save button
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_content)

        right_panel.addLayout(title_layout)
        right_panel.addLayout(type_layout)
        right_panel.addWidget(QLabel("Content:"))
        right_panel.addWidget(self.content_edit)
        right_panel.addWidget(self.save_btn)

        # Add panels to main layout
        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 2)

        self.setLayout(layout)

    def load_content_list(self):
        """Load content list from database"""
        try:
            self.content_list.clear()
            # Content loading logic will be implemented here
        except Exception as e:
            logger.error(f"Error loading content list: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to load content list: {str(e)}"
            )

    def load_content(self, item):
        """Load selected content into editor"""
        try:
            # Content loading logic will be implemented here
            pass
        except Exception as e:
            logger.error(f"Error loading content: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load content: {str(e)}")

    def new_content(self):
        """Create new content"""
        try:
            self.title_edit.clear()
            self.content_edit.clear()
            self.type_combo.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Error creating new content: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to create new content: {str(e)}"
            )

    def save_content(self):
        """Save current content"""
        try:
            # Content saving logic will be implemented here
            QMessageBox.information(self, "Success", "Content saved successfully")
        except Exception as e:
            logger.error(f"Error saving content: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save content: {str(e)}")

    def delete_content(self):
        """Delete selected content"""
        try:
            current_item = self.content_list.currentItem()
            if current_item:
                # Content deletion logic will be implemented here
                self.content_list.takeItem(self.content_list.row(current_item))
        except Exception as e:
            logger.error(f"Error deleting content: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete content: {str(e)}")
