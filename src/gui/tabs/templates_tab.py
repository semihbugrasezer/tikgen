from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class TemplatesTab(QWidget):
    """Templates tab for managing content templates"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Templates"))
        self.setLayout(layout)

    def load_templates(self):
        """Load templates from database"""
        pass
