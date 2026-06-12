"""Shared fixtures for desktop-UI tests (needs the ``gui`` extra).

Forces the offscreen Qt platform so the whole suite runs with no display, and
provides a single process-wide ``QApplication``. Tests are skipped automatically
when PySide6 is not installed (pure-engine environments).
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6 import QtWidgets  # noqa: E402


@pytest.fixture(scope="session")
def qapp():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app
