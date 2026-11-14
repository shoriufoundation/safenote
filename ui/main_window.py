"""
SafeNote Main Application Window.

Implements the complete desktop user interface:
- Modern sidebar navigation (Dashboard, Record, Library, Player, Settings, About)
- Responsive stacked page layout
- Emergency Hide privacy screen with hotkey (Ctrl+Shift+H)
- Configurable keyboard shortcuts
- Audio recording & in-memory playback integration
- System tray integration
- First-run onboarding wizard
- Dynamic dark / light theming
- Multi-language localization (Turkish, English, Azerbaijani)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from audio.player import AudioPlayer
from audio.recorder import AudioRecorder
from core.application import get_app
from storage.recording_repository import RecordingRepository
from ui.about_widget import AboutWidget
from ui.dashboard_widget import DashboardWidget
from ui.emergency_hide_widget import EmergencyHideWidget
from ui.first_run_dialog import FirstRunWizard
from ui.library_widget import LibraryWidget
from ui.player_widget import PlayerWidget
from ui.recorder_widget import RecorderWidget
from ui.settings_widget import SettingsWidget
from ui.tray import SafeNoteTrayIcon

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    SafeNote Main Window.
    """

    # Page indices
    PAGE_DASHBOARD = 0
    PAGE_RECORDING = 1
    PAGE_LIBRARY = 2
    PAGE_PLAYER = 3
    PAGE_SETTINGS = 4
    PAGE_ABOUT = 5
    PAGE_EMERGENCY = 6

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("SafeNote")
        self.setMinimumSize(880, 580)
        self.resize(1020, 680)

        # Core engine components
        self._app_mgr = get_app()
        self._recorder = AudioRecorder(self)
        self._player = AudioPlayer(self)
        self._repo = RecordingRepository(
            storage_dir=self._app_mgr.config.get_storage_directory()
        )

        self._is_emergency_locked = False
        self._prev_page_idx = self.PAGE_DASHBOARD

        self._init_ui()
        self._setup_shortcuts()
        self._setup_tray()
        self._connect_signals()
        self._apply_theme()

        # Check for first-run
        if self._app_mgr.config.is_first_run():
            wizard = FirstRunWizard(self)
            wizard.exec()
            self._repo = RecordingRepository(
                storage_dir=self._app_mgr.config.get_storage_directory()
            )
            self._apply_theme()

    def _init_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────
        self._sidebar = QFrame()
        self._sidebar.setObjectName("sidebar")
        sb_layout = QVBoxLayout(self._sidebar)
        sb_layout.setContentsMargins(12, 16, 12, 16)
        sb_layout.setSpacing(8)

        # Brand / Logo Header
        brand_box = QHBoxLayout()
        brand_box.setContentsMargins(8, 6, 8, 12)
        brand_icon = QLabel("🛡️")
        brand_icon.setStyleSheet("font-size: 20px;")
        self._brand_title = QLabel("SafeNote")
        self._brand_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        brand_box.addWidget(brand_icon)
        brand_box.addWidget(self._brand_title)
        brand_box.addStretch()
        sb_layout.addLayout(brand_box)

        # Nav Buttons
        self._nav_buttons: list[QPushButton] = []

        self._btn_nav_dash = QPushButton("📊  Dashboard")
        self._btn_nav_rec = QPushButton("🎙️  Recording")
        self._btn_nav_lib = QPushButton("📁  Library")
        self._btn_nav_player = QPushButton("▶️  Player")
        self._btn_nav_settings = QPushButton("⚙️  Settings")
        self._btn_nav_about = QPushButton("ℹ️  About")

        nav_items = [
            (self._btn_nav_dash, self.PAGE_DASHBOARD),
            (self._btn_nav_rec, self.PAGE_RECORDING),
            (self._btn_nav_lib, self.PAGE_LIBRARY),
            (self._btn_nav_player, self.PAGE_PLAYER),
            (self._btn_nav_settings, self.PAGE_SETTINGS),
            (self._btn_nav_about, self.PAGE_ABOUT),
        ]

        for btn, page_idx in nav_items:
            btn.setObjectName("nav_button")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=page_idx: self.navigate_to(idx))
            sb_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sb_layout.addStretch()

        # Status badge at bottom of sidebar
        self._sidebar_status = QLabel("● Ready")
        self._sidebar_status.setStyleSheet("color: #2ea043; font-weight: 600; font-size: 12px; padding: 6px 12px;")
        sb_layout.addWidget(self._sidebar_status)

        # Emergency Hide Button (Sidebar footer)
        self._sidebar_emergency_btn = QPushButton("🛡️  Emergency Hide")
        self._sidebar_emergency_btn.setObjectName("danger")
        self._sidebar_emergency_btn.setMinimumHeight(38)
        self._sidebar_emergency_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._sidebar_emergency_btn.clicked.connect(self.trigger_emergency_hide)
        sb_layout.addWidget(self._sidebar_emergency_btn)

        main_layout.addWidget(self._sidebar)

        # ── Stacked Pages Container ──────────────────────────────────
        self._stack = QStackedWidget()

        self._page_dashboard = DashboardWidget(self._recorder, self._repo, self)
        self._page_recorder = RecorderWidget(self._recorder, self)
        self._page_library = LibraryWidget(self._repo, self)
        self._page_player = PlayerWidget(self._player, self)
        self._page_settings = SettingsWidget(self)
        self._page_about = AboutWidget(self)
        self._page_emergency = EmergencyHideWidget(self)

        self._stack.addWidget(self._page_dashboard)    # Index 0
        self._stack.addWidget(self._page_recorder)     # Index 1
        self._stack.addWidget(self._page_library)      # Index 2
        self._stack.addWidget(self._page_player)       # Index 3
        self._stack.addWidget(self._page_settings)     # Index 4
        self._stack.addWidget(self._page_about)        # Index 5
        self._stack.addWidget(self._page_emergency)    # Index 6

        main_layout.addWidget(self._stack, stretch=1)

        self.navigate_to(self.PAGE_DASHBOARD)
        self.retranslate()

    def _setup_shortcuts(self) -> None:
        cfg = self._app_mgr.config
        em_sh_str = cfg.get_emergency_hide_shortcut() or "Ctrl+Shift+H"
        rec_sh_str = cfg.get_record_shortcut() or "Ctrl+R"

        self._shortcut_emergency = QShortcut(QKeySequence(em_sh_str), self)
        self._shortcut_emergency.activated.connect(self.trigger_emergency_hide)

        self._shortcut_record = QShortcut(QKeySequence(rec_sh_str), self)
        self._shortcut_record.activated.connect(self._toggle_recording)

    def _setup_tray(self) -> None:
        self._tray = SafeNoteTrayIcon(self)
        self._tray.open_requested.connect(self._restore_from_tray)
        self._tray.start_recording_requested.connect(self._start_recording)
        self._tray.stop_recording_requested.connect(self._stop_recording)
        self._tray.open_library_requested.connect(lambda: self.navigate_to(self.PAGE_LIBRARY))
        self._tray.emergency_hide_requested.connect(self.trigger_emergency_hide)
        self._tray.exit_requested.connect(self._clean_exit)
        self._tray.show()

    def _connect_signals(self) -> None:
        self._app_mgr.language_changed.connect(self.retranslate)
        self._app_mgr.theme_changed.connect(self._apply_theme)

        # Dashboard navigation signals
        self._page_dashboard.navigate_to_recording.connect(lambda: self.navigate_to(self.PAGE_RECORDING))
        self._page_dashboard.navigate_to_library.connect(lambda: self.navigate_to(self.PAGE_LIBRARY))
        self._page_dashboard.play_recording_requested.connect(self._play_file)
        self._page_dashboard._emergency_btn.clicked.connect(self.trigger_emergency_hide)

        # Library navigation to player
        self._page_library.play_requested.connect(self._play_file)

        # Recorder updates
        self._page_recorder.recording_finished.connect(self._on_recording_saved)
        self._recorder.recording_started.connect(self._on_recording_started)
        self._recorder.recording_stopped.connect(self._on_recording_stopped)

        # Emergency unlock
        self._page_emergency.unlocked.connect(self.unlock_emergency_hide)

        # Settings changed
        self._page_settings.settings_updated.connect(self._on_settings_updated)

    def _apply_theme(self) -> None:
        stylesheet = self._app_mgr.get_theme_stylesheet()
        self.setStyleSheet(stylesheet)

    def retranslate(self) -> None:
        app = self._app_mgr
        self._btn_nav_dash.setText(f"📊  {app.tr('dashboard')}")
        self._btn_nav_rec.setText(f"🎙️  {app.tr('recording')}")
        self._btn_nav_lib.setText(f"📁  {app.tr('library')}")
        self._btn_nav_player.setText(f"▶️  {app.tr('player')}")
        self._btn_nav_settings.setText(f"⚙️  {app.tr('settings')}")
        self._btn_nav_about.setText(f"ℹ️  {app.tr('about')}")
        self._sidebar_emergency_btn.setText(f"🛡️  {app.tr('emergency_hide')}")
        self._update_status_ui()

    def navigate_to(self, page_index: int) -> None:
        """Switch active page in the main window."""
        if self._is_emergency_locked and page_index != self.PAGE_EMERGENCY:
            return

        self._stack.setCurrentIndex(page_index)

        # Update active nav button state
        for idx, btn in enumerate(self._nav_buttons):
            is_active = (idx == page_index)
            btn.setProperty("active", "true" if is_active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Refresh page data if applicable
        if page_index == self.PAGE_DASHBOARD:
            self._page_dashboard.refresh_stats()
        elif page_index == self.PAGE_LIBRARY:
            self._page_library.refresh_library()

    def _play_file(self, path: str) -> None:
        self.navigate_to(self.PAGE_PLAYER)
        self._page_player.load_recording(path)
        self._page_player._player.play()

    def _toggle_recording(self) -> None:
        self._page_recorder.toggle_recording()

    def _start_recording(self) -> None:
        self.navigate_to(self.PAGE_RECORDING)
        self._page_recorder.start_recording()

    def _stop_recording(self) -> None:
        self._page_recorder.stop_recording()

    def _on_recording_started(self) -> None:
        self._tray.update_recording_state(True)
        self._update_status_ui()

    def _on_recording_stopped(self, path: str) -> None:
        self._tray.update_recording_state(False)
        self._update_status_ui()

    def _on_recording_saved(self, path: str) -> None:
        p = Path(path)
        try:
            metadata = {
                "sample_rate": self._app_mgr.config.get_sample_rate(),
                "channels": self._app_mgr.config.get_channels(),
                "duration_seconds": self._recorder.duration,
            }
            self._repo.register_recording(path, metadata)
            self._page_dashboard.refresh_stats()
            self._page_library.refresh_library()
        except Exception as exc:
            logger.exception("Failed to register recording in database: %s", exc)

    def _update_status_ui(self) -> None:
        app = self._app_mgr
        if self._recorder.is_recording:
            self._sidebar_status.setText(f"● {app.tr('recording_active')}")
            self._sidebar_status.setStyleSheet("color: #f85149; font-weight: bold; font-size: 12px; padding: 6px 12px;")
        else:
            self._sidebar_status.setText(f"● {app.tr('status_ready') if 'status_ready' in app.localizer._translations else 'Ready'}")
            self._sidebar_status.setStyleSheet("color: #2ea043; font-weight: 600; font-size: 12px; padding: 6px 12px;")

    # ── Emergency Hide Implementation ─────────────────────────────────

    def trigger_emergency_hide(self) -> None:
        """
        Instantly conceal sensitive application content.
        Safely stops active recording before hiding sensitive content.
        """
        if self._is_emergency_locked:
            return

        # Safely finalize any active recording
        if self._recorder.is_recording:
            try:
                self._recorder.stop()
            except Exception as exc:
                logger.error("Emergency hide stopped active recording with error: %s", exc)

        # Stop audio playback
        if self._player.is_playing():
            self._player.stop()

        self._prev_page_idx = self._stack.currentIndex()
        self._is_emergency_locked = True
        self._sidebar.hide()
        self.navigate_to(self.PAGE_EMERGENCY)
        self.show()
        self.activateWindow()

    def unlock_emergency_hide(self) -> None:
        """Restore normal interface view after emergency lock."""
        self._is_emergency_locked = False
        self._sidebar.show()
        target_page = self._prev_page_idx if self._prev_page_idx != self.PAGE_EMERGENCY else self.PAGE_DASHBOARD
        self.navigate_to(target_page)

    def _on_settings_updated(self) -> None:
        # Re-register shortcuts in case they changed
        self._setup_shortcuts()
        self._repo = RecordingRepository(
            storage_dir=self._app_mgr.config.get_storage_directory()
        )

    def _restore_from_tray(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def _clean_exit(self) -> None:
        if self._recorder.is_recording:
            self._recorder.stop()
        if self._player.is_playing():
            self._player.stop()
        self._repo.close()
        self._tray.hide()
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        # Check start_minimized / close behavior
        if self._app_mgr.config.get_start_minimized():
            self.hide()
            event.ignore()
        else:
            if self._recorder.is_recording:
                reply = QMessageBox.question(
                    self,
                    "Active Recording",
                    "A recording is currently in progress. Stop and save recording before exiting?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self._recorder.stop()
            self._clean_exit()
            event.accept()
