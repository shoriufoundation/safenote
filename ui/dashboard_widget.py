"""
SafeNote Dashboard Widget.

Provides an overview of the application state:
- Quick recording start/stop
- Storage and statistics summary cards
- Encryption and privacy status banner
- Recent recordings quick-access list
- Direct navigation triggers
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from audio.recorder import AudioRecorder
from core.application import get_app
from storage.recording_repository import RecordingRepository

logger = logging.getLogger(__name__)


class DashboardWidget(QWidget):
    """
    Main dashboard overview screen.
    """

    navigate_to_recording = Signal()
    navigate_to_library = Signal()
    play_recording_requested = Signal(str)

    def __init__(
        self,
        recorder: AudioRecorder,
        repo: RecordingRepository,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._recorder = recorder
        self._repo = repo
        self._init_ui()
        self.refresh_stats()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(24)

        # Header with App Title & Slogan
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        self._title_label = QLabel("SafeNote")
        self._title_label.setObjectName("title")
        self._subtitle_label = QLabel()
        self._subtitle_label.setObjectName("subtitle")
        title_box.addWidget(self._title_label)
        title_box.addWidget(self._subtitle_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Emergency Hide Button (top right for quick access)
        self._emergency_btn = QPushButton("🛡️ Emergency Lock")
        self._emergency_btn.setObjectName("danger")
        self._emergency_btn.setToolTip("Instantly conceal application (Ctrl+Shift+H)")
        header_layout.addWidget(self._emergency_btn)

        main_layout.addLayout(header_layout)

        # Quick Action Banner
        self._action_card = QFrame()
        self._action_card.setObjectName("card")
        action_layout = QHBoxLayout(self._action_card)
        action_layout.setContentsMargins(24, 20, 24, 20)

        action_text_box = QVBoxLayout()
        self._action_heading = QLabel()
        self._action_heading.setObjectName("heading")
        self._action_desc = QLabel()
        self._action_desc.setObjectName("subtitle")
        action_text_box.addWidget(self._action_heading)
        action_text_box.addWidget(self._action_desc)
        action_layout.addLayout(action_text_box, stretch=1)

        self._quick_record_btn = QPushButton()
        self._quick_record_btn.setObjectName("record")
        self._quick_record_btn.setMinimumHeight(44)
        self._quick_record_btn.setMinimumWidth(180)
        self._quick_record_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._quick_record_btn.clicked.connect(self.navigate_to_recording.emit)
        action_layout.addWidget(self._quick_record_btn)

        main_layout.addWidget(self._action_card)

        # Metric Stats Cards Grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(16)

        # Card 1: Total Recordings
        self._card1 = QFrame()
        self._card1.setObjectName("card")
        c1_layout = QVBoxLayout(self._card1)
        c1_layout.setContentsMargins(20, 16, 20, 16)
        c1_title = QLabel("📁 Total Recordings")
        c1_title.setObjectName("subtitle")
        self._count_label = QLabel("0")
        self._count_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #58a6ff;")
        c1_layout.addWidget(c1_title)
        c1_layout.addWidget(self._count_label)
        stats_grid.addWidget(self._card1, 0, 0)

        # Card 2: Encrypted Storage
        self._card2 = QFrame()
        self._card2.setObjectName("card")
        c2_layout = QVBoxLayout(self._card2)
        c2_layout.setContentsMargins(20, 16, 20, 16)
        c2_title = QLabel("💾 Encrypted Size")
        c2_title.setObjectName("subtitle")
        self._size_label = QLabel("0 KB")
        self._size_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #2ea043;")
        c2_layout.addWidget(c2_title)
        c2_layout.addWidget(self._size_label)
        stats_grid.addWidget(self._card2, 0, 1)

        # Card 3: Security & Privacy
        self._card3 = QFrame()
        self._card3.setObjectName("card")
        c3_layout = QVBoxLayout(self._card3)
        c3_layout.setContentsMargins(20, 16, 20, 16)
        c3_title = QLabel("🔒 Privacy Engine")
        c3_title.setObjectName("subtitle")
        self._sec_label = QLabel("AES-256-GCM")
        self._sec_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #a371f7;")
        c3_note = QLabel("OS Keyring Protected")
        c3_note.setStyleSheet("font-size: 11px; color: #8b949e;")
        c3_layout.addWidget(c3_title)
        c3_layout.addWidget(self._sec_label)
        c3_layout.addWidget(c3_note)
        stats_grid.addWidget(self._card3, 0, 2)

        main_layout.addLayout(stats_grid)

        # Recent Recordings Section
        recent_card = QFrame()
        recent_card.setObjectName("card")
        recent_layout = QVBoxLayout(recent_card)
        recent_layout.setContentsMargins(20, 18, 20, 18)
        recent_layout.setSpacing(12)

        recent_header = QHBoxLayout()
        self._recent_heading = QLabel("Recent Recordings")
        self._recent_heading.setObjectName("heading")
        self._view_all_btn = QPushButton("View All →")
        self._view_all_btn.setStyleSheet("border: none; background: transparent; color: #58a6ff; font-weight: 600;")
        self._view_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._view_all_btn.clicked.connect(self.navigate_to_library.emit)

        recent_header.addWidget(self._recent_heading)
        recent_header.addStretch()
        recent_header.addWidget(self._view_all_btn)
        recent_layout.addLayout(recent_header)

        self._recent_items_box = QVBoxLayout()
        self._recent_items_box.setSpacing(8)
        recent_layout.addLayout(self._recent_items_box)

        main_layout.addWidget(recent_card)
        main_layout.addStretch()

        self.retranslate()
        get_app().language_changed.connect(self.retranslate)

    def retranslate(self) -> None:
        app = get_app()
        self._title_label.setText(app.tr("app_name"))
        self._subtitle_label.setText(app.tr("slogan"))
        self._emergency_btn.setText(f"🛡️ {app.tr('emergency_hide')}")
        self._action_heading.setText(app.tr("recording_ready"))
        self._action_desc.setText(app.tr("emergency_hide_desc"))
        self._quick_record_btn.setText(f"⏺ {app.tr('start_recording')}")

    def refresh_stats(self) -> None:
        """Update dashboard counters and recent recordings list."""
        stats = self._repo.get_storage_stats()
        count = stats.get("total_recordings", 0)
        size_bytes = stats.get("total_size", 0)

        self._count_label.setText(str(count))
        if size_bytes < 1024:
            self._size_label.setText(f"{size_bytes} B")
        elif size_bytes < 1024 * 1024:
            self._size_label.setText(f"{size_bytes / 1024:.1f} KB")
        else:
            self._size_label.setText(f"{size_bytes / (1024 * 1024):.1f} MB")

        # Clear and repopulate recent items
        while self._recent_items_box.count():
            child = self._recent_items_box.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        recordings = self._repo.get_all_recordings()[:4]
        if not recordings:
            empty_lbl = QLabel("No recordings yet. Press 'Start Recording' to create your first encrypted note.")
            empty_lbl.setObjectName("subtitle")
            empty_lbl.setStyleSheet("font-style: italic; color: #8b949e; padding: 12px 0;")
            self._recent_items_box.addWidget(empty_lbl)
        else:
            for rec in recordings:
                row_frame = QFrame()
                row_frame.setStyleSheet("background-color: #161b22; border-radius: 6px; padding: 6px 12px;")
                row_layout = QHBoxLayout(row_frame)
                row_layout.setContentsMargins(8, 6, 8, 6)

                name_lbl = QLabel(rec.get("display_name") or rec.get("filename", ""))
                name_lbl.setStyleSheet("font-weight: 500;")
                date_lbl = QLabel(rec.get("created_at", "")[:10])
                date_lbl.setObjectName("subtitle")
                date_lbl.setStyleSheet("font-size: 11px;")

                play_btn = QPushButton("▶ Play")
                play_btn.setFixedSize(65, 28)
                play_btn.setStyleSheet("font-size: 12px; padding: 2px 6px;")
                path = rec.get("filepath", "")
                play_btn.clicked.connect(lambda checked, p=path: self.play_recording_requested.emit(p))

                row_layout.addWidget(name_lbl, stretch=1)
                row_layout.addWidget(date_lbl)
                row_layout.addSpacing(8)
                row_layout.addWidget(play_btn)
                self._recent_items_box.addWidget(row_frame)
