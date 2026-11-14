"""
SafeNote Application Singleton.

Coordinates configuration, localization, theming, and application-wide signals.
"""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal

from core.configuration import Configuration, KEY_LANGUAGE, KEY_THEME
from core.localization import Localization, LANGUAGE_NAMES

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Theme Stylesheets (Dark and Light)
# ---------------------------------------------------------------------------

DARK_THEME = """
QMainWindow, QWidget#centralWidget, QDialog {
    background-color: #121418;
    color: #e6edf3;
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    font-size: 14px;
}

QWidget {
    background-color: transparent;
    color: #e6edf3;
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
}

QFrame#sidebar {
    background-color: #181b21;
    border-right: 1px solid #282d37;
    min-width: 200px;
    max-width: 220px;
}

QFrame#card, QFrame#panel {
    background-color: #1a1e26;
    border: 1px solid #282d37;
    border-radius: 10px;
}

QFrame#card:hover {
    border-color: #3d4554;
}

QLabel {
    color: #e6edf3;
}

QLabel#title {
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
}

QLabel#subtitle {
    font-size: 13px;
    color: #8b949e;
}

QLabel#heading {
    font-size: 18px;
    font-weight: 600;
    color: #f0f6fc;
}

QLabel#badge {
    padding: 3px 8px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #363b42;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #30363d;
    border-color: #8b949e;
}

QPushButton:pressed {
    background-color: #161b22;
}

QPushButton:disabled {
    background-color: #161b22;
    color: #484f58;
    border-color: #21262d;
}

QPushButton#nav_button {
    text-align: left;
    padding: 10px 16px;
    border: none;
    border-radius: 6px;
    background-color: transparent;
    font-weight: 500;
    font-size: 14px;
    color: #8b949e;
}

QPushButton#nav_button:hover {
    background-color: #21262d;
    color: #f0f6fc;
}

QPushButton#nav_button[active="true"] {
    background-color: #1f6feb;
    color: #ffffff;
    font-weight: 600;
}

QPushButton#primary {
    background-color: #238636;
    color: #ffffff;
    border: 1px solid #2ea043;
}

QPushButton#primary:hover {
    background-color: #2ea043;
}

QPushButton#danger {
    background-color: #da3633;
    color: #ffffff;
    border: 1px solid #f85149;
}

QPushButton#danger:hover {
    background-color: #b62324;
}

QPushButton#record {
    background-color: #238636;
    color: #ffffff;
    border: none;
    border-radius: 25px;
    font-size: 16px;
    font-weight: bold;
    min-height: 50px;
    padding: 10px 24px;
}

QPushButton#record:hover {
    background-color: #2ea043;
}

QPushButton#record_stop {
    background-color: #da3633;
    color: #ffffff;
    border: none;
    border-radius: 25px;
    font-size: 16px;
    font-weight: bold;
    min-height: 50px;
    padding: 10px 24px;
}

QPushButton#record_stop:hover {
    background-color: #b62324;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #0d1117;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #1f6feb;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border-color: #58a6ff;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #161b22;
    color: #e6edf3;
    border: 1px solid #30363d;
    selection-background-color: #1f6feb;
}

QTableWidget {
    background-color: #161b22;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    gridline-color: #21262d;
    selection-background-color: #1f6feb;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #0d1117;
    color: #8b949e;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #30363d;
    font-weight: 600;
}

QScrollBar:vertical {
    border: none;
    background: #0d1117;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #30363d;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #8b949e;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #21262d;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #1f6feb;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #58a6ff;
    width: 14px;
    margin: -4px 0;
    border-radius: 7px;
}

QProgressBar {
    background-color: #21262d;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #e6edf3;
    font-size: 11px;
}

QProgressBar::chunk {
    background-color: #238636;
    border-radius: 4px;
}

QTabWidget::pane {
    border: 1px solid #30363d;
    border-radius: 6px;
    background-color: #161b22;
}

QTabBar::tab {
    background-color: #0d1117;
    color: #8b949e;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #161b22;
    color: #e6edf3;
    font-weight: 600;
}

QCheckBox {
    spacing: 8px;
    color: #e6edf3;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #30363d;
    background-color: #0d1117;
}

QCheckBox::indicator:checked {
    background-color: #1f6feb;
    border-color: #58a6ff;
}
"""

