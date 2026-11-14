"""
Pytest configuration for SafeNote test suite.
Ensures a single QApplication instance exists for GUI tests.
"""

import os
import pytest
from PySide6.QtWidgets import QApplication

# Set offscreen platform for reliable test execution on all environments
os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture(scope="session")
def qapp():
    """Shared QApplication for all tests in the session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
