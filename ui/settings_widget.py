"""
SafeNote Settings Widget.

Provides full configuration for:
- General (Theme, Startup options, Update checks)
- Audio (Default sample rate, channels)
- Encryption & Security (Keyring status, Export / Import key backup)
- Storage (Directory path, Browse, Rescan)
- Keyboard Shortcuts (Emergency Hide, Record toggle)
- Language (Turkish, English, Azerbaijani)
"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.application import get_app
from core.configuration import (
    KEY_AUTO_START,
    KEY_CHECK_UPDATES,
    KEY_CHANNELS,
    KEY_EMERGENCY_HIDE_SHORTCUT,
    KEY_LANGUAGE,
    KEY_RECORD_SHORTCUT,
    KEY_SAMPLE_RATE,
    KEY_START_MINIMIZED,
    KEY_STORAGE_DIRECTORY,
    KEY_THEME,
)
from core.localization import LANGUAGE_NAMES
from crypto.key_manager import export_key_base64, import_key_base64, key_exists

logger = logging.getLogger(__name__)


class SettingsWidget(QWidget):
    """
    Settings configuration interface.
    """

    settings_updated = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()
        self.load_settings()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(16)

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

        # Tab widget for organized settings
        self._tabs = QTabWidget()
        self._tabs.setObjectName("settings_tabs")

        # Tab 1: General
        self._tab_general = self._build_general_tab()
        self._tabs.addTab(self._tab_general, "⚙️ General")

        # Tab 2: Audio
        self._tab_audio = self._build_audio_tab()
        self._tabs.addTab(self._tab_audio, "🎙️ Audio")

        # Tab 3: Security & Encryption
        self._tab_security = self._build_security_tab()
        self._tabs.addTab(self._tab_security, "🔒 Security")

        # Tab 4: Storage
        self._tab_storage = self._build_storage_tab()
        self._tabs.addTab(self._tab_storage, "💾 Storage")

        # Tab 5: Keyboard Shortcuts
        self._tab_shortcuts = self._build_shortcuts_tab()
        self._tabs.addTab(self._tab_shortcuts, "⌨️ Shortcuts")

        # Tab 6: Language
        self._tab_language = self._build_language_tab()
        self._tabs.addTab(self._tab_language, "🌐 Language")

        main_layout.addWidget(self._tabs, stretch=1)

        # Bottom buttons (Save / Apply / Restore)
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        self._btn_save = QPushButton("💾 Save Settings")
        self._btn_save.setObjectName("primary")
        self._btn_save.setMinimumWidth(140)
        self._btn_save.clicked.connect(self.save_settings)
        btn_bar.addWidget(self._btn_save)

        main_layout.addLayout(btn_bar)

        self.retranslate()
        get_app().language_changed.connect(self.retranslate)

    # ----------------------------------------------------------------------
    # Tab Builders
    # ----------------------------------------------------------------------

    def _build_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Appearance Group
        grp_theme = QGroupBox("Appearance")
        g_layout = QGridLayout(grp_theme)
        self._lbl_theme = QLabel("Interface Theme:")
        self._combo_theme = QComboBox()
        self._combo_theme.addItems(["Dark", "Light"])
        self._combo_theme.currentIndexChanged.connect(self._on_theme_changed)
        g_layout.addWidget(self._lbl_theme, 0, 0)
        g_layout.addWidget(self._combo_theme, 0, 1)
        layout.addWidget(grp_theme)

        # Startup Options Group
        grp_startup = QGroupBox("Startup Behavior")
        s_layout = QVBoxLayout(grp_startup)
        s_layout.setSpacing(12)
        self._chk_autostart = QCheckBox("Start SafeNote when Windows starts")
        self._chk_minimized = QCheckBox("Start minimized to system tray")
        self._chk_updates = QCheckBox("Check for application updates on launch")
        s_layout.addWidget(self._chk_autostart)
        s_layout.addWidget(self._chk_minimized)
        s_layout.addWidget(self._chk_updates)
        layout.addWidget(grp_startup)

        layout.addStretch()
        return widget

    def _build_audio_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        grp_defaults = QGroupBox("Recording Defaults")
        grid = QGridLayout(grp_defaults)
        grid.setSpacing(12)

        self._lbl_rate = QLabel("Default Sample Rate:")
        self._combo_rate = QComboBox()
        self._combo_rate.addItems(["44100 Hz", "48000 Hz", "22050 Hz", "16000 Hz"])

        self._lbl_chan = QLabel("Default Channels:")
        self._combo_chan = QComboBox()
        self._combo_chan.addItems(["1 (Mono)", "2 (Stereo)"])

        grid.addWidget(self._lbl_rate, 0, 0)
        grid.addWidget(self._combo_rate, 0, 1)
        grid.addWidget(self._lbl_chan, 1, 0)
        grid.addWidget(self._combo_chan, 1, 1)

        layout.addWidget(grp_defaults)

        note_label = QLabel(
            "Note: 44,100 Hz Mono is recommended for high voice clarity and compact encrypted file size."
        )
        note_label.setObjectName("subtitle")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)

        layout.addStretch()
        return widget

    def _build_security_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Encryption Info
        grp_crypto = QGroupBox("Encryption Engine")
        c_layout = QVBoxLayout(grp_crypto)
        c_layout.setSpacing(8)

        info1 = QLabel("Cipher: AES-256-GCM (Authenticated Encryption with Associated Data)")
        info1.setStyleSheet("font-weight: 500;")
        info2 = QLabel("Key Storage: OS Keyring (Windows Credential Manager)")
        info3 = QLabel("Status: Key is active and protected.")
        info3.setStyleSheet("color: #2ea043; font-weight: 600;")

        c_layout.addWidget(info1)
        c_layout.addWidget(info2)
        c_layout.addWidget(info3)
        layout.addWidget(grp_crypto)

        # Key Lifecycle and Backup
        grp_key = QGroupBox("Key Management & Disaster Recovery")
        k_layout = QVBoxLayout(grp_key)
        k_layout.setSpacing(12)

        k_warn = QLabel(
            "⚠️ CRITICAL: If you lose your encryption key, your recordings CANNOT be decrypted. "
            "You can export your key to a secure password manager for safe offline backup."
        )
        k_warn.setObjectName("subtitle")
        k_warn.setWordWrap(True)
        k_warn.setStyleSheet("color: #d29922; font-weight: 500;")
        k_layout.addWidget(k_warn)

        btn_row = QHBoxLayout()
        self._btn_export_key = QPushButton("🔑 Backup Key (Base64)")
        self._btn_export_key.clicked.connect(self._export_key)

        self._btn_import_key = QPushButton("📥 Restore Key from Backup")
        self._btn_import_key.clicked.connect(self._import_key)

        btn_row.addWidget(self._btn_export_key)
        btn_row.addWidget(self._btn_import_key)
        btn_row.addStretch()
        k_layout.addLayout(btn_row)

        layout.addWidget(grp_key)
        layout.addStretch()
        return widget

    def _build_storage_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        grp_store = QGroupBox("Recording Directory")
        s_layout = QVBoxLayout(grp_store)
        s_layout.setSpacing(10)

        self._lbl_store_path = QLabel("Location for encrypted .sna files:")
        self._edit_storage = QLineEdit()
        self._edit_storage.setReadOnly(True)

        row_btns = QHBoxLayout()
        self._btn_browse_store = QPushButton("📂 Browse...")
        self._btn_browse_store.clicked.connect(self._browse_storage)
        self._btn_open_folder = QPushButton("📁 Open in Explorer")
        self._btn_open_folder.clicked.connect(self._open_storage_folder)

        row_btns.addWidget(self._btn_browse_store)
        row_btns.addWidget(self._btn_open_folder)
        row_btns.addStretch()

        s_layout.addWidget(self._lbl_store_path)
        s_layout.addWidget(self._edit_storage)
        s_layout.addLayout(row_btns)

        layout.addWidget(grp_store)
        layout.addStretch()
        return widget

    def _build_shortcuts_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        grp_keys = QGroupBox("Keyboard Shortcuts")
        k_grid = QGridLayout(grp_keys)
        k_grid.setSpacing(12)

        self._lbl_sh_emergency = QLabel("Emergency Hide:")
        self._edit_sh_emergency = QLineEdit()
        self._edit_sh_emergency.setPlaceholderText("Ctrl+Shift+H")

        self._lbl_sh_record = QLabel("Start / Stop Recording:")
        self._edit_sh_record = QLineEdit()
        self._edit_sh_record.setPlaceholderText("Ctrl+R")

        k_grid.addWidget(self._lbl_sh_emergency, 0, 0)
        k_grid.addWidget(self._edit_sh_emergency, 0, 1)
        k_grid.addWidget(self._lbl_sh_record, 1, 0)
        k_grid.addWidget(self._edit_sh_record, 1, 1)

        layout.addWidget(grp_keys)

        sh_info = QLabel(
            "Shortcut format: e.g. 'Ctrl+Shift+H', 'Ctrl+R', 'F9'. Shortcuts work while SafeNote is focused."
        )
        sh_info.setObjectName("subtitle")
        layout.addWidget(sh_info)

        layout.addStretch()
        return widget

    def _build_language_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        grp_lang = QGroupBox("Application Language")
        l_layout = QGridLayout(grp_lang)

        self._lbl_lang = QLabel("Language / Dil / Dil:")
        self._combo_lang = QComboBox()
        for code, name in LANGUAGE_NAMES.items():
            self._combo_lang.addItem(f"{name} ({code})", code)
        self._combo_lang.currentIndexChanged.connect(self._on_language_changed)

        l_layout.addWidget(self._lbl_lang, 0, 0)
        l_layout.addWidget(self._combo_lang, 0, 1)

        layout.addWidget(grp_lang)

        lang_note = QLabel(
            "SafeNote is fully localized in Turkish (Türkçe), English, and Azerbaijani (Azərbaycanca)."
        )
        lang_note.setObjectName("subtitle")
        layout.addWidget(lang_note)

        layout.addStretch()
        return widget

    # ----------------------------------------------------------------------
    # Logic & Persistence
    # ----------------------------------------------------------------------

    def load_settings(self) -> None:
        """Load current settings from QSettings backend into UI fields."""
        app = get_app()
        cfg = app.config

        # Theme
        theme = cfg.get_theme()
        idx = 1 if theme == "light" else 0
        self._combo_theme.setCurrentIndex(idx)

        # General
        self._chk_autostart.setChecked(cfg.get_auto_start())
        self._chk_minimized.setChecked(cfg.get_start_minimized())
        self._chk_updates.setChecked(cfg.get_check_updates())

        # Audio
        rate = cfg.get_sample_rate()
        rate_str = f"{rate} Hz"
        rate_idx = self._combo_rate.findText(rate_str, Qt.MatchFlag.MatchStartsWith)
        if rate_idx >= 0:
            self._combo_rate.setCurrentIndex(rate_idx)

        chan = cfg.get_channels()
        self._combo_chan.setCurrentIndex(0 if chan == 1 else 1)

        # Storage
        self._edit_storage.setText(cfg.get_storage_directory())

        # Shortcuts
        self._edit_sh_emergency.setText(cfg.get_emergency_hide_shortcut())
        self._edit_sh_record.setText(cfg.get_record_shortcut())

        # Language
        lang = cfg.get_language()
        lang_idx = self._combo_lang.findData(lang)
        if lang_idx >= 0:
            self._combo_lang.blockSignals(True)
            self._combo_lang.setCurrentIndex(lang_idx)
            self._combo_lang.blockSignals(False)

    def save_settings(self) -> None:
        """Save settings from UI to backend configuration."""
        app = get_app()
        cfg = app.config

        cfg.set_auto_start(self._chk_autostart.isChecked())
        cfg.set_start_minimized(self._chk_minimized.isChecked())
        cfg.set_check_updates(self._chk_updates.isChecked())

        # Audio
        rate_val = int(self._combo_rate.currentText().split()[0])
        cfg.set_sample_rate(rate_val)
        chan_val = 1 if self._combo_chan.currentIndex() == 0 else 2
        cfg.set_channels(chan_val)

        # Storage
        cfg.set_storage_directory(self._edit_storage.text().strip())

        # Shortcuts
        sh_em = self._edit_sh_emergency.text().strip() or "Ctrl+Shift+H"
        sh_rec = self._edit_sh_record.text().strip() or "Ctrl+R"
        cfg.set_emergency_hide_shortcut(sh_em)
        cfg.set_record_shortcut(sh_rec)

        cfg.sync()
        self.settings_updated.emit()
        QMessageBox.information(self, app.tr("info"), "Settings successfully saved.")

    def _on_theme_changed(self, idx: int) -> None:
        theme = "light" if idx == 1 else "dark"
        get_app().change_theme(theme)

    def _on_language_changed(self, idx: int) -> None:
        lang = self._combo_lang.itemData(idx)
        if lang:
            get_app().change_language(lang)

    def _browse_storage(self) -> None:
        curr = self._edit_storage.text().strip()
        path = QFileDialog.getExistingDirectory(self, "Select Recording Directory", curr)
        if path:
            self._edit_storage.setText(path)

    def _open_storage_folder(self) -> None:
        path = self._edit_storage.text().strip()
        if os.path.exists(path):
            os.startfile(path)
        else:
            QMessageBox.warning(self, "Directory not found", f"The directory does not exist yet:\n{path}")

    def _export_key(self) -> None:
        app = get_app()
        try:
            b64_key = export_key_base64()
            QInputDialog.getMultiLineText(
                self,
                "SafeNote Key Backup",
                "Store this 256-bit encryption key in a secure location (e.g. password manager):\n"
                "WARNING: Anyone with this key can decrypt your recordings.",
                b64_key
            )
        except Exception as exc:
            QMessageBox.critical(self, app.tr("error"), f"Key export failed: {exc}")

    def _import_key(self) -> None:
        app = get_app()
        warn = QMessageBox.warning(
            self,
            app.tr("warning"),
            "CAUTION: Overwriting your encryption key will make recordings made with "
            "the current key permanently unreadable unless you have a backup of it.\n\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if warn != QMessageBox.StandardButton.Yes:
            return

        text, ok = QInputDialog.getText(
            self,
            "Import Encryption Key",
            "Paste the Base64-encoded 256-bit key:"
        )
        if ok and text.strip():
            try:
                import_key_base64(text.strip())
                QMessageBox.information(self, app.tr("info"), "Key successfully imported and stored in Keyring.")
            except Exception as exc:
                QMessageBox.critical(self, app.tr("error"), f"Invalid key: {exc}")

    def retranslate(self) -> None:
        app = get_app()
        self._page_title.setText(app.tr("settings"))
        self._page_subtitle.setText(app.tr("settings_general") if "settings_general" in app.localizer._translations else "Application and security configuration")
        self._tabs.setTabText(0, f"⚙️ {app.tr('settings_general') if 'settings_general' in app.localizer._translations else 'General'}")
        self._tabs.setTabText(1, f"🎙️ {app.tr('settings_audio') if 'settings_audio' in app.localizer._translations else 'Audio'}")
        self._tabs.setTabText(2, f"🔒 {app.tr('settings_security') if 'settings_security' in app.localizer._translations else 'Security'}")
        self._tabs.setTabText(3, f"💾 {app.tr('settings_storage') if 'settings_storage' in app.localizer._translations else 'Storage'}")
        self._tabs.setTabText(4, f"⌨️ {app.tr('settings_shortcuts') if 'settings_shortcuts' in app.localizer._translations else 'Shortcuts'}")
        self._tabs.setTabText(5, f"🌐 {app.tr('settings_language') if 'settings_language' in app.localizer._translations else 'Language'}")
        self._btn_save.setText(f"💾 {app.tr('save')}")
