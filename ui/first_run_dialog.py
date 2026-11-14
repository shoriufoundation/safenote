"""
SafeNote First-Run Setup Wizard Dialog.

Guides new users through initial preferences:
- Preferred language (Turkish, English, Azerbaijani)
- Storage directory selection
- Theme selection (Dark / Light)
- Startup & update checking preferences
- Keyboard shortcuts summary
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.application import get_app
from core.localization import LANGUAGE_NAMES

logger = logging.getLogger(__name__)


class FirstRunWizard(QDialog):
    """
    First-run setup wizard dialog.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("SafeNote Setup Wizard")
        self.setFixedSize(560, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Step stack
        self._stack = QStackedWidget()

        # Step 0: Welcome & Language
        self._stack.addWidget(self._build_step_welcome())

        # Step 1: Storage & Theme
        self._stack.addWidget(self._build_step_storage())

        # Step 2: Startup & Privacy
        self._stack.addWidget(self._build_step_startup())

        # Step 3: Finish
        self._stack.addWidget(self._build_step_finish())

        main_layout.addWidget(self._stack, stretch=1)

        # Navigation Bar
        nav_layout = QHBoxLayout()
        self._step_indicator = QLabel("Step 1 of 4")
        self._step_indicator.setObjectName("subtitle")
        nav_layout.addWidget(self._step_indicator)
        nav_layout.addStretch()

        self._btn_back = QPushButton("← Back")
        self._btn_back.clicked.connect(self._prev_step)
        self._btn_back.setEnabled(False)

        self._btn_next = QPushButton("Next →")
        self._btn_next.setObjectName("primary")
        self._btn_next.clicked.connect(self._next_step)

        nav_layout.addWidget(self._btn_back)
        nav_layout.addWidget(self._btn_next)
        main_layout.addLayout(nav_layout)

    def _build_step_welcome(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        title = QLabel("🛡️ Welcome to SafeNote")
        title.setObjectName("title")
        subtitle = QLabel("Your safety. Your privacy. Your choice.\nLet's configure your basic preferences.")
        subtitle.setObjectName("subtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)

        lang_card = QFrame()
        lang_card.setObjectName("card")
        l_layout = QVBoxLayout(lang_card)
        l_layout.setSpacing(8)

        lbl = QLabel("Select your preferred language / Dil seçin:")
        lbl.setStyleSheet("font-weight: 600;")
        self._combo_lang = QComboBox()
        for code, name in LANGUAGE_NAMES.items():
            self._combo_lang.addItem(f"{name} ({code})", code)

        self._combo_lang.currentIndexChanged.connect(self._on_lang_changed)

        l_layout.addWidget(lbl)
        l_layout.addWidget(self._combo_lang)
        layout.addWidget(lang_card)

        layout.addStretch()
        return widget

    def _build_step_storage(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        title = QLabel("Storage & Appearance")
        title.setObjectName("heading")
        layout.addWidget(title)

        # Storage Card
        s_card = QFrame()
        s_card.setObjectName("card")
        s_layout = QVBoxLayout(s_card)
        s_layout.setSpacing(8)

        lbl_s = QLabel("Recordings Storage Directory:")
        lbl_s.setStyleSheet("font-weight: 600;")
        self._edit_storage = QLineEdit()
        default_dir = str(Path.home() / "SafeNote" / "Recordings")
        self._edit_storage.setText(default_dir)

        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse_dir)

        s_box = QHBoxLayout()
        s_box.addWidget(self._edit_storage, stretch=1)
        s_box.addWidget(btn_browse)

        s_layout.addWidget(lbl_s)
        s_layout.addLayout(s_box)
        layout.addWidget(s_card)

        # Theme Card
        t_card = QFrame()
        t_card.setObjectName("card")
        t_layout = QVBoxLayout(t_card)
        t_layout.setSpacing(8)

        lbl_t = QLabel("Choose Theme:")
        lbl_t.setStyleSheet("font-weight: 600;")
        self._combo_theme = QComboBox()
        self._combo_theme.addItems(["Dark (Recommended)", "Light"])
        t_layout.addWidget(lbl_t)
        t_layout.addWidget(self._combo_theme)
        layout.addWidget(t_card)

        layout.addStretch()
        return widget

    def _build_step_startup(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        title = QLabel("Startup & Updates")
        title.setObjectName("heading")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("card")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(12)

        self._chk_autostart = QCheckBox("Start SafeNote when Windows starts")
        self._chk_minimized = QCheckBox("Start minimized to the system tray")
        self._chk_updates = QCheckBox("Check for application updates on launch")
        self._chk_updates.setChecked(True)

        c_layout.addWidget(self._chk_autostart)
        c_layout.addWidget(self._chk_minimized)
        c_layout.addWidget(self._chk_updates)
        layout.addWidget(card)

        note = QLabel(
            "Privacy Reminder: SafeNote never downloads or installs updates silently.\n"
            "All network queries are strictly opt-in."
        )
        note.setObjectName("subtitle")
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addStretch()
        return widget

    def _build_step_finish(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        title = QLabel("🎉 Setup Complete!")
        title.setObjectName("heading")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("card")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(10)

        info = QLabel(
            "Quick Reference:\n\n"
            "• 🛡️ Emergency Hide: Press Ctrl+Shift+H anytime to instantly lock the screen.\n"
            "• 🎙️ Quick Record: Press Ctrl+R to start/stop recording.\n"
            "• 🔒 Safe Storage: Recordings are encrypted with AES-256-GCM.\n\n"
            "You can adjust these settings at any time from the Settings page."
        )
        info.setWordWrap(True)
        info.setStyleSheet("line-height: 1.5;")
        c_layout.addWidget(info)
        layout.addWidget(card)

        layout.addStretch()
        return widget

    def _on_lang_changed(self, idx: int) -> None:
        code = self._combo_lang.itemData(idx)
        if code:
            get_app().change_language(code)

    def _browse_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Directory", self._edit_storage.text())
        if path:
            self._edit_storage.setText(path)

    def _prev_step(self) -> None:
        idx = self._stack.currentIndex()
        if idx > 0:
            self._stack.setCurrentIndex(idx - 1)
            self._update_nav(idx - 1)

    def _next_step(self) -> None:
        idx = self._stack.currentIndex()
        if idx < self._stack.count() - 1:
            self._stack.setCurrentIndex(idx + 1)
            self._update_nav(idx + 1)
        else:
            self._save_and_finish()

    def _update_nav(self, idx: int) -> None:
        total = self._stack.count()
        self._step_indicator.setText(f"Step {idx + 1} of {total}")
        self._btn_back.setEnabled(idx > 0)
        if idx == total - 1:
            self._btn_next.setText("Finish ✓")
        else:
            self._btn_next.setText("Next →")

    def _save_and_finish(self) -> None:
        app = get_app()
        cfg = app.config

        # Storage
        storage_path = self._edit_storage.text().strip()
        if storage_path:
            cfg.set_storage_directory(storage_path)

        # Theme
        theme = "light" if self._combo_theme.currentIndex() == 1 else "dark"
        app.change_theme(theme)

        # Startup
        cfg.set_auto_start(self._chk_autostart.isChecked())
        cfg.set_start_minimized(self._chk_minimized.isChecked())
        cfg.set_check_updates(self._chk_updates.isChecked())

        # First run complete
        cfg.set_first_run_complete(True)
        cfg.sync()

        self.accept()
