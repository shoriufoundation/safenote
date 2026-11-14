"""
Automated unit tests for SafeNote UI Module.

Tests:
- Emergency Hide state transitions (lock and unlock)
- First-run wizard initialization and navigation
- Main window navigation and page indices
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from ui.emergency_hide_widget import EmergencyHideWidget
from ui.first_run_dialog import FirstRunWizard
from ui.main_window import MainWindow


def test_emergency_hide_widget(qapp):
    """Test emergency hide widget signals and retranslation."""
    widget = EmergencyHideWidget()
    unlocked_signal_fired = False

    def on_unlocked():
        nonlocal unlocked_signal_fired
        unlocked_signal_fired = True

    widget.unlocked.connect(on_unlocked)
    widget._unlock_btn.click()
    assert unlocked_signal_fired is True


def test_first_run_wizard_navigation(qapp):
    """Test FirstRunWizard navigation through all steps."""
    wizard = FirstRunWizard()
    assert wizard._stack.currentIndex() == 0
    wizard._next_step()
    assert wizard._stack.currentIndex() == 1
    wizard._next_step()
    assert wizard._stack.currentIndex() == 2
    wizard._next_step()
    assert wizard._stack.currentIndex() == 3
    wizard._prev_step()
    assert wizard._stack.currentIndex() == 2


def test_main_window_emergency_hide_transition(qapp):
    """Test MainWindow transitions cleanly to Emergency Hide and restores correctly."""
    with tempfile.TemporaryDirectory() as td:
        with patch("sounddevice.RawInputStream"):
            with patch("core.configuration.Configuration.is_first_run", return_value=False):
                win = MainWindow()
                win.show()
                assert not win._is_emergency_locked
                assert not win._sidebar.isHidden()

                # Trigger emergency lock
                win.trigger_emergency_hide()
                assert win._is_emergency_locked
                assert win._sidebar.isHidden()
                assert win._stack.currentIndex() == MainWindow.PAGE_EMERGENCY

                # Unlock
                win.unlock_emergency_hide()
                assert not win._is_emergency_locked
                assert not win._sidebar.isHidden()
                assert win._stack.currentIndex() == MainWindow.PAGE_DASHBOARD
                win.close()
