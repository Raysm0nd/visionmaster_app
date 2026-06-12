"""Left icon dock — the 12 node categories, with a selected highlight.

This phase wires selection highlighting only (matching the design); binding a
category to "add that node" is intentionally out of scope.
"""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from visionpower.app import constants, icons, theme


class Dock(QtWidgets.QWidget):
    categorySelected = QtCore.Signal(int)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(constants.DOCK_W)
        self.setObjectName("dock")
        self.setStyleSheet(
            f"#dock{{background:{theme.BG_DOCK};"
            f"border-right:1px solid rgba(255,255,255,0.06);}}"
        )
        self.selected_index = 0
        self.buttons: list[QtWidgets.QPushButton] = []

        col = QtWidgets.QVBoxLayout(self)
        col.setContentsMargins(0, 8, 0, 8)
        col.setSpacing(4)
        col.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)

        for i, (icon, label) in enumerate(constants.DOCK_CATEGORIES):
            btn = self._dock_button(icon, label, i)
            self.buttons.append(btn)
            col.addWidget(btn, alignment=QtCore.Qt.AlignHCenter)

        self._restyle()

    # -- public API --------------------------------------------------------
    def select(self, index: int) -> None:
        self.selected_index = index
        self._restyle()
        self.categorySelected.emit(index)

    # -- helpers -----------------------------------------------------------
    def _dock_button(self, icon: str, label: str, index: int) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton()
        btn.setIcon(icons.make_icon(icon, "#788397", 18))
        btn.setIconSize(QtCore.QSize(18, 18))
        btn.setToolTip(label)
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setFixedSize(40, 40)
        btn.clicked.connect(lambda _=False, i=index: self.select(i))
        return btn

    def _restyle(self) -> None:
        for i, btn in enumerate(self.buttons):
            icon_name = constants.DOCK_CATEGORIES[i][0]
            if i == self.selected_index:
                btn.setIcon(icons.make_icon(icon_name, "#DCEAFC", 18))
                btn.setStyleSheet(
                    "QPushButton{border:none;border-radius:9px;"
                    "background:rgba(47,128,216,0.22);"
                    "border:1px solid rgba(47,128,216,0.55);}"
                )
            else:
                btn.setIcon(icons.make_icon(icon_name, "#788397", 18))
                btn.setStyleSheet(
                    "QPushButton{border:none;border-radius:9px;background:transparent;}"
                    "QPushButton:hover{background:rgba(47,128,216,0.12);}"
                )
