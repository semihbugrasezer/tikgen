from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class TrendsTab(QWidget):
    """Trends tab for analyzing Pinterest trends"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Trends"))
        self.setLayout(layout)

    def load_trends(self):
        """Load trend data"""
        pass
