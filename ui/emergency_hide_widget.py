"""
SafeNote Emergency Hide Widget.

Provides a neutral screen that immediately conceals sensitive application content.
Preserves user data and recordings, providing an obvious documented return mechanism.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.application import get_app


class EmergencyHideWidget(QWidget):
    """
    Emergency Hide privacy screen.
    
    Replaces sensitive recording and library content with a clean,
    neutral display until unlocked by the user.
    """

    unlocked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)

        # Center card container
        card = QFrame()
        card.setObjectName("card")
        card.setFixedSize(480, 360)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(16)

        # Neutral lock icon
        self._icon_label = QLabel("🛡️")
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet("font-size: 48px; background: transparent;")

        # Title
        self._title_label = QLabel()
        self._title_label.setObjectName("heading")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setStyleSheet("font-size: 20px; font-weight: bold;")

        # Description / Notice
        self._desc_label = QLabel()
        self._desc_label.setObjectName("subtitle")
        self._desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._desc_label.setWordWrap(True)

        # Security disclaimer note
        self._note_label = QLabel(
            "Screen privacy mode active. All data remains encrypted.\n"
            "Press the button below or your configured shortcut to return."
        )
        self._note_label.setObjectName("subtitle")
        self._note_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._note_label.setWordWrap(True)
        self._note_label.setStyleSheet("font-size: 11px; color: #6e7681; margin-top: 8px;")

        # Unlock button
        self._unlock_btn = QPushButton()
        self._unlock_btn.setObjectName("primary")
        self._unlock_btn.setMinimumHeight(42)
        self._unlock_btn.setFixedWidth(200)
        self._unlock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._unlock_btn.clicked.connect(self.unlocked.emit)

        card_layout.addWidget(self._icon_label)
        card_layout.addWidget(self._title_label)
        card_layout.addWidget(self._desc_label)
        card_layout.addWidget(self._note_label)
        card_layout.addSpacing(12)
        card_layout.addWidget(self._unlock_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(card)

        self.retranslate()
        get_app().language_changed.connect(self.retranslate)

    def retranslate(self) -> None:
        app = get_app()
        self._title_label.setText(app.tr("workspace_locked"))
        self._desc_label.setText(app.tr("workspace_locked_desc"))
        self._unlock_btn.setText(f"🔓 {app.tr('unlock')}")
