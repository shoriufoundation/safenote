"""
SafeNote — Encrypted Desktop Audio Recorder.

Organization: Shoriu Foundation
Version: 0.1.0-dev
License: WTFPL 2
Slogan: Your safety. Your privacy. Your choice.
"""

from __future__ import annotations

import logging
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication

from core.application import get_app
from ui.main_window import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("SafeNote")


def _create_app_icon() -> QIcon:
    """Create default application icon."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setBrush(QColor("#1f6feb"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(4, 4, 56, 56, 14, 14)

    painter.setPen(QColor("#ffffff"))
    font = QFont("Segoe UI", 20, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "SN")
    painter.end()

    return QIcon(pixmap)


def main() -> None:
    app = QApplication(sys.argv)

    app.setApplicationName("SafeNote")
    app.setOrganizationName("Shoriu Foundation")
    app.setOrganizationDomain("shoriu.org")
    app.setApplicationVersion("0.1.0-dev")
    app.setWindowIcon(_create_app_icon())

    app_mgr = get_app()
    app.setStyleSheet(app_mgr.get_theme_stylesheet())

    window = MainWindow()

    # If start_minimized is false (default), show window; otherwise remain in tray
    if not app_mgr.config.get_start_minimized():
        window.show()
    else:
        logger.info("Starting minimized to system tray.")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
