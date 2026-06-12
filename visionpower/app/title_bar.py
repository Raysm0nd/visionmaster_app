"""Custom title bar for the frameless window — logo, menus, window controls.

Drag anywhere on the bar moves the window. Control buttons emit signals; the
host window decides what minimise/maximise/close actually do.
"""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from visionpower.app import icons, theme

_MENUS = ["檔案", "設定", "工具", "系統", "說明"]


class TitleBar(QtWidgets.QWidget):
    minimizeClicked = QtCore.Signal()
    maximizeClicked = QtCore.Signal()
    closeClicked = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setObjectName("titleBar")
        self.setStyleSheet(
            f"#titleBar{{background:{theme.BG_PANEL};"
            f"border-bottom:1px solid rgba(47,128,216,0.14);}}"
        )
        self._drag_offset: QtCore.QPoint | None = None

        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(14, 0, 8, 0)
        row.setSpacing(2)

        row.addWidget(self._build_logo())
        row.addSpacing(8)
        for label in _MENUS:
            row.addWidget(self._menu_button(label))
        row.addStretch(1)

        # right-side controls
        self.cloud_btn = self._chrome_button("cloud", "雲同步")
        self.gear_btn = self._chrome_button("gear", "設定")
        row.addWidget(self.cloud_btn)
        row.addWidget(self.gear_btn)
        row.addSpacing(8)
        self.min_btn = self._chrome_button("min", "最小化")
        self.max_btn = self._chrome_button("max", "最大化")
        self.close_btn = self._chrome_button("close", "關閉", danger=True)
        self.min_btn.clicked.connect(self.minimizeClicked)
        self.max_btn.clicked.connect(self.maximizeClicked)
        self.close_btn.clicked.connect(self.closeClicked)
        row.addWidget(self.min_btn)
        row.addWidget(self.max_btn)
        row.addWidget(self.close_btn)

    # -- public API --------------------------------------------------------
    def menu_labels(self) -> list[str]:
        return list(_MENUS)

    # -- construction helpers ---------------------------------------------
    def _build_logo(self) -> QtWidgets.QWidget:
        wrap = QtWidgets.QWidget()
        lay = QtWidgets.QHBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(11)

        badge = QtWidgets.QLabel()
        badge.setFixedSize(32, 32)
        badge.setPixmap(self._logo_pixmap())
        lay.addWidget(badge)

        text = QtWidgets.QWidget()
        tlay = QtWidgets.QVBoxLayout(text)
        tlay.setContentsMargins(0, 0, 0, 0)
        tlay.setSpacing(2)
        self.app_name_label = QtWidgets.QLabel("VisionPower")
        self.app_name_label.setStyleSheet(
            f"color:{theme.TEXT};font-family:'{theme.FONT_BRAND}','Noto Sans TC';"
            f"font-weight:700;font-size:15px;"
        )
        sub = QtWidgets.QLabel("MACHINE VISION")
        sub.setStyleSheet(
            f"color:{theme.TEXT_FAINT};font-size:8px;font-weight:600;"
            f"letter-spacing:3px;"
        )
        tlay.addWidget(self.app_name_label)
        tlay.addWidget(sub)
        lay.addWidget(text)
        return wrap

    def _logo_pixmap(self) -> QtGui.QPixmap:
        """Blue rounded badge with a white V and the AGC red corner."""

        dpr = 2
        pm = QtGui.QPixmap(32 * dpr, 32 * dpr)
        pm.fill(QtCore.Qt.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.scale(dpr, dpr)
        grad = QtGui.QLinearGradient(0, 0, 32, 32)
        grad.setColorAt(0, QtGui.QColor("#1162C6"))
        grad.setColorAt(1, QtGui.QColor("#0A3F86"))
        p.setBrush(grad)
        p.setPen(QtCore.Qt.NoPen)
        p.drawRoundedRect(0, 0, 32, 32, 9, 9)
        # red corner triangle
        p.setBrush(QtGui.QColor(theme.RED))
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(20, 0), QtCore.QPointF(32, 0), QtCore.QPointF(32, 12)]))
        # white V
        pen = QtGui.QPen(QtGui.QColor("#EAF2FC"), 2.5)
        pen.setJoinStyle(QtCore.Qt.RoundJoin)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        p.setPen(pen)
        path = QtGui.QPainterPath(QtCore.QPointF(7, 9))
        path.lineTo(16, 25)
        path.lineTo(25, 9)
        p.drawPath(path)
        p.end()
        pm.setDevicePixelRatio(dpr)
        return pm

    def _menu_button(self, label: str) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton(label)
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setFlat(True)
        btn.setFixedHeight(28)
        btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;border-radius:7px;"
            f"color:#C2CCDA;font-size:13px;padding:0 11px;}}"
            f"QPushButton:hover{{background:rgba(255,255,255,0.07);}}"
        )
        return btn

    def _chrome_button(self, icon: str, tip: str, danger: bool = False) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton()
        btn.setIcon(icons.make_icon(icon, "#8693A6", 16))
        btn.setIconSize(QtCore.QSize(16, 16))
        btn.setToolTip(tip)
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setFixedSize(30, 30)
        hover = theme.RED if danger else "rgba(255,255,255,0.07)"
        btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;border-radius:7px;}}"
            f"QPushButton:hover{{background:{hover};}}"
        )
        return btn

    # -- window dragging ---------------------------------------------------
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.LeftButton:
            win = self.window()
            self._drag_offset = event.globalPosition().toPoint() - win.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._drag_offset is not None and event.buttons() & QtCore.Qt.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)
