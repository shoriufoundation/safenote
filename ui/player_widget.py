"""
SafeNote Audio Player Widget.

Provides full controls for decrypting and playing SafeNote recordings:
- Decrypts in-memory (no plaintext file on disk)
- Play, pause, resume, stop
- Seekable timeline slider
- Volume slider and mute toggle
- Jump forward / backward (+/- 5 seconds)
- Duration and position indicators
- Metadata display (sample rate, channels, created time, size)
- Error handling for wrong keys and corrupted files
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from audio.player import AudioPlayer, PlayerState
from core.application import get_app
from crypto.key_manager import get_or_create_key

logger = logging.getLogger(__name__)


def _format_time(seconds: float) -> str:
    """Format seconds into MM:SS or HH:MM:SS."""
    sec = max(0, int(seconds))
    hrs = sec // 3600
    mins = (sec % 3600) // 60
    s = sec % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{s:02d}"
    return f"{mins:02d}:{s:02d}"


class PlayerWidget(QWidget):
    """
    Audio playback UI page.
    """

    def __init__(self, player: AudioPlayer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._player = player
        self._current_path: Optional[str] = None
        self._is_scrubbing: bool = False
        self._duration: float = 0.0

        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(20)

        # Header section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        self._page_title = QLabel()
        self._page_title.setObjectName("title")
        self._page_subtitle = QLabel()
        self._page_subtitle.setObjectName("subtitle")
        header_layout.addWidget(self._page_title)
        header_layout.addWidget(self._page_subtitle)
        main_layout.addLayout(header_layout)

        # Now Playing Card
        now_playing_card = QFrame()
        now_playing_card.setObjectName("card")
        np_layout = QVBoxLayout(now_playing_card)
        np_layout.setContentsMargins(28, 24, 28, 24)
        np_layout.setSpacing(16)

        # File info banner
        file_header = QHBoxLayout()
        self._file_name_label = QLabel("No recording loaded")
        self._file_name_label.setObjectName("heading")
        self._file_name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._open_btn = QPushButton("📂 Open .sna...")
        self._open_btn.clicked.connect(self._browse_and_open)

        file_header.addWidget(self._file_name_label, stretch=1)
        file_header.addWidget(self._open_btn)
        np_layout.addLayout(file_header)

        # Metadata chip / info
        self._meta_label = QLabel("Select an encrypted recording to play")
        self._meta_label.setObjectName("subtitle")
        self._meta_label.setStyleSheet("font-size: 12px; color: #8b949e;")
        np_layout.addWidget(self._meta_label)

        np_layout.addSpacing(8)

        # Timeline and Sliders
        timeline_layout = QVBoxLayout()
        timeline_layout.setSpacing(4)

        self._seek_slider = QSlider(Qt.Orientation.Horizontal)
        self._seek_slider.setRange(0, 1000)
        self._seek_slider.setValue(0)
        self._seek_slider.setEnabled(False)
        self._seek_slider.sliderPressed.connect(self._on_seek_pressed)
        self._seek_slider.sliderReleased.connect(self._on_seek_released)
        self._seek_slider.sliderMoved.connect(self._on_seek_moved)

        time_labels = QHBoxLayout()
        self._pos_label = QLabel("00:00")
        self._pos_label.setStyleSheet("font-family: monospace; font-size: 12px;")
        self._dur_label = QLabel("00:00")
        self._dur_label.setStyleSheet("font-family: monospace; font-size: 12px;")
        time_labels.addWidget(self._pos_label)
        time_labels.addStretch()
        time_labels.addWidget(self._dur_label)

        timeline_layout.addWidget(self._seek_slider)
        timeline_layout.addLayout(time_labels)
        np_layout.addLayout(timeline_layout)

        # Transport Controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._btn_back5 = QPushButton("⏪ -5s")
        self._btn_back5.setFixedWidth(70)
        self._btn_back5.clicked.connect(lambda: self._seek_relative(-5.0))
        self._btn_back5.setEnabled(False)

        self._btn_play = QPushButton("▶ Play")
        self._btn_play.setObjectName("primary")
        self._btn_play.setMinimumWidth(110)
        self._btn_play.setMinimumHeight(40)
        self._btn_play.clicked.connect(self._toggle_play)
        self._btn_play.setEnabled(False)

        self._btn_stop = QPushButton("⏹ Stop")
        self._btn_stop.setMinimumWidth(80)
        self._btn_stop.setMinimumHeight(40)
        self._btn_stop.clicked.connect(self._player.stop)
        self._btn_stop.setEnabled(False)

        self._btn_fwd5 = QPushButton("+5s ⏩")
        self._btn_fwd5.setFixedWidth(70)
        self._btn_fwd5.clicked.connect(lambda: self._seek_relative(5.0))
        self._btn_fwd5.setEnabled(False)

        controls_layout.addWidget(self._btn_back5)
        controls_layout.addWidget(self._btn_play)
        controls_layout.addWidget(self._btn_stop)
        controls_layout.addWidget(self._btn_fwd5)
        np_layout.addLayout(controls_layout)

        # Volume control bar
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(8)
        self._vol_icon = QLabel("🔊")
        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(100)
        self._vol_slider.setFixedWidth(140)
        self._vol_slider.valueChanged.connect(self._on_volume_changed)
        self._vol_label = QLabel("100%")
        self._vol_label.setFixedWidth(40)
        self._vol_label.setStyleSheet("font-size: 11px; color: #8b949e;")

        volume_layout.addStretch()
        volume_layout.addWidget(self._vol_icon)
        volume_layout.addWidget(self._vol_slider)
        volume_layout.addWidget(self._vol_label)
        volume_layout.addStretch()
        np_layout.addLayout(volume_layout)

        main_layout.addWidget(now_playing_card)

        # Security info card
        sec_card = QFrame()
        sec_card.setObjectName("card")
        sec_layout = QHBoxLayout(sec_card)
        sec_layout.setContentsMargins(16, 12, 16, 12)
        sec_icon = QLabel("🔒")
        sec_icon.setStyleSheet("font-size: 20px;")
        sec_text = QLabel(
            "Privacy guarantee: Decryption occurs entirely in memory. "
            "No temporary unencrypted audio files are written to disk during playback."
        )
        sec_text.setObjectName("subtitle")
        sec_text.setWordWrap(True)
        sec_layout.addWidget(sec_icon)
        sec_layout.addWidget(sec_text, stretch=1)
        main_layout.addWidget(sec_card)

        main_layout.addStretch()

        self.retranslate()
        get_app().language_changed.connect(self.retranslate)

    def _connect_signals(self) -> None:
        self._player.playback_started.connect(self._on_playback_started)
        self._player.playback_paused.connect(self._on_playback_paused)
        self._player.playback_resumed.connect(self._on_playback_resumed)
        self._player.playback_stopped.connect(self._on_playback_stopped)
        self._player.playback_finished.connect(self._on_playback_finished)
        self._player.position_changed.connect(self._on_position_changed)
        self._player.duration_available.connect(self._on_duration_available)
        self._player.error_occurred.connect(self._on_player_error)

    def retranslate(self) -> None:
        app = get_app()
        self._page_title.setText(app.tr("player"))
        self._page_subtitle.setText(app.tr("audio_player_subtitle") if "audio_player_subtitle" in app.localizer._translations else "In-memory playback for encrypted recordings")
        if self._current_path is None:
            self._file_name_label.setText(app.tr("no_recording_loaded"))
            self._meta_label.setText(app.tr("select_recording"))
        self._open_btn.setText(f"📂 {app.tr('browse')}...")
        self._update_play_button_text()

    def _browse_and_open(self) -> None:
        app = get_app()
        initial_dir = app.config.get_storage_directory()
        path, _ = QFileDialog.getOpenFileName(
            self,
            app.tr("open_recording"),
            initial_dir,
            "SafeNote Recordings (*.sna);;All Files (*.*)"
        )
        if path:
            self.load_recording(path)

    def load_recording(self, path: str) -> bool:
        """Load and decrypt an encrypted .sna file into memory."""
        self._current_path = path
        p = Path(path)
        self._file_name_label.setText(p.name)

        app = get_app()
        try:
            key = get_or_create_key()
        except Exception as exc:
            QMessageBox.critical(self, app.tr("error"), f"Key retrieval error: {exc}")
            return False

        self._player.load_file(path, key)
        self._meta_label.setText(f"Path: {p.parent} • Size: {p.stat().st_size:,} bytes")
        self._seek_slider.setEnabled(True)
        self._btn_play.setEnabled(True)
        self._btn_stop.setEnabled(True)
        self._btn_back5.setEnabled(True)
        self._btn_fwd5.setEnabled(True)
        self._update_play_button_text()
        return True

    def _toggle_play(self) -> None:
        if self._player.is_playing():
            self._player.pause()
        else:
            self._player.play()

    def _update_play_button_text(self) -> None:
        app = get_app()
        if self._player.is_playing():
            self._btn_play.setText(f"⏸ {app.tr('pause')}")
            self._btn_play.setObjectName("")
        else:
            self._btn_play.setText(f"▶ {app.tr('play')}")
            self._btn_play.setObjectName("primary")
        self._btn_play.style().unpolish(self._btn_play)
        self._btn_play.style().polish(self._btn_play)

    def _on_playback_started(self) -> None:
        self._update_play_button_text()

    def _on_playback_paused(self) -> None:
        self._update_play_button_text()

    def _on_playback_resumed(self) -> None:
        self._update_play_button_text()

    def _on_playback_stopped(self) -> None:
        self._update_play_button_text()
        self._seek_slider.setValue(0)
        self._pos_label.setText("00:00")

    def _on_playback_finished(self) -> None:
        self._update_play_button_text()
        self._seek_slider.setValue(0)
        self._pos_label.setText("00:00")

    def _on_duration_available(self, duration: float) -> None:
        self._duration = duration
        self._dur_label.setText(_format_time(duration))

    def _on_position_changed(self, pos: float) -> None:
        if self._is_scrubbing:
            return
        self._pos_label.setText(_format_time(pos))
        if self._duration > 0:
            ratio = min(max(pos / self._duration, 0.0), 1.0)
            self._seek_slider.blockSignals(True)
            self._seek_slider.setValue(int(ratio * 1000))
            self._seek_slider.blockSignals(False)

    def _on_seek_pressed(self) -> None:
        self._is_scrubbing = True

    def _on_seek_moved(self, value: int) -> None:
        if self._duration > 0:
            target = (value / 1000.0) * self._duration
            self._pos_label.setText(_format_time(target))

    def _on_seek_released(self) -> None:
        self._is_scrubbing = False
        if self._duration > 0:
            target = (self._seek_slider.value() / 1000.0) * self._duration
            self._player.seek(target)

    def _seek_relative(self, delta: float) -> None:
        new_pos = max(0.0, min(self._player.get_position() + delta, self._duration))
        self._player.seek(new_pos)

    def _on_volume_changed(self, val: int) -> None:
        self._player.set_volume(val / 100.0)
        self._vol_label.setText(f"{val}%")
        if val == 0:
            self._vol_icon.setText("🔇")
        elif val < 50:
            self._vol_icon.setText("🔉")
        else:
            self._vol_icon.setText("🔊")

    def _on_player_error(self, err: str) -> None:
        QMessageBox.critical(self, get_app().tr("error"), err)
