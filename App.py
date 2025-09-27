import sys
import requests, json, base64
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QLabel,
    QPushButton, QInputDialog, QVBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from ConfigManager import ConfigManager
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

class ConfigApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Config Checker")
        self.setFixedSize(220, 160)

        # Verify public key & payload on startup
        self.verify_payload()

        self.config = ConfigManager()

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Grid layout 2x2
        self.grid = QGridLayout()
        self.grid.setSpacing(5)

        self.grid.addWidget(QLabel("yid"), 0, 0)
        self.grid.addWidget(QLabel("pwd"), 1, 0)

        self.status_yid = QLabel()
        self.status_pwd = QLabel()
        self.grid.addWidget(self.status_yid, 0, 1)
        self.grid.addWidget(self.status_pwd, 1, 1)

        main_layout.addLayout(self.grid)

        # Button
        self.check_btn = QPushButton("Check / Set Keys")
        self.check_btn.clicked.connect(self.check_keys)
        main_layout.addWidget(self.check_btn)

        # Decrypted values label
        self.decrypted_label = QLabel("")
        self.decrypted_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(self.decrypted_label)

        self.setLayout(main_layout)

        # Initial display
        self.update_status_labels()

    def verify_payload(self):
        url = "https://singular-snickerdoodle-de09f9.netlify.app/payload.json"
        try:
            r = requests.get(url, timeout=5)
            data = r.json()
            payload_bytes = base64.b64decode(data["payload"])
            signature = base64.b64decode(data["sig"])

            public_key_pem = b"""-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEdoUvlLjynhTV+MUNR6MhuBofhAfV
tzviR3OO8ugwD2m1V28R8NxJfhDrf76q36Fn4wCN7WSMDmbTfKB8/hB08A==
-----END PUBLIC KEY-----"""

            public_key = serialization.load_pem_public_key(public_key_pem)
            public_key.verify(signature, payload_bytes, ec.ECDSA(hashes.SHA256()))

            payload = json.loads(payload_bytes)
            return payload.get("allow", False)
        except requests.RequestException:
            QMessageBox.critical(self, "Error", "The app has been permanently terminated by the developer. Thank you for using the app.")
            sys.exit(1)
        except Exception:
            QMessageBox.critical(self, "Error", "Signature verification failed! App will exit.")
            sys.exit(1)

    def update_status_labels(self):
        self.set_status_label(self.status_yid, "yid")
        self.set_status_label(self.status_pwd, "pwd")

        # Decrypted values, mask pwd
        yid_val = self.config.get("yid") or ""
        pwd_val = self.config.get("pwd") or ""
        masked_pwd = "•" * len(pwd_val)
        self.decrypted_label.setText(f"yid: {yid_val}\npwd: {masked_pwd}")

    def set_status_label(self, label, key):
        value = self.config.get(key)
        if value:
            label.setText("✔")
            label.setStyleSheet("color: green; font-weight: bold;")
        else:
            label.setText("✖")
            label.setStyleSheet("color: red; font-weight: bold;")

    def check_keys(self):
        for key in ["yid", "pwd"]:
            while not self.config.get(key):
                if key == "yid":
                    text, ok = QInputDialog.getText(
                        self, "Missing Key", f"Enter 6-digit value for '{key}':"
                    )
                    if not ok:
                        break
                    text = text.strip()
                    if not text.isdigit() or len(text) != 6:
                        QMessageBox.warning(self, "Invalid Input", "yid must be exactly 6 digits.")
                        continue
                else:  # pwd hidden
                    text, ok = QInputDialog.getText(
                        self, "Missing Key", f"Enter value for '{key}':",
                        QInputDialog.TextEchoMode.Password
                    )
                    if not ok or not text.strip():
                        break
                self.config.set(key, text.strip())
        self.update_status_labels()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConfigApp()
    window.show()
    sys.exit(app.exec())
