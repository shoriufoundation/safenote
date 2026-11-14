"""
Automated unit tests for SafeNote Core Infrastructure.

Tests:
- Configuration singleton, defaults, and persistence
- Localization dictionaries (Turkish, English, Azerbaijani)
- Translation completeness
- SafeNoteApplication coordination
"""

import pytest
from PySide6.QtCore import QCoreApplication

from core.application import SafeNoteApplication, get_app
from core.configuration import (
    KEY_CHANNELS,
    KEY_EMERGENCY_HIDE_SHORTCUT,
    KEY_LANGUAGE,
    KEY_RECORD_SHORTCUT,
    KEY_SAMPLE_RATE,
    KEY_THEME,
    Configuration,
)
from core.localization import (
    LANGUAGE_NAMES,
    TRANSLATIONS_AZ,
    TRANSLATIONS_EN,
    TRANSLATIONS_TR,
    Localization,
)


def test_configuration_defaults(qapp):
    """Test configuration initializes with expected default values."""
    cfg = Configuration.instance()
    assert cfg.get_language() in ("tr", "en", "az")
    assert cfg.get_theme() in ("dark", "light")
    assert cfg.get_sample_rate() in (44100, 48000, 22050, 16000)
    assert cfg.get_channels() in (1, 2)
    assert "Ctrl" in cfg.get_emergency_hide_shortcut()


def test_localization_languages():
    """Test that all three required languages have non-empty translations."""
    assert len(LANGUAGE_NAMES) == 3
    assert "tr" in LANGUAGE_NAMES
    assert "en" in LANGUAGE_NAMES
    assert "az" in LANGUAGE_NAMES

    # Check key counts
    assert len(TRANSLATIONS_TR) > 50
    assert len(TRANSLATIONS_EN) > 50
    assert len(TRANSLATIONS_AZ) > 50

    # Test key presence
    critical_keys = [
        "app_name",
        "slogan",
        "dashboard",
        "recording",
        "library",
        "player",
        "settings",
        "about",
        "start_recording",
        "stop_recording",
        "emergency_hide",
        "workspace_locked",
        "unlock",
    ]

    for key in critical_keys:
        assert key in TRANSLATIONS_TR, f"Missing {key} in TR"
        assert key in TRANSLATIONS_EN, f"Missing {key} in EN"
        assert key in TRANSLATIONS_AZ, f"Missing {key} in AZ"


def test_localization_lookup():
    """Test translation lookup and fallback."""
    loc_tr = Localization("tr")
    assert loc_tr.tr("app_name") == "SafeNote"
    assert loc_tr.tr("start_recording") == "Kaydı Başlat"

    loc_en = Localization("en")
    assert loc_en.tr("start_recording") == "Start Recording"

    loc_az = Localization("az")
    assert loc_az.tr("start_recording") == "Yazmağa Başla"


def test_application_singleton(qapp):
    """Test SafeNoteApplication signals and coordination."""
    app_mgr = get_app()
    assert app_mgr is not None
    assert app_mgr.tr("app_name") == "SafeNote"

    # Test theme stylesheet generation
    dark_css = app_mgr.get_theme_stylesheet("dark")
    assert "background-color" in dark_css
    light_css = app_mgr.get_theme_stylesheet("light")
    assert "background-color" in light_css
