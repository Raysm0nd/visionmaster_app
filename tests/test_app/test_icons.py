"""Phase 3 (Red): line-icon factory faithful to the design's SVG path set."""

from __future__ import annotations

from PySide6 import QtCore

from visionpower.app import icons


# Every icon name the shell / dock / canvas / panels reference.
_REQUIRED = [
    "cloud", "gear", "min", "max", "close", "play", "step",
    "save", "open", "export", "import", "lock",
    "camera", "library", "var", "str", "cube", "aim", "code",
    "ruler", "scan", "clock", "sliders", "layers", "bucket", "chart",
    "image", "pencil", "branch", "send", "blob", "ocr",
    "network", "plus", "search", "zoomout", "onetoone", "fullscreen",
    "split", "grid", "chevleft", "chevright", "warn", "runcircle",
]


def test_every_required_icon_is_defined():
    missing = [n for n in _REQUIRED if n not in icons.ICONS]
    assert missing == [], f"undefined icons: {missing}"


def test_make_icon_returns_nonnull_qicon(qapp):
    for name in _REQUIRED:
        ic = icons.make_icon(name, "#c2ccda", 18)
        assert not ic.isNull(), f"icon {name!r} rendered null"


def test_make_pixmap_has_requested_logical_size(qapp):
    # Rendered at 2x for crisp edges, so logical (device-independent) size == 24.
    pm = icons.make_pixmap("play", "#ffffff", 24)
    assert pm.deviceIndependentSize().toSize() == QtCore.QSize(24, 24)


def test_unknown_icon_falls_back_without_crashing(qapp):
    ic = icons.make_icon("does-not-exist", "#ffffff", 18)
    assert ic is not None  # returns a (possibly dot) icon, never raises
