from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit,
    QPushButton, QHBoxLayout, QMessageBox, QVBoxLayout, QLabel
)
from PyQt6.QtGui import QIntValidator
from ConfigManager import ConfigManager
import sys

REQUIRED_FIELDS = ["store_num", "lan_id", "yid", "pwd"]

class CredentialsDialog(QDialog):
    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.setWindowTitle("Credentials")

        outer = QVBoxLayout()

        # Info text
        info_label = QLabel(
            "The app requires all 4 fields. "
            "The information is encrypted locally and will only be used for automation."
        )
        info_label.setWordWrap(True)
        outer.addWidget(info_label)

        # Form layout
        layout = QFormLayout()

        self.store_num = QLineEdit()
        self.store_num.setValidator(QIntValidator(0, 9999999))
        self.store_num.setMaxLength(7)
        layout.addRow("Store Num (7 digits):", self.store_num)

        self.lan_id = QLineEdit()
        layout.addRow("LAN ID:", self.lan_id)

        self.yid = QLineEdit()
        self.yid.setValidator(QIntValidator(0, 999999))
        self.yid.setMaxLength(6)
        layout.addRow("YID (6 digits):", self.yid)

        self.pwd = QLineEdit()
        self.pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd.setMaxLength(8)
        layout.addRow("Password (7–8 digits):", self.pwd)

        outer.addLayout(layout)

        # Buttons
        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self.save)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)

        outer.addLayout(btns)
        self.setLayout(outer)

        # Pre-fill existing values except password
        self.load_existing()

        self.first_run = False  # will be set from ensure_credentials

    def set_first_run(self, first_run: bool):
        self.first_run = first_run

    def closeEvent(self, event):
        """Handle window X button."""
        if self.first_run:
            # Quit app immediately if first run
            sys.exit(0)
        else:
            # Accept normal close
            event.accept()

    def load_existing(self):
        store_num = self.config.get("store_num")
        lan_id = self.config.get("lan_id")
        yid = self.config.get("yid")
        if store_num:
            self.store_num.setText(store_num)
        if lan_id:
            self.lan_id.setText(lan_id)
        if yid:
            self.yid.setText(yid)

    def save(self):
        if len(self.store_num.text()) != 7:
            QMessageBox.warning(self, "Error", "Store number must be 7 digits.")
            return
        if len(self.yid.text()) != 6:
            QMessageBox.warning(self, "Error", "YID must be 6 digits.")
            return
        if len(self.pwd.text()) not in (7, 8):
            QMessageBox.warning(self, "Error", "Password must be 7 or 8 digits.")
            return

        self.config.set("store_num", self.store_num.text())
        self.config.set("lan_id", self.lan_id.text())
        self.config.set("yid", self.yid.text())
        self.config.set("pwd", self.pwd.text())
        self.accept()

def ensure_credentials(config: ConfigManager, parent=None):
    """
    Ensure all credentials are filled. 
    - If all fields exist: do nothing.
    - If none exist: prompt user to fill them.
    - Cancel loops only if fields incomplete.
    """
    # Check if all or none are filled
    filled = [bool(config.get(f)) for f in REQUIRED_FIELDS]
    if all(filled):
        return True  # everything exists, no prompt
    else:
        complete = False  # none or incomplete

    while not complete:
        dlg = CredentialsDialog(config)
        dlg.set_first_run(True)  # only first run allows X to quit
        result = dlg.exec()

        # Check completeness after dialog closes
        complete = all(config.get(f) for f in REQUIRED_FIELDS)

        if result == QDialog.DialogCode.Accepted and complete:
            return True  # user saved all fields

        elif result == QDialog.DialogCode.Rejected:
            if not complete:
                # Cancel pressed but fields incomplete
                QMessageBox.warning(
                    parent, "Missing Data",
                    "All fields must be set before using the app."
                )
                continue
            else:
                # Cancel pressed and fields exist (later run)
                return True
