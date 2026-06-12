"""AXON / VisionPower dark theme — AGC corporate palette.

All UI chrome is driven from the named tokens below; widgets reference these
constants instead of hard-coding hex, so a palette tweak is a one-line change.

``apply_theme(app)`` registers the bundled Noto Sans TC font (real CJK glyphs
even for headless/offscreen rendering) and applies the dark stylesheet.
"""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtGui, QtWidgets

# ---------------------------------------------------------------- palette
# AGC corporate colours (locked by the approved AXON design).
PRIMARY = "#0C4DA2"   # deep brand blue
ACCENT = "#2F80D8"    # interactive highlight (visible on dark)
RED = "#D23A55"       # alert / close / detection box
SUCCESS = "#34D399"   # done / ok
WARN = "#FBBF24"      # warning / NG

# Surfaces (darkest → lightest).
BG = "#0A0D13"        # window body
BG_DEEP = "#05070B"   # outermost backdrop
BG_PANEL = "#0B1018"  # toolbars / side panels
BG_CANVAS = "#070D15"  # node canvas
BG_DOCK = "#0A0F17"   # left icon dock

# Text + lines.
TEXT = "#E7ECF3"      # primary text
TEXT_DIM = "#7E8AA0"  # secondary / status text
TEXT_FAINT = "#5D6C80"  # hints / indices
BORDER = "#1C2530"    # hairline separators

# Per-node accent swatches, in pipeline order (image-source → send-data).
NODE_COLORS = ["#2DD4BF", "#5AA0E6", "#A78BFA", "#FBBF24", "#F472B6", "#34D399"]

# ----------------------------------------------------------------- fonts
# Preferred families with a graceful fallback when not installed on the host.
FONT_BRAND = "Space Grotesk"   # logo / headings
FONT_BODY = "IBM Plex Sans"    # general UI text
FONT_MONO = "JetBrains Mono"   # numbers / codes / readouts

_FONT_FILE = Path(__file__).parent / "assets" / "fonts" / "NotoSansTC-Regular.ttf"


def resolve_font_family(preferred: str, fallback: str) -> str:
    """Return ``preferred`` if installed (per QFontDatabase), else ``fallback``.

    Requires a live ``QApplication`` (QFontDatabase is queried statically).
    """

    if preferred in QtGui.QFontDatabase.families():
        return preferred
    return fallback


def build_stylesheet() -> str:
    """Build the application QSS from the palette tokens."""

    return f"""
* {{ outline: none; }}
QMainWindow, QDialog, QWidget {{
    background-color: {BG}; color: {TEXT};
    font-family: '{FONT_BODY}', 'Noto Sans TC', sans-serif;
}}
QToolTip {{
    background: {BG_PANEL}; color: {TEXT};
    border: 1px solid {ACCENT}; padding: 3px 6px;
}}
QLabel {{ background: transparent; }}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {BG_DEEP}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 6px; padding: 4px 8px;
    selection-background-color: {ACCENT};
}}
QComboBox QAbstractItemView {{
    background: {BG_PANEL}; color: {TEXT};
    selection-background-color: {ACCENT}; border: 1px solid {BORDER};
}}
QPushButton {{
    background-color: rgba(47,128,216,0.10); color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 8px; padding: 6px 14px;
}}
QPushButton:hover {{ background-color: rgba(47,128,216,0.20); }}
QPushButton:pressed {{ background-color: {ACCENT}; color: #fff; }}
QCheckBox::indicator {{
    width: 14px; height: 14px; border: 1px solid {BORDER};
    background: {BG_DEEP}; border-radius: 3px;
}}
QCheckBox::indicator:checked {{ background: {ACCENT}; }}
QScrollBar:vertical {{ background: transparent; width: 9px; }}
QScrollBar:horizontal {{ background: transparent; height: 9px; }}
QScrollBar::handle {{
    background: rgba(255,255,255,0.12); border-radius: 4px; min-height: 24px;
}}
QScrollBar::handle:hover {{ background: rgba(255,255,255,0.22); }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QSplitter::handle {{ background: {BORDER}; }}
"""


def apply_theme(app: QtWidgets.QApplication) -> None:
    """Register the bundled CJK font and apply the dark AGC stylesheet."""

    base_family = "Noto Sans TC"
    if _FONT_FILE.exists():
        font_id = QtGui.QFontDatabase.addApplicationFont(str(_FONT_FILE))
        families = QtGui.QFontDatabase.applicationFontFamilies(font_id)
        if families:
            base_family = families[0]
    app.setFont(QtGui.QFont(resolve_font_family(FONT_BODY, base_family), 9))
    app.setStyle("Fusion")  # consistent base across platforms
    app.setStyleSheet(build_stylesheet())
