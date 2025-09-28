from PyQt6.QtWidgets import QSplashScreen
from PyQt6.QtGui import QPainter, QFont, QFontMetrics
from PyQt6.QtCore import Qt

class TextSplash(QSplashScreen):
    def __init__(self, text="Loading...", font=None, padding=20):
        super().__init__()
        self.text = text
        if font is None:
            font = QFont("Arial", 12)
        self.setFont(font)

        # Calculate size based on text
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.height()
        self.setFixedSize(text_width + padding, text_height + padding)

        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

    def drawContents(self, painter: QPainter):
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text)