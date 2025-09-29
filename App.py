import os
from PyQt6.QtWidgets import (
    QApplication, QMessageBox, QMainWindow, QPushButton,
    QWidget, QVBoxLayout, QCheckBox, QLineEdit,
    QComboBox, QLabel, QSpinBox, QHBoxLayout
)

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIntValidator
from Download import Download
import Label
from PogLocator import PogLocator
from Telxon import LabelGenerator
from Units import UnitFactory
from Planogram import Planogram

from ConfigManager import ConfigManager
import sys
import CredentialsDialog
from Loading import TextSplash
from SurveyDB import SurveyDB
from verify_payload import verify_payload
import subprocess  # for opening PDF

class MainWindow(QMainWindow):
    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.setWindowTitle("App")

        # track visibility flag
        self.visible = False

        # initially load the survey db
        self.get_survey()

        # button to modify credentials
        btn = QPushButton("Modify Credentials")
        btn.clicked.connect(self.modify_credentials)

        self.pog = None
        # pog input
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter 5 or 6 digit POG #")
        self.input_field.setValidator(QIntValidator(10000, 999999))  # restrict 5–6 digits
        self.input_field.returnPressed.connect(self.handle_pog_lookup)

        enter_btn = QPushButton("Enter")
        enter_btn.clicked.connect(self.handle_pog_lookup)

        # checkbox for curious toggle
        curious_chk = QCheckBox("I'm feeling curious")
        curious_chk.stateChanged.connect(self.toggle_visible)

        # dropdown for sizes
        self.dropdown = QComboBox()
        self.dropdown.currentIndexChanged.connect(self.handle_dropdown_selection)

        self.status_label = QLabel("Status: Ready")

        # From/To spinboxes
        self.range_container = QWidget()
        self.range_layout = QHBoxLayout()
        self.range_container.setLayout(self.range_layout)
        self.range_container.hide()

        self.from_spin = QSpinBox()
        self.from_spin.setMinimum(1)
        self.to_spin = QSpinBox()
        self.to_spin.setMinimum(1)
        self.continue_btn = QPushButton("Continue")
        self.continue_btn.clicked.connect(self.handle_continue)

        self.range_layout.addWidget(QLabel("From:"))
        self.range_layout.addWidget(self.from_spin)
        self.range_layout.addWidget(QLabel("To:"))
        self.range_layout.addWidget(self.to_spin)
        self.range_layout.addWidget(self.continue_btn)

        # layout
        container = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(btn)
        layout.addWidget(self.input_field)
        layout.addWidget(enter_btn)
        layout.addWidget(self.dropdown)
        layout.addWidget(curious_chk)
        layout.addWidget(self.status_label)
        layout.addWidget(self.range_container)

        container.setLayout(layout)
        self.setCentralWidget(container)

    def modify_credentials(self):
        dlg = CredentialsDialog.CredentialsDialog(self.config)
        dlg.exec()

        self.get_survey()

    def get_survey(self):
        store_num = self.config.get('store_num')
        try:
            self.survey_db = SurveyDB(store_num)
        except Exception:
            # cannot get survey
            self.survey_db = None
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Store survey not obtained")
            msg_box.setText(f'Cannot find survey database for {store_num}.')
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.exec()
    
    def toggle_visible(self):
        self.visible = not self.visible
        print(f"self.visible = {self.visible}")
    
    def handle_pog_lookup(self):
        pog_num = self.input_field.text().strip()
        if not (len(pog_num) in [5, 6]):
            QMessageBox.warning(self, "Invalid Input", "POG must be 5 or 6 digits.")
            return

        locator = PogLocator()
        try:
            pog_size, size_href_pairs = locator.get_pog_links(
                pog_num=pog_num,
                survey_db=self.survey_db,
                store_num=self.config.get("store_num"),
                visible=self.visible
            )

            self.dropdown.clear()
            for size_str, href in size_href_pairs:
                self.dropdown.addItem(size_str, href)

            if pog_size:
                target = UnitFactory.create(pog_size)
                match_found = False
                for i, (size_str, href) in enumerate(size_href_pairs):
                    if UnitFactory.create(size_str) == target:
                        self.dropdown.setCurrentIndex(i)
                        match_found = True
                        break
                if not match_found:
                    QMessageBox.information(self, "Select Size", "Could not find POG size, please select the size.")
            else:
                QMessageBox.information(self, "Select Size", "Could not find POG size, please select the size.")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def handle_dropdown_selection(self, index: int):
        if index < 0:
            return
        href = self.dropdown.itemData(index)
        if not href:
            return

        self.status_label.setText(f"Status: Loading {href}...")
        try:
            self.pog = Planogram()
            self.pog.get_pog(href)
            items = self.pog.get_num_items()
            est_sec = int(items * 4.5)
            minutes, seconds = divmod(est_sec, 60)
            self.status_label.setText(
                f"Status: {items} items found. "
                f"Label generation will take ~{minutes}m {seconds}s."
            )

            if items > 60:
                # Show From/To inputs
                self.from_spin.setMaximum(items)
                self.to_spin.setMaximum(items)
                self.to_spin.setValue(items)
                self.from_spin.setValue(1)
                self.range_container.show()
            else:
                # Automatically start
                self.range_container.hide()
                self.generate_labels_via_telxon(self.pog, 1, items)

        except Exception as e:
            self.status_label.setText("Status: Failed to load POG")
            QMessageBox.critical(self, "Error", str(e))
    
    def handle_continue(self):
        if not self.pog:
            return
        from_idx = self.from_spin.value()
        to_idx = self.to_spin.value()
        self.range_container.hide()
        self.generate_labels_via_telxon(self.pog, from_idx, to_idx)

    def generate_labels_via_telxon(self, pog: Planogram, from_idx: int, to_idx: int):
        subset_df = pog.pog_df.iloc[from_idx - 1:to_idx].copy()

        yid = self.config.get('yid')
        pwd = self.config.get('pwd')
        creds = (yid, pwd)

        self.status_label.setText(f"Generating labels for {len(subset_df)} items...")

        # Generate labels via Telxon
        generator = LabelGenerator()
        try:
            generator.generate_labels(subset_df, creds, visibility=self.visible)
            self.status_label.setText("Label generation completed. Downloading PDF from email...")
        except Exception as e:
            self.status_label.setText("Label generation failed")
            QMessageBox.critical(self, "Error", f"Telxon label generation failed:\n{e}")
            return

        # Download the PDF
        downloader = Download()
        try:
            pdf_path = downloader.get_pdf(yid, visible=self.visible)
            self.status_label.setText(f"Downloaded PDF: {pdf_path}")
        except Exception as e:
            self.status_label.setText("Failed to download PDF")
            QMessageBox.critical(self, "Error", f"PDF download failed:\n{e}")
            return

        # Decorate labels
        try:
            label_obj = Label.Label(label_sheet=pdf_path, inches=2)  # adjust inches as needed
            label_obj.get_crc_seq()
            label_obj.decorate_labels(pog_df=subset_df, outfile="numbered_labels")
            self.status_label.setText("Labels decorated successfully")
        except Exception as e:
            self.status_label.setText("Failed to decorate PDF")
            QMessageBox.critical(self, "Error", f"Label decoration failed:\n{e}")
            return

        # Open the generated PDF cross-platform
        outfile_path = os.path.abspath("numbered_labels.pdf")
        try:
            if sys.platform.startswith("win"):
                os.startfile(outfile_path)
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", outfile_path])
            else:  # Linux
                subprocess.Popen(["xdg-open", outfile_path])
            self.status_label.setText("Labels generated and opened. Closing app...")
        except Exception as e:
            self.status_label.setText("Failed to open PDF")
            QMessageBox.warning(self, "Warning", f"Could not open PDF automatically:\n{e}")

        # Quit app after a short delay to allow PDF to open
        QTimer.singleShot(500, QApplication.quit)

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

    # Show main window
    win = MainWindow(cfg)
    win.show()

    sys.exit(app.exec())