LIGHT_THEME = """
QMainWindow, QWidget#centralWidget, QDialog {
    background-color: #f6f8fa;
    color: #1f2328;
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    font-size: 14px;
}

QWidget {
    background-color: transparent;
    color: #1f2328;
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
}

QFrame#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #d0d7de;
    min-width: 200px;
    max-width: 220px;
}

QFrame#card, QFrame#panel {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 10px;
}

QFrame#card:hover {
    border-color: #afb8c1;
}

QLabel {
    color: #1f2328;
}

QLabel#title {
    font-size: 24px;
    font-weight: 700;
    color: #1f2328;
}

QLabel#subtitle {
    font-size: 13px;
    color: #656d76;
}

QLabel#heading {
    font-size: 18px;
    font-weight: 600;
    color: #1f2328;
}

QPushButton {
    background-color: #f6f8fa;
    color: #1f2328;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #f3f4f6;
    border-color: #8c959f;
}

QPushButton:pressed {
    background-color: #ebecf0;
}

QPushButton:disabled {
    background-color: #f6f8fa;
    color: #8c959f;
    border-color: #d0d7de;
}

QPushButton#nav_button {
    text-align: left;
    padding: 10px 16px;
    border: none;
    border-radius: 6px;
    background-color: transparent;
    font-weight: 500;
    font-size: 14px;
    color: #656d76;
}

QPushButton#nav_button:hover {
    background-color: #eaeef2;
    color: #1f2328;
}

QPushButton#nav_button[active="true"] {
    background-color: #0969da;
    color: #ffffff;
    font-weight: 600;
}

QPushButton#primary {
    background-color: #1f883d;
    color: #ffffff;
    border: 1px solid #1a7f37;
}

QPushButton#primary:hover {
    background-color: #1a7f37;
}

QPushButton#danger {
    background-color: #cf222e;
    color: #ffffff;
    border: 1px solid #b62324;
}

QPushButton#danger:hover {
    background-color: #a40e26;
}

QPushButton#record {
    background-color: #1f883d;
    color: #ffffff;
    border: none;
    border-radius: 25px;
    font-size: 16px;
    font-weight: bold;
    min-height: 50px;
    padding: 10px 24px;
}

QPushButton#record:hover {
    background-color: #1a7f37;
}

QPushButton#record_stop {
    background-color: #cf222e;
    color: #ffffff;
    border: none;
    border-radius: 25px;
    font-size: 16px;
    font-weight: bold;
    min-height: 50px;
    padding: 10px 24px;
}

QPushButton#record_stop:hover {
    background-color: #a40e26;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #ffffff;
    color: #1f2328;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #0969da;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border-color: #0969da;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #1f2328;
    border: 1px solid #d0d7de;
    selection-background-color: #0969da;
}

QTableWidget {
    background-color: #ffffff;
    color: #1f2328;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    gridline-color: #eaeef2;
    selection-background-color: #0969da;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #f6f8fa;
    color: #656d76;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #d0d7de;
    font-weight: 600;
}

QScrollBar:vertical {
    border: none;
    background: #f6f8fa;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #d0d7de;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #8c959f;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #eaeef2;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #0969da;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #0969da;
    width: 14px;
    margin: -4px 0;
    border-radius: 7px;
}

QProgressBar {
    background-color: #eaeef2;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #1f2328;
    font-size: 11px;
}

QProgressBar::chunk {
    background-color: #1f883d;
    border-radius: 4px;
}

QTabWidget::pane {
    border: 1px solid #d0d7de;
    border-radius: 6px;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: #f6f8fa;
    color: #656d76;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #1f2328;
    font-weight: 600;
}

QCheckBox {
    spacing: 8px;
    color: #1f2328;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #d0d7de;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #0969da;
    border-color: #0969da;
}
"""


class SafeNoteApplication(QObject):
    """
    Central Application coordinator singleton.
    
    Manages configuration, localization, theming, and broadcasts global signals.
    """

    language_changed = Signal(str)
    theme_changed = Signal(str)
    settings_changed = Signal()

    _instance: Optional["SafeNoteApplication"] = None

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._config = Configuration.instance()
        lang = self._config.get_language() or "tr"
        self._localizer = Localization(lang)

    @classmethod
    def instance(cls) -> "SafeNoteApplication":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def config(self) -> Configuration:
        return self._config

    @property
    def localizer(self) -> Localization:
        return self._localizer

    def tr(self, key: str, *args, **kwargs) -> str:
        """Translate a string key using current localizer."""
        return self._localizer.tr(key, *args, **kwargs)

    def change_language(self, language_code: str) -> None:
        """Change application language and notify all components."""
        if language_code not in LANGUAGE_NAMES:
            logger.warning("Attempted to set unknown language: %s", language_code)
            return

        self._localizer.set_language(language_code)
        self._config.set_language(language_code)
        self.language_changed.emit(language_code)
        self.settings_changed.emit()

    def change_theme(self, theme_name: str) -> None:
        """Change application theme and notify all components."""
        theme_name = theme_name.lower()
        if theme_name not in ("dark", "light"):
            theme_name = "dark"

        self._config.set_theme(theme_name)
        self.theme_changed.emit(theme_name)
        self.settings_changed.emit()

    def get_theme_stylesheet(self, theme: Optional[str] = None) -> str:
        """Return the CSS stylesheet for the given (or configured) theme."""
        if theme is None:
            theme = self._config.get_theme()
        if theme == "light":
            return LIGHT_THEME
        return DARK_THEME


def get_app() -> SafeNoteApplication:
    """Convenience getter for the SafeNoteApplication instance."""
    return SafeNoteApplication.instance()
