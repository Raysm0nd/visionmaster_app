"""VisionMaster-style dark theme: bundled CJK font + charcoal QSS.

``apply_theme(app)`` registers the bundled Noto Sans TC font (so headless /
offscreen rendering has real glyphs, and Traditional-Chinese UI chrome renders
everywhere) and applies the dark stylesheet with the orange accent used for
selection/highlights.
"""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtGui, QtWidgets

ACCENT = "#e87d0d"  # VisionMaster-ish orange
_FONT_FILE = Path(__file__).parent / "assets" / "fonts" / "NotoSansTC-Regular.ttf"

_QSS = f"""
* {{ outline: none; }}
QMainWindow, QDialog, QDockWidget, QWidget {{
    background-color: #2d2d2d; color: #d6d6d6;
}}
QMenuBar, QMenu {{ background-color: #232323; color: #d6d6d6; }}
QMenuBar::item:selected, QMenu::item:selected {{ background: {ACCENT}; color: #fff; }}
QToolBar {{
    background-color: #232323; border: none; spacing: 4px; padding: 3px;
}}
QToolBar QToolButton {{
    background: transparent; color: #d6d6d6; padding: 4px 10px; border-radius: 3px;
}}
QToolBar QToolButton:hover {{ background: #3a3a3a; }}
QToolBar QToolButton:pressed {{ background: {ACCENT}; color: #fff; }}
QDockWidget {{ titlebar-close-icon: none; font-weight: bold; }}
QDockWidget::title {{
    background: #232323; padding: 5px 8px; border-bottom: 1px solid #1a1a1a;
}}
QTabWidget::pane {{ border: 1px solid #1f1f1f; background: #2d2d2d; }}
QTabBar::tab {{
    background: #232323; color: #b8b8b8; padding: 6px 18px;
    border: 1px solid #1f1f1f; border-bottom: none;
}}
QTabBar::tab:selected {{
    background: #2d2d2d; color: #fff; border-bottom: 2px solid {ACCENT};
}}
QListWidget, QTreeWidget, QTableWidget, QTableView {{
    background-color: #262626; alternate-background-color: #2b2b2b;
    border: 1px solid #1f1f1f; color: #d6d6d6;
    selection-background-color: {ACCENT}; selection-color: #fff;
    gridline-color: #383838;
}}
QHeaderView::section {{
    background-color: #232323; color: #cfcfcf; padding: 4px 8px;
    border: none; border-right: 1px solid #1a1a1a; border-bottom: 1px solid #1a1a1a;
}}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: #1f1f1f; color: #e0e0e0; border: 1px solid #3c3c3c;
    border-radius: 2px; padding: 3px 6px; selection-background-color: {ACCENT};
}}
QComboBox QAbstractItemView {{
    background: #262626; color: #e0e0e0; selection-background-color: {ACCENT};
}}
QPushButton {{
    background-color: #3a3a3a; color: #e0e0e0; border: 1px solid #4a4a4a;
    border-radius: 3px; padding: 4px 14px;
}}
QPushButton:hover {{ background-color: #454545; }}
QPushButton:pressed {{ background-color: {ACCENT}; color: #fff; }}
QCheckBox::indicator {{
    width: 14px; height: 14px; border: 1px solid #555; background: #1f1f1f;
}}
QCheckBox::indicator:checked {{ background: {ACCENT}; }}
QStatusBar {{ background: #232323; color: #b0b0b0; }}
QScrollBar:vertical {{ background: #262626; width: 11px; }}
QScrollBar:horizontal {{ background: #262626; height: 11px; }}
QScrollBar::handle {{ background: #4a4a4a; border-radius: 4px; min-height: 24px; }}
QScrollBar::handle:hover {{ background: #5a5a5a; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QSplitter::handle {{ background: #1f1f1f; }}
QToolTip {{ background: #1f1f1f; color: #e0e0e0; border: 1px solid {ACCENT}; }}
"""


def apply_theme(app: QtWidgets.QApplication) -> None:
    family = "Noto Sans TC"
    if _FONT_FILE.exists():
        font_id = QtGui.QFontDatabase.addApplicationFont(str(_FONT_FILE))
        families = QtGui.QFontDatabase.applicationFontFamilies(font_id)
        if families:
            family = families[0]
    app.setFont(QtGui.QFont(family, 9))
    app.setStyle("Fusion")  # consistent base across platforms
    app.setStyleSheet(_QSS)
