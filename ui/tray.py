"""
SafeNote System Tray Integration.

Provides background tray controls and status indication:
- Open SafeNote window
- Start / Stop recording directly from tray
- Open recording library
- Trigger Emergency Hide
- Clean exit
- Visual indicator when microphone is active (never conceals recording)
"""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget

from core.application import get_app

logger = logging.getLogger(__name__)


def _create_tray_icon(is_recording: bool) -> QIcon:
    """Dynamically draw a crisp tray icon using QPainter."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    if is_recording:
        # High-visibility pulsing red circle with 'REC' text
        painter.setBrush(QColor("#da3633"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 28, 28)

        painter.setPen(QColor("#ffffff"))
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "REC")
    else:
        # Green / Blue shield icon for SafeNote
        painter.setBrush(QColor("#1f6feb"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(3, 3, 26, 26, 6, 6)

        painter.setPen(QColor("#ffffff"))
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "SN")

    painter.end()
    return QIcon(pixmap)


class SafeNoteTrayIcon(QSystemTrayIcon):
    """
    Application System Tray Icon and Context Menu.
    """

    open_requested = Signal()
    start_recording_requested = Signal()
    stop_recording_requested = Signal()
    open_library_requested = Signal()
    emergency_hide_requested = Signal()
    exit_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._is_recording = False
        self._init_menu()
        self.update_recording_state(False)
        self.activated.connect(self._on_activated)

    def _init_menu(self) -> None:
        self._menu = QMenu()

        self._action_open = QAction("SafeNote", self)
        self._action_open.triggered.connect(self.open_requested.emit)

        self._action_toggle_rec = QAction("⏺ Start Recording", self)
        self._action_toggle_rec.triggered.connect(self._toggle_recording)

        self._action_library = QAction("📁 Recording Library", self)
        self._action_library.triggered.connect(self.open_library_requested.emit)

        self._action_hide = QAction("🛡️ Emergency Hide", self)
        self._action_hide.triggered.connect(self.emergency_hide_requested.emit)

        self._action_exit = QAction("❌ Exit", self)
        self._action_exit.triggered.connect(self.exit_requested.emit)

        self._menu.addAction(self._action_open)
        self._menu.addSeparator()
        self._menu.addAction(self._action_toggle_rec)
        self._menu.addAction(self._action_library)
        self._menu.addAction(self._action_hide)
        self._menu.addSeparator()
        self._menu.addAction(self._action_exit)

        self.setContextMenu(self._menu)
        self.retranslate()
        get_app().language_changed.connect(self.retranslate)

    def retranslate(self) -> None:
        app = get_app()
        self._action_open.setText(f"SafeNote — {app.tr('dashboard')}")
        self._action_library.setText(f"📁 {app.tr('library')}")
        self._action_hide.setText(f"🛡️ {app.tr('emergency_hide')}")
        self._action_exit.setText(f"❌ {app.tr('tray_exit') if 'tray_exit' in app.localizer._translations else 'Exit'}")
        self._update_action_rec_text()

    def _update_action_rec_text(self) -> None:
        app = get_app()
        if self._is_recording:
            self._action_toggle_rec.setText(f"⏹ {app.tr('stop_recording')}")
        else:
            self._action_toggle_rec.setText(f"⏺ {app.tr('start_recording')}")

    def update_recording_state(self, is_recording: bool) -> None:
        self._is_recording = is_recording
        self.setIcon(_create_tray_icon(is_recording))
        app = get_app()
        if is_recording:
            self.setToolTip(f"SafeNote — 🔴 {app.tr('recording_active')} (Microphone Active)")
        else:
            self.setToolTip(f"SafeNote — {app.tr('recording_ready')}")
        self._update_action_rec_text()

    def _toggle_recording(self) -> None:
        if self._is_recording:
            self.stop_recording_requested.emit()
        else:
            self.start_recording_requested.emit()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.open_requested.emit()
