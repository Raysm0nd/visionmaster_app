"""Self-drawn blueprint node canvas (replaces NodeGraphQt).

Renders a vertical flow of node cards on a cyan blueprint grid, with selection,
run-time light-up animation, and zoom — all via QPainter. The widget is driven
by lightweight :class:`NodeView` models so it stays decoupled from the engine.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6 import QtCore, QtGui, QtWidgets

from visionpower.app import icons, theme

# Card layout (base, unscaled coordinates).
_TOP_PAD = 34
_CARD_W = 236
_CARD_H = 64
_GAP = 30
_STRIDE = _CARD_H + _GAP

_ZOOM_MIN, _ZOOM_MAX, _ZOOM_STEP = 25, 400, 25


@dataclass
class NodeView:
    """Lightweight display model for one node card."""

    id: str
    index: int
    name: str
    color: str
    glyph: str


class NodeCanvas(QtWidgets.QWidget):
    nodeSelected = QtCore.Signal(str)   # node id
    runFinished = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.nodes: list[NodeView] = []
        self.selected_index = -1
        self.zoom = 100
        self.running = False
        self.ran_step = -1
        self.run_from = 0
        self._run_time = "—"

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._on_timer)

        self._control_bar = _ControlBar(self)
        self.setMouseTracking(True)

    # -- model -------------------------------------------------------------
    def set_nodes(self, nodes: list[NodeView]) -> None:
        self.nodes = list(nodes)
        if self.selected_index >= len(self.nodes):
            self.selected_index = -1
        self.update()

    def set_run_time(self, text: str) -> None:
        self._run_time = text
        self._control_bar.set_time(text)

    # -- selection ---------------------------------------------------------
    def select_index(self, index: int) -> None:
        if 0 <= index < len(self.nodes):
            self.selected_index = index
            self.nodeSelected.emit(self.nodes[index].id)
            self.update()

    # -- zoom --------------------------------------------------------------
    def zoom_in(self) -> None:
        self._set_zoom(self.zoom + _ZOOM_STEP)

    def zoom_out(self) -> None:
        self._set_zoom(self.zoom - _ZOOM_STEP)

    def zoom_reset(self) -> None:
        self._set_zoom(100)

    def zoom_label(self) -> str:
        return f"{self.zoom}%"

    def _set_zoom(self, value: int) -> None:
        self.zoom = max(_ZOOM_MIN, min(_ZOOM_MAX, value))
        self._control_bar.set_zoom(self.zoom_label())
        self.update()

    # -- run animation -----------------------------------------------------
    def begin_run(self, from_index: int) -> None:
        self.running = True
        self.run_from = max(0, from_index)
        self.ran_step = self.run_from
        self.selected_index = self.run_from
        self.update()

    def advance_step(self) -> bool:
        """Advance one node. Returns False once stepped past the last node."""

        last = len(self.nodes) - 1
        if self.ran_step >= last:
            self.running = False
            self.ran_step = -1
            self.update()
            return False
        self.ran_step += 1
        self.selected_index = self.ran_step
        self.update()
        return True

    def start_run(self, from_index: int) -> None:
        """Begin the animated run (320ms/step), emitting runFinished at the end."""

        if self.running:
            return
        self.begin_run(from_index)
        self._timer.start(320)

    def _on_timer(self) -> None:
        if not self.advance_step():
            self._timer.stop()
            self.runFinished.emit()

    # -- geometry / hit-testing -------------------------------------------
    def _card_rect(self, i: int) -> QtCore.QRect:
        cx = self.width() / 2
        x = int(cx - _CARD_W / 2)
        y = _TOP_PAD + i * _STRIDE
        return QtCore.QRect(x, y, _CARD_W, _CARD_H)

    def _content_to_widget(self, point: QtCore.QPoint) -> QtCore.QPoint:
        z = self.zoom / 100
        cx = self.width() / 2
        sx = cx + (point.x() - cx) * z
        sy = point.y() * z
        return QtCore.QPoint(int(sx), int(sy))

    def _widget_to_content(self, point: QtCore.QPoint) -> QtCore.QPointF:
        z = self.zoom / 100
        cx = self.width() / 2
        bx = (point.x() - cx) / z + cx
        by = point.y() / z
        return QtCore.QPointF(bx, by)

    def node_at(self, point: QtCore.QPoint) -> int:
        content = self._widget_to_content(point)
        for i in range(len(self.nodes)):
            if self._card_rect(i).contains(content.toPoint()):
                return i
        return -1

    # -- events ------------------------------------------------------------
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.LeftButton:
            idx = self.node_at(event.position().toPoint())
            if idx >= 0:
                self.select_index(idx)
        super().mousePressEvent(event)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        self._control_bar.move(16, self.height() - self._control_bar.height() - 16)
        super().resizeEvent(event)

    # -- painting ----------------------------------------------------------
    def paintEvent(self, _event: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        self._paint_grid(p)
        z = self.zoom / 100
        cx = self.width() / 2
        p.translate(cx, 0)
        p.scale(z, z)
        p.translate(-cx, 0)
        for i in range(len(self.nodes)):
            if i < len(self.nodes) - 1:
                self._paint_connector(p, i)
        for i in range(len(self.nodes)):
            self._paint_card(p, i)
        p.end()

    def _paint_grid(self, p: QtGui.QPainter) -> None:
        p.fillRect(self.rect(), QtGui.QColor(theme.BG_CANVAS))
        pen = QtGui.QPen(QtGui.QColor(47, 128, 216, 26))
        pen.setWidth(1)
        p.setPen(pen)
        step = 26
        for x in range(0, self.width(), step):
            p.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), step):
            p.drawLine(0, y, self.width(), y)

    def _paint_connector(self, p: QtGui.QPainter, i: int) -> None:
        r0 = self._card_rect(i)
        x = r0.center().x()
        y1 = r0.bottom()
        y2 = self._card_rect(i + 1).top()
        flowing = self.running and self.ran_step > i
        color = QtGui.QColor(theme.ACCENT) if flowing else QtGui.QColor(255, 255, 255, 40)
        pen = QtGui.QPen(color, 2)
        if flowing:
            pen.setStyle(QtCore.Qt.DashLine)
        p.setPen(pen)
        p.drawLine(x, y1, x, y2)
        # arrowhead
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QColor(255, 255, 255, 70))
        p.drawPolygon(QtGui.QPolygonF([
            QtCore.QPointF(x - 4, y2 - 5), QtCore.QPointF(x + 4, y2 - 5), QtCore.QPointF(x, y2),
        ]))

    def _paint_card(self, p: QtGui.QPainter, i: int) -> None:
        node = self.nodes[i]
        r = self._card_rect(i)
        is_cur = self.running and self.ran_step == i
        is_done = self.running and self.ran_step > i
        is_sel = not self.running and self.selected_index == i

        # card surface
        p.setBrush(QtGui.QColor(11, 21, 34, 140))
        if is_cur or is_sel:
            border = QtGui.QColor(theme.ACCENT)
        elif is_done:
            border = QtGui.QColor(theme.SUCCESS)
        else:
            border = QtGui.QColor(47, 128, 216, 87)
        pen = QtGui.QPen(border, 1.6 if (is_cur or is_sel or is_done) else 1)
        p.setPen(pen)
        p.drawRoundedRect(r, 8, 8)

        # icon chip
        chip = QtCore.QRect(r.left() + 13, r.top() + 14, 36, 36)
        p.setPen(QtCore.Qt.NoPen)
        col = QtGui.QColor(node.color)
        chip_bg = QtGui.QColor(col)
        chip_bg.setAlpha(40)
        p.setBrush(chip_bg)
        p.drawRoundedRect(chip, 8, 8)
        pm = icons.make_pixmap(node.glyph, node.color, 18)
        p.drawPixmap(chip.left() + 9, chip.top() + 9, pm)

        # index + name
        tx = chip.right() + 12
        p.setPen(QtGui.QColor(theme.TEXT_FAINT))
        idx_font = QtGui.QFont(theme.FONT_MONO, 7)
        p.setFont(idx_font)
        p.drawText(tx, r.top() + 26, str(node.index))
        name_font = QtGui.QFont(theme.FONT_BODY, 10)
        name_font.setBold(True)
        p.setFont(name_font)
        p.setPen(QtGui.QColor(theme.TEXT))
        p.drawText(tx + 16, r.top() + 27, node.name)
        # status line
        p.setPen(QtGui.QColor(theme.TEXT_DIM))
        p.setFont(QtGui.QFont(theme.FONT_BODY, 8))
        status = "執行中…" if is_cur else "完成" if is_done else "已選取" if is_sel else "就緒"
        p.drawText(tx, r.top() + 46, status)

        # status dot
        dot_c = (QtGui.QColor(theme.ACCENT) if (is_cur or is_sel)
                 else QtGui.QColor(theme.SUCCESS) if is_done
                 else QtGui.QColor(58, 68, 86))
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(dot_c)
        p.drawEllipse(r.right() - 18, r.center().y() - 4, 8, 8)


class _ControlBar(QtWidgets.QWidget):
    """Floating glass bar (bottom-left): run-time + zoom controls."""

    def __init__(self, canvas: NodeCanvas) -> None:
        super().__init__(canvas)
        self._canvas = canvas
        self.setFixedHeight(36)
        self.setStyleSheet(
            "background:rgba(9,15,24,0.84);border:1px solid rgba(47,128,216,0.24);"
            "border-radius:11px;"
        )
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(13, 0, 7, 0)
        row.setSpacing(2)

        self._time = QtWidgets.QLabel("流程 —")
        self._time.setStyleSheet(
            f"color:{theme.TEXT_DIM};font-family:'{theme.FONT_MONO}',monospace;"
            f"font-size:11px;background:transparent;border:none;"
        )
        row.addWidget(self._time)
        row.addWidget(self._divider())
        row.addWidget(self._zbtn("zoomout", canvas.zoom_out))
        self._zoom = QtWidgets.QLabel("100%")
        self._zoom.setAlignment(QtCore.Qt.AlignCenter)
        self._zoom.setFixedWidth(46)
        self._zoom.setStyleSheet(
            f"color:#CFE2FB;font-family:'{theme.FONT_MONO}',monospace;font-size:11px;"
            f"background:transparent;border:none;"
        )
        self._zoom.mousePressEvent = lambda _e: canvas.zoom_reset()
        row.addWidget(self._zoom)
        row.addWidget(self._zbtn("search", canvas.zoom_in))
        self.adjustSize()

    def set_time(self, text: str) -> None:
        self._time.setText(f"流程 {text}")

    def set_zoom(self, text: str) -> None:
        self._zoom.setText(text)

    def _divider(self) -> QtWidgets.QFrame:
        line = QtWidgets.QFrame()
        line.setFixedSize(1, 17)
        line.setStyleSheet("background:rgba(255,255,255,0.13);border:none;")
        return line

    def _zbtn(self, icon: str, slot) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton()
        btn.setIcon(icons.make_icon(icon, "#9AA6B8", 16))
        btn.setIconSize(QtCore.QSize(16, 16))
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setFixedSize(27, 27)
        btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:7px;}"
            "QPushButton:hover{background:rgba(255,255,255,0.08);}"
        )
        btn.clicked.connect(slot)
        return btn
