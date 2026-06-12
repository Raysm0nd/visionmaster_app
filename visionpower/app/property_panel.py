"""Property panel: auto-generates parameter widgets from a node's ParamSpecs.

This is the payoff of the self-describing node schema — no per-node form code.
Editing a widget writes back to the core node and emits ``param_changed`` so the
main window can re-run the (incrementally cached) flow for live tuning.
"""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from visionpower.core import Node
from visionpower.core.params import ParamSpec, ParamType

_INT_LIMIT = 2_147_483_647


class PropertyPanel(QtWidgets.QWidget):
    param_changed = QtCore.Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._node: Node | None = None
        self._layout = QtWidgets.QVBoxLayout(self)
        self._title = QtWidgets.QLabel("未選取節點")
        self._title.setStyleSheet("font-weight: bold;")
        self._layout.addWidget(self._title)
        self._form_host = QtWidgets.QWidget()
        self._form = QtWidgets.QFormLayout(self._form_host)
        self._layout.addWidget(self._form_host)
        self._layout.addStretch(1)

    def show_node(self, node: Node | None) -> None:
        self._node = node
        self._clear_form()
        if node is None:
            self._title.setText("未選取節點")
            return
        self._title.setText(f"{node.LABEL or node.NODE_TYPE}")
        for spec in node.PARAMS:
            self._form.addRow(spec.name, self._make_widget(spec))
        if not node.PARAMS:
            self._form.addRow(QtWidgets.QLabel("（無參數）"))

    # -- widget construction ----------------------------------------------
    def _make_widget(self, spec: ParamSpec) -> QtWidgets.QWidget:
        value = self._node.param(spec.name)
        if spec.type is ParamType.INT:
            w = QtWidgets.QSpinBox()
            w.setRange(int(spec.min) if spec.min is not None else -_INT_LIMIT,
                       int(spec.max) if spec.max is not None else _INT_LIMIT)
            w.setSingleStep(int(spec.step) if spec.step else 1)
            w.setValue(int(value))
            w.valueChanged.connect(lambda v, s=spec: self._update(s, v))
            return self._with_tip(w, spec)
        if spec.type is ParamType.FLOAT:
            w = QtWidgets.QDoubleSpinBox()
            w.setRange(float(spec.min) if spec.min is not None else -1e12,
                       float(spec.max) if spec.max is not None else 1e12)
            w.setSingleStep(float(spec.step) if spec.step else 0.1)
            w.setDecimals(3)
            w.setValue(float(value))
            w.valueChanged.connect(lambda v, s=spec: self._update(s, v))
            return self._with_tip(w, spec)
        if spec.type is ParamType.BOOL:
            w = QtWidgets.QCheckBox()
            w.setChecked(bool(value))
            w.toggled.connect(lambda v, s=spec: self._update(s, v))
            return self._with_tip(w, spec)
        if spec.type is ParamType.CHOICE:
            w = QtWidgets.QComboBox()
            w.addItems(spec.choices or [])
            w.setCurrentText(str(value))
            w.currentTextChanged.connect(lambda v, s=spec: self._update(s, v))
            return self._with_tip(w, spec)
        if spec.type is ParamType.PATH:
            return self._path_widget(spec, str(value))
        # STRING
        w = QtWidgets.QLineEdit(str(value))
        w.editingFinished.connect(lambda w=w, s=spec: self._update(s, w.text()))
        return self._with_tip(w, spec)

    def _path_widget(self, spec: ParamSpec, value: str) -> QtWidgets.QWidget:
        host = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(host)
        row.setContentsMargins(0, 0, 0, 0)
        edit = QtWidgets.QLineEdit(value)
        button = QtWidgets.QPushButton("…")
        button.setFixedWidth(28)
        row.addWidget(edit)
        row.addWidget(button)
        edit.editingFinished.connect(lambda: self._update(spec, edit.text()))

        def browse() -> None:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Select image", "", "Images (*.png *.jpg *.jpeg *.bmp *.tif)"
            )
            if path:
                edit.setText(path)
                self._update(spec, path)

        button.clicked.connect(browse)
        host.setToolTip(spec.description)
        return host

    def _with_tip(self, w: QtWidgets.QWidget, spec: ParamSpec) -> QtWidgets.QWidget:
        if spec.description:
            w.setToolTip(spec.description)
        return w

    def _update(self, spec: ParamSpec, value) -> None:
        if self._node is None:
            return
        self._node.set_param(spec.name, value)
        self.param_changed.emit()

    def _clear_form(self) -> None:
        while self._form.count():
            item = self._form.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
