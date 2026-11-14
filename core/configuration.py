"""
SafeNote Configuration Management Module.

Provides centralized configuration management using QSettings.
Implements a singleton pattern for consistent access across the application.
"""

import os
from pathlib import Path

from PySide6.QtCore import QSettings


# ---------------------------------------------------------------------------
# Settings key constants
# ---------------------------------------------------------------------------

# General
KEY_LANGUAGE = "general/language"
KEY_THEME = "general/theme"
KEY_AUTO_START = "general/auto_start"
KEY_START_MINIMIZED = "general/start_minimized"
KEY_CHECK_UPDATES = "general/check_updates"
KEY_FIRST_RUN_COMPLETE = "general/first_run_complete"

# Storage
KEY_STORAGE_DIRECTORY = "storage/directory"

# Audio
KEY_SAMPLE_RATE = "audio/sample_rate"
KEY_CHANNELS = "audio/channels"

# Shortcuts
KEY_EMERGENCY_HIDE_SHORTCUT = "shortcuts/emergency_hide"
KEY_RECORD_SHORTCUT = "shortcuts/record"


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------

DEFAULTS = {
    KEY_LANGUAGE: "tr",
    KEY_THEME: "dark",
    KEY_AUTO_START: False,
    KEY_START_MINIMIZED: False,
    KEY_CHECK_UPDATES: True,
    KEY_FIRST_RUN_COMPLETE: False,
    KEY_STORAGE_DIRECTORY: str(Path.home() / "SafeNote" / "Recordings"),
    KEY_SAMPLE_RATE: 44100,
    KEY_CHANNELS: 1,
    KEY_EMERGENCY_HIDE_SHORTCUT: "Ctrl+Shift+H",
    KEY_RECORD_SHORTCUT: "Ctrl+R",
}


class Configuration:
    """
    Singleton configuration manager backed by QSettings.

    All application settings are accessed and modified through this class.
    Default values are applied transparently when a key has not been
    explicitly set.

    Usage::

        config = Configuration.instance()
        lang = config.get(KEY_LANGUAGE)
        config.set(KEY_THEME, "light")
    """

    _instance: "Configuration | None" = None

    def __init__(self) -> None:
        """Initialise the QSettings backend (INI format, user scope)."""
        self._settings = QSettings(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            "SafeNote",
            "SafeNote",
        )

    # -- singleton access ---------------------------------------------------

    @classmethod
    def instance(cls) -> "Configuration":
        """Return the single shared Configuration instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton (useful for testing)."""
        cls._instance = None

    # -- generic get / set --------------------------------------------------

    def get(self, key: str, fallback=None):
        """
        Retrieve a setting value.

        Parameters
        ----------
        key : str
            One of the ``KEY_*`` constants defined in this module.
        fallback :
            Returned when neither the stored settings nor ``DEFAULTS``
            contain *key*.  When *None*, the built-in default is used.

        Returns
        -------
        object
            The stored (or default) value, with automatic type casting for
            booleans and integers based on the default type.
        """
        default = DEFAULTS.get(key, fallback)
        value = self._settings.value(key, default)

        # QSettings may return strings for booleans / integers – cast back.
        if isinstance(default, bool):
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)
        if isinstance(default, int) and not isinstance(default, bool):
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        return value

    def set(self, key: str, value) -> None:
        """
        Persist a setting value.

        Parameters
        ----------
        key : str
            One of the ``KEY_*`` constants.
        value :
            The value to store.
        """
        self._settings.setValue(key, value)
        self._settings.sync()

    # -- convenience accessors ----------------------------------------------

    # Language
    def get_language(self) -> str:
        """Return the current UI language code (``'tr'``, ``'en'``, or ``'az'``)."""
        return self.get(KEY_LANGUAGE)

    def set_language(self, language: str) -> None:
        """Set the UI language code."""
        self.set(KEY_LANGUAGE, language)

    # Theme
    def get_theme(self) -> str:
        """Return the current theme name (``'dark'`` or ``'light'``)."""
        return self.get(KEY_THEME)

    def set_theme(self, theme: str) -> None:
        """Set the theme name."""
        self.set(KEY_THEME, theme)

    # Storage directory
    def get_storage_directory(self) -> str:
        """
        Return the recordings storage directory path.

        The directory is created on disk if it does not already exist.
        """
        directory = self.get(KEY_STORAGE_DIRECTORY)
        os.makedirs(directory, exist_ok=True)
        return directory

    def set_storage_directory(self, directory: str) -> None:
        """Set the recordings storage directory path."""
        self.set(KEY_STORAGE_DIRECTORY, directory)

    # Auto-start
    def get_auto_start(self) -> bool:
        """Return whether the app should start with the OS."""
        return self.get(KEY_AUTO_START)

    def set_auto_start(self, enabled: bool) -> None:
        """Set the auto-start preference."""
        self.set(KEY_AUTO_START, enabled)

    # Start minimized
    def get_start_minimized(self) -> bool:
        """Return whether the app should start minimized to tray."""
        return self.get(KEY_START_MINIMIZED)

    def set_start_minimized(self, enabled: bool) -> None:
        """Set the start-minimized preference."""
        self.set(KEY_START_MINIMIZED, enabled)

    # Check updates
    def get_check_updates(self) -> bool:
        """Return whether the app should check for updates on launch."""
        return self.get(KEY_CHECK_UPDATES)

    def set_check_updates(self, enabled: bool) -> None:
        """Set the check-updates preference."""
        self.set(KEY_CHECK_UPDATES, enabled)

    # Sample rate
    def get_sample_rate(self) -> int:
        """Return the audio sample rate in Hz."""
        return self.get(KEY_SAMPLE_RATE)

    def set_sample_rate(self, rate: int) -> None:
        """Set the audio sample rate in Hz."""
        self.set(KEY_SAMPLE_RATE, rate)

    # Channels
    def get_channels(self) -> int:
        """Return the number of audio channels (1 = mono, 2 = stereo)."""
        return self.get(KEY_CHANNELS)

    def set_channels(self, channels: int) -> None:
        """Set the number of audio channels."""
        self.set(KEY_CHANNELS, channels)

    # Shortcuts
    def get_emergency_hide_shortcut(self) -> str:
        """Return the keyboard shortcut string for emergency hide."""
        return self.get(KEY_EMERGENCY_HIDE_SHORTCUT)

    def set_emergency_hide_shortcut(self, shortcut: str) -> None:
        """Set the keyboard shortcut string for emergency hide."""
        self.set(KEY_EMERGENCY_HIDE_SHORTCUT, shortcut)

    def get_record_shortcut(self) -> str:
        """Return the keyboard shortcut string for start/stop recording."""
        return self.get(KEY_RECORD_SHORTCUT)

    def set_record_shortcut(self, shortcut: str) -> None:
        """Set the keyboard shortcut string for start/stop recording."""
        self.set(KEY_RECORD_SHORTCUT, shortcut)

    # First run
    def is_first_run(self) -> bool:
        """Return ``True`` if the first-run wizard has not been completed."""
        return not self.get(KEY_FIRST_RUN_COMPLETE)

    def set_first_run_complete(self, complete: bool = True) -> None:
        """Mark the first-run wizard as completed."""
        self.set(KEY_FIRST_RUN_COMPLETE, complete)

    # -- housekeeping -------------------------------------------------------

    def sync(self) -> None:
        """Flush any pending writes to persistent storage."""
        self._settings.sync()

    def all_keys(self) -> list[str]:
        """Return a list of all keys currently stored in settings."""
        return self._settings.allKeys()
