from PyQt6.QtWidgets import (
    QApplication
)

# Example main window with "Modify credentials" button
from PyQt6.QtWidgets import QMainWindow, QPushButton
from ConfigManager import ConfigManager
import sys

import CredentialsDialog

class MainWindow(QMainWindow):
    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.setWindowTitle("App")

        btn = QPushButton("Modify Credentials")
        btn.clicked.connect(self.modify_credentials)
        self.setCentralWidget(btn)

    def modify_credentials(self):
        dlg = CredentialsDialog.CredentialsDialog(self.config)
        dlg.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    cfg = ConfigManager()

    # loop until valid
    CredentialsDialog.ensure_credentials(cfg)

    win = MainWindow(cfg)
    win.show()
    sys.exit(app.exec())
