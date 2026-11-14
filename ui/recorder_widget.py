"""
SafeNote Audio Recorder Widget.

Provides full controls for recording audio:
- Microphone device selection
- Sample rate and channel configuration
- Live audio VU level meter
- Elapsed duration display
- High-visibility transparent recording status banner
- Start / Stop controls with error handling
"""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from audio.devices import list_input_devices, get_default_input_device
from audio.recorder import AudioRecorder
from core.application import get_app

logger = logging.getLogger(__name__)


class RecorderWidget(QWidget):
    """
    Dedicated audio recording page.
    """

    recording_started = Signal()
    recording_finished = Signal(str)  # filepath

    def __init__(self, recorder: AudioRecorder, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._recorder = recorder
        self._devices: list[dict] = []
        self._init_ui()
        self._connect_signals()
        self.refresh_devices()

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

        # Status Banner (Recording indicator)
        self._status_banner = QFrame()
        self._status_banner.setObjectName("panel")
        self._status_banner.setStyleSheet(
            "QFrame#panel { background-color: #1a221e; border: 1px solid #238636; border-radius: 8px; }"
        )
        banner_layout = QHBoxLayout(self._status_banner)
        banner_layout.setContentsMargins(16, 12, 16, 12)

        self._status_indicator = QLabel("●")
        self._status_indicator.setStyleSheet("color: #2ea043; font-size: 16px; font-weight: bold;")
        self._status_text = QLabel()
        self._status_text.setStyleSheet("font-weight: 600; font-size: 14px; color: #2ea043;")
        self._mic_info_text = QLabel()
        self._mic_info_text.setObjectName("subtitle")
        self._mic_info_text.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        banner_layout.addWidget(self._status_indicator)
        banner_layout.addWidget(self._status_text)
        banner_layout.addStretch()
        banner_layout.addWidget(self._mic_info_text)
        main_layout.addWidget(self._status_banner)

        # Center recording controls card
        center_card = QFrame()
        center_card.setObjectName("card")
        center_layout = QVBoxLayout(center_card)
        center_layout.setContentsMargins(32, 32, 32, 32)
        center_layout.setSpacing(24)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Large duration timer display
        self._duration_label = QLabel("00:00:00")
        self._duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._duration_label.setStyleSheet(
            "font-size: 48px; font-weight: bold; font-family: monospace; color: #ffffff;"
        )
        center_layout.addWidget(self._duration_label)

        # VU Level Meter
        vu_layout = QVBoxLayout()
        vu_layout.setSpacing(6)
        vu_header = QHBoxLayout()
        self._vu_title = QLabel("Microphone Level")
        self._vu_title.setObjectName("subtitle")
        self._vu_title.setStyleSheet("font-size: 12px;")
        vu_header.addWidget(self._vu_title)
        vu_header.addStretch()
        vu_layout.addLayout(vu_header)

        self._vu_meter = QProgressBar()
        self._vu_meter.setRange(0, 100)
        self._vu_meter.setValue(0)
        self._vu_meter.setTextVisible(False)
        self._vu_meter.setFixedHeight(8)
        self._vu_meter.setStyleSheet(
            "QProgressBar { background-color: #21262d; border-radius: 4px; }"
            "QProgressBar::chunk { background-color: #2ea043; border-radius: 4px; }"
        )
        vu_layout.addWidget(self._vu_meter)
        center_layout.addLayout(vu_layout)

        # Record / Stop Button
        self._record_btn = QPushButton()
        self._record_btn.setObjectName("record")
        self._record_btn.setMinimumHeight(56)
        self._record_btn.setMinimumWidth(260)
        self._record_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._record_btn.clicked.connect(self.toggle_recording)
        center_layout.addWidget(self._record_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(center_card)

        # Device & Audio Configuration Panel
        config_card = QFrame()
        config_card.setObjectName("card")
        config_layout = QGridLayout(config_card)
        config_layout.setContentsMargins(20, 16, 20, 16)
        config_layout.setHorizontalSpacing(16)
        config_layout.setVerticalSpacing(12)

        # Microphone device
        self._device_lbl = QLabel()
        self._device_combo = QComboBox()
        self._device_combo.currentIndexChanged.connect(self._on_device_changed)

        self._refresh_dev_btn = QPushButton("🔄")
        self._refresh_dev_btn.setToolTip("Refresh devices")
        self._refresh_dev_btn.setFixedWidth(40)
        self._refresh_dev_btn.clicked.connect(self.refresh_devices)

        dev_box = QHBoxLayout()
        dev_box.addWidget(self._device_combo, stretch=1)
        dev_box.addWidget(self._refresh_dev_btn)

        # Sample rate
        self._rate_lbl = QLabel()
        self._rate_combo = QComboBox()
        self._rate_combo.addItems(["44100 Hz", "48000 Hz", "22050 Hz", "16000 Hz"])
        self._rate_combo.currentIndexChanged.connect(self._on_audio_param_changed)

        # Channels
        self._channels_lbl = QLabel()
        self._channels_combo = QComboBox()
        self._channels_combo.currentIndexChanged.connect(self._on_audio_param_changed)

        config_layout.addWidget(self._device_lbl, 0, 0)
        config_layout.addLayout(dev_box, 0, 1)
        config_layout.addWidget(self._rate_lbl, 1, 0)
        config_layout.addWidget(self._rate_combo, 1, 1)
        config_layout.addWidget(self._channels_lbl, 2, 0)
        config_layout.addWidget(self._channels_combo, 2, 1)

        main_layout.addWidget(config_card)
        main_layout.addStretch()

        self.retranslate()
        get_app().language_changed.connect(self.retranslate)

    def _connect_signals(self) -> None:
        self._recorder.duration_updated.connect(self._on_duration_updated)
        self._recorder.level_updated.connect(self._on_level_updated)
        self._recorder.recording_error.connect(self._on_recording_error)
        self._recorder.device_disconnected.connect(self._on_device_disconnected)

    def retranslate(self) -> None:
        app = get_app()
        self._page_title.setText(app.tr("recording"))
        self._page_subtitle.setText(app.tr("microphone_active") if self._recorder.is_recording else app.tr("recording_ready"))
        self._device_lbl.setText(app.tr("audio_device"))
        self._rate_lbl.setText(app.tr("sample_rate"))
        self._channels_lbl.setText(app.tr("channels"))

        curr_chan = self._channels_combo.currentIndex()
        self._channels_combo.clear()
        self._channels_combo.addItems([
            f"1 ({app.tr('mono')})",
            f"2 ({app.tr('stereo')})",
        ])
        if curr_chan >= 0:
            self._channels_combo.setCurrentIndex(curr_chan)

        self._vu_title.setText(app.tr("audio_level"))
        self._update_status_ui()

    def refresh_devices(self) -> None:
        """Scan and populate available input devices."""
        self._device_combo.blockSignals(True)
        self._device_combo.clear()
        try:
            self._devices = list_input_devices()
            if not self._devices:
                self._device_combo.addItem(get_app().tr("no_microphone"), None)
            else:
                for dev in self._devices:
                    label = dev["name"]
                    if dev.get("is_default"):
                        label += " ★"
                    self._device_combo.addItem(label, dev["id"])
        except Exception as exc:
            logger.exception("Error listing audio devices")
            self._device_combo.addItem("Default Device", None)
        self._device_combo.blockSignals(False)

    def _on_device_changed(self) -> None:
        dev_id = self._device_combo.currentData()
        self._apply_audio_config()

    def _on_audio_param_changed(self) -> None:
        self._apply_audio_config()

    def _apply_audio_config(self) -> None:
        dev_id = self._device_combo.currentData()
        rate_str = self._rate_combo.currentText().split()[0]
        try:
            rate = int(rate_str)
        except ValueError:
            rate = 44100
        channels = 1 if self._channels_combo.currentIndex() <= 0 else 2
        self._recorder.configure(sample_rate=rate, channels=channels, device_id=dev_id)

    def toggle_recording(self) -> None:
        if not self._recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self) -> bool:
        if self._recorder.is_recording:
            return False

        self._apply_audio_config()
        app = get_app()
        storage_dir = app.config.get_storage_directory()

        from crypto.key_manager import get_or_create_key
        try:
            key = get_or_create_key()
        except Exception as exc:
            QMessageBox.critical(self, app.tr("error"), f"Key retrieval failed: {exc}")
            return False

        if self._recorder.start(storage_dir=storage_dir, key=key):
            self._update_status_ui()
            self._device_combo.setEnabled(False)
            self._rate_combo.setEnabled(False)
            self._channels_combo.setEnabled(False)
            self.recording_started.emit()
            return True
        else:
            err = self._recorder.error or "Failed to start recording."
            QMessageBox.critical(self, app.tr("error"), err)
            return False

    def stop_recording(self) -> Optional[str]:
        if not self._recorder.is_recording:
            return None

        try:
            path = self._recorder.stop()
            self._update_status_ui()
            self._device_combo.setEnabled(True)
            self._rate_combo.setEnabled(True)
            self._channels_combo.setEnabled(True)
            self._vu_meter.setValue(0)

            if path:
                self.recording_finished.emit(path)
                QMessageBox.information(
                    self,
                    get_app().tr("recording_saved"),
                    f"{get_app().tr('file_saved')}:\n{path}"
                )
            return path
        except Exception as exc:
            self._update_status_ui()
            self._device_combo.setEnabled(True)
            self._rate_combo.setEnabled(True)
            self._channels_combo.setEnabled(True)
            QMessageBox.critical(self, get_app().tr("error"), str(exc))
            return None

    def _update_status_ui(self) -> None:
        app = get_app()
        if self._recorder.is_recording:
            self._status_banner.setStyleSheet(
                "QFrame#panel { background-color: #2b1d1d; border: 1px solid #da3633; border-radius: 8px; }"
            )
            self._status_indicator.setStyleSheet("color: #f85149; font-size: 16px; font-weight: bold;")
            self._status_text.setStyleSheet("font-weight: 600; font-size: 14px; color: #f85149;")
            self._status_text.setText(f"● {app.tr('recording_active')}")
            self._mic_info_text.setText(f"🎤 {app.tr('microphone_active')}")
            self._record_btn.setText(f"⏹  {app.tr('stop_recording')}")
            self._record_btn.setObjectName("record_stop")
        else:
            self._status_banner.setStyleSheet(
                "QFrame#panel { background-color: #1a221e; border: 1px solid #238636; border-radius: 8px; }"
            )
            self._status_indicator.setStyleSheet("color: #2ea043; font-size: 16px; font-weight: bold;")
            self._status_text.setStyleSheet("font-weight: 600; font-size: 14px; color: #2ea043;")
            self._status_text.setText(f"● {app.tr('recording_ready')}")
            self._mic_info_text.setText("")
            self._record_btn.setText(f"⏺  {app.tr('start_recording')}")
            self._record_btn.setObjectName("record")
            self._duration_label.setText("00:00:00")

        self._record_btn.style().unpolish(self._record_btn)
        self._record_btn.style().polish(self._record_btn)

    def _on_duration_updated(self, seconds: float) -> None:
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        self._duration_label.setText(f"{hrs:02d}:{mins:02d}:{secs:02d}")

    def _on_level_updated(self, level: float) -> None:
        # Scale to 0..100
        val = int(min(max(level * 100, 0), 100))
        self._vu_meter.setValue(val)
        # Dynamic color for VU meter
        if val > 80:
            color = "#f85149"
        elif val > 50:
            color = "#d29922"
        else:
            color = "#2ea043"
        self._vu_meter.setStyleSheet(
            f"QProgressBar {{ background-color: #21262d; border-radius: 4px; }}"
            f"QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}"
        )

    def _on_recording_error(self, err: str) -> None:
        QMessageBox.critical(self, get_app().tr("error"), err)
        self._update_status_ui()

    def _on_device_disconnected(self) -> None:
        QMessageBox.warning(self, get_app().tr("warning"), get_app().tr("microphone_disconnected"))
        self.refresh_devices()
