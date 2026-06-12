"""Application toolbar — file/module icon actions + run buttons.

Icon actions emit named signals; the host window wires them to behaviour. The
two run buttons (執行全部 primary, 部分執行 secondary) drive engine execution.
"""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from visionpower.app import icons, theme

# (icon, tooltip, signal-name) for the two icon-button groups.
_TOOLS_A = [
    ("save", "儲存", "saveClicked"),
    ("open", "開啟", "openClicked"),
    ("export", "另存", "saveAsClicked"),
    ("import", "匯入", "importClicked"),
    ("lock", "加密", "lockClicked"),
]
_TOOLS_B = [
    ("camera", "擷取", "captureClicked"),
    ("library", "模組庫", "libraryClicked"),
    ("var", "全域變數", "varsClicked"),
    ("cube", "3D 處理", "td3Clicked"),
    ("aim", "全域校正", "calibClicked"),
    ("code", "腳本", "scriptClicked"),
]


class Toolbar(QtWidgets.QWidget):
    runAll = QtCore.Signal()
    runPartial = QtCore.Signal()
    saveClicked = QtCore.Signal()
    openClicked = QtCore.Signal()
    saveAsClicked = QtCore.Signal()
    importClicked = QtCore.Signal()
    lockClicked = QtCore.Signal()
    captureClicked = QtCore.Signal()
    libraryClicked = QtCore.Signal()
    varsClicked = QtCore.Signal()
    td3Clicked = QtCore.Signal()
    calibClicked = QtCore.Signal()
    scriptClicked = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(54)
        self.setObjectName("toolbar")
        self.setStyleSheet(
            f"#toolbar{{background:{theme.BG_PANEL};"
            f"border-bottom:1px solid rgba(255,255,255,0.06);}}"
        )

        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(14, 0, 14, 0)
        row.setSpacing(4)

        for icon, tip, sig in _TOOLS_A:
            row.addWidget(self._icon_button(icon, tip, sig))
        row.addWidget(self._separator())
        for icon, tip, sig in _TOOLS_B:
            row.addWidget(self._icon_button(icon, tip, sig))
        row.addWidget(self._separator())

        self.run_all_btn = self._primary_run_button()
        self.run_partial_btn = self._secondary_run_button()
        self.run_all_btn.clicked.connect(self.runAll)
        self.run_partial_btn.clicked.connect(self.runPartial)
        row.addWidget(self.run_all_btn)
        row.addWidget(self.run_partial_btn)
        row.addStretch(1)

    # -- helpers -----------------------------------------------------------
    def _icon_button(self, icon: str, tip: str, signal_name: str) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton()
        btn.setIcon(icons.make_icon(icon, "#97A3B4", 18))
        btn.setIconSize(QtCore.QSize(18, 18))
        btn.setToolTip(tip)
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setFixedSize(34, 34)
        btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:8px;}"
            "QPushButton:hover{background:rgba(47,128,216,0.14);}"
        )
        if hasattr(self, signal_name):
            btn.clicked.connect(getattr(self, signal_name))
        return btn

    def _separator(self) -> QtWidgets.QFrame:
        line = QtWidgets.QFrame()
        line.setFixedSize(1, 22)
        line.setStyleSheet("background:rgba(255,255,255,0.09);")
        return line

    def _primary_run_button(self) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton("  執行全部")
        btn.setIcon(icons.make_icon("play", "#FFFFFF", 15))
        btn.setIconSize(QtCore.QSize(15, 15))
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setFixedHeight(34)
        btn.setMinimumWidth(108)
        btn.setStyleSheet(
            f"QPushButton{{color:#fff;border:none;border-radius:8px;"
            f"font-size:12px;font-weight:600;padding:0 14px;"
            f"background:{theme.PRIMARY};}}"
            f"QPushButton:hover{{background:{theme.ACCENT};}}"
        )
        return btn

    def _secondary_run_button(self) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton("  部分執行")
        btn.setIcon(icons.make_icon("step", "#CFE2FB", 15))
        btn.setIconSize(QtCore.QSize(15, 15))
        btn.setToolTip("從選取節點往下執行")
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setFixedHeight(34)
        btn.setStyleSheet(
            "QPushButton{color:#CFE2FB;border-radius:8px;"
            "font-size:12px;font-weight:600;padding:0 13px;"
            "background:rgba(47,128,216,0.10);"
            "border:1px solid rgba(47,128,216,0.34);}"
            "QPushButton:hover{background:rgba(47,128,216,0.20);color:#fff;}"
        )
        return btn
