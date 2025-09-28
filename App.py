from PyQt6.QtWidgets import QApplication, QMessageBox, QMainWindow, QPushButton, QSplashScreen
from PyQt6.QtCore import QTimer

from ConfigManager import ConfigManager
import sys
import CredentialsDialog
from Loading import TextSplash
from verify_payload import verify_payload

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

    # Splash screen sized to fit text
    splash = TextSplash(text="Loading app...")
    splash.show()
    app.processEvents()  # force splash to show

    # Verify payload
    allowed, message = verify_payload()
    if not allowed:
        splash.close()
        msg_box = QMessageBox()
        msg_box.setWindowTitle("App Terminated")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.exec()
        sys.exit(1)
    splash.close()

    # Initialize config and ensure credentials
    cfg = ConfigManager()
    CredentialsDialog.ensure_credentials(cfg)

    # Small delay to let user see splash
    QTimer.singleShot(200, splash.close)

    # Show main window
    win = MainWindow(cfg)
    win.show()

    sys.exit(app.exec())
