"""Phase 3 (Red): frameless shell — title bar, toolbar, window controls."""

from __future__ import annotations

from PySide6 import QtCore

from visionpower.app.title_bar import TitleBar
from visionpower.app.toolbar import Toolbar
from visionpower.app.main_window import MainWindow


# ---------------------------------------------------------------- TitleBar
def test_title_bar_shows_brand_and_five_menus(qapp):
    tb = TitleBar()
    assert tb.app_name_label.text() == "VisionPower"
    assert tb.menu_labels() == ["檔案", "設定", "工具", "系統", "說明"]


def test_title_bar_control_buttons_emit_signals(qapp):
    tb = TitleBar()
    got = {"min": 0, "max": 0, "close": 0}
    tb.minimizeClicked.connect(lambda: got.__setitem__("min", got["min"] + 1))
    tb.maximizeClicked.connect(lambda: got.__setitem__("max", got["max"] + 1))
    tb.closeClicked.connect(lambda: got.__setitem__("close", got["close"] + 1))
    tb.min_btn.click()
    tb.max_btn.click()
    tb.close_btn.click()
    assert got == {"min": 1, "max": 1, "close": 1}


# ----------------------------------------------------------------- Toolbar
def test_toolbar_has_run_all_and_run_partial(qapp):
    tbar = Toolbar()
    assert "執行全部" in tbar.run_all_btn.text()
    assert "部分執行" in tbar.run_partial_btn.text()


def test_toolbar_run_buttons_emit_signals(qapp):
    tbar = Toolbar()
    fired = []
    tbar.runAll.connect(lambda: fired.append("all"))
    tbar.runPartial.connect(lambda: fired.append("partial"))
    tbar.run_all_btn.click()
    tbar.run_partial_btn.click()
    assert fired == ["all", "partial"]


# --------------------------------------------------------------- MainWindow
def test_window_is_frameless(qapp):
    win = MainWindow()
    assert bool(win.windowFlags() & QtCore.Qt.FramelessWindowHint)


def test_window_embeds_title_bar_and_toolbar(qapp):
    win = MainWindow()
    assert isinstance(win.title_bar, TitleBar)
    assert isinstance(win.toolbar, Toolbar)


def test_toggle_max_flips_state(qapp):
    win = MainWindow()
    assert win.toggle_max() is True
    assert win.toggle_max() is False


def test_maximize_restores_previous_geometry(qapp):
    win = MainWindow()
    win.show()
    win.resize(1100, 720)
    before = win.geometry()
    win.toggle_max()   # fill available screen
    win.toggle_max()   # restore
    assert win.geometry() == before


def test_window_uses_pure_frameless_flag(qapp):
    # Extra window-button hints make Windows draw native caption buttons that
    # overlap (and swallow clicks on) our custom controls — keep it pure.
    win = MainWindow()
    flags = win.windowFlags()
    assert bool(flags & QtCore.Qt.FramelessWindowHint)
    assert not (flags & QtCore.Qt.WindowMaximizeButtonHint)


def test_minimize_call_does_not_crash(qapp):
    win = MainWindow()
    win.show()
    win.showMinimized()  # must not raise on a frameless window
    win.showNormal()


def test_panels_are_fixed_size_not_user_adjustable(qapp):
    # canvas + right panel sit in a plain layout — no splitter/dock to drag.
    win = MainWindow()
    assert win.right_panel.minimumWidth() == win.right_panel.maximumWidth()  # fixed 542
    assert win.dock.width() == 56


def test_close_button_hides_window(qapp):
    win = MainWindow()
    win.show()
    assert win.isVisible()
    win.title_bar.closeClicked.emit()
    assert not win.isVisible()


# --------------------------------------------------- sizing / resizing
def test_window_has_minimum_size(qapp):
    win = MainWindow()
    assert win.minimumWidth() >= 800
    assert win.minimumHeight() >= 600


def test_fitted_geometry_fits_within_small_screen(qapp):
    avail = QtCore.QRect(0, 0, 1280, 720)
    g = MainWindow._fitted_geometry(avail)
    assert g.width() <= 1280 and g.height() <= 720
    assert g.x() >= 0 and g.y() >= 0  # centred, on-screen


def test_fitted_geometry_caps_at_design_size_on_large_screen(qapp):
    avail = QtCore.QRect(0, 0, 3840, 2160)
    g = MainWindow._fitted_geometry(avail)
    assert g.width() <= 1440 and g.height() <= 902


def test_resize_edge_detects_corners_and_centre(qapp):
    win = MainWindow()
    win.resize(1200, 800)  # >= minimum size so the geometry is honoured
    assert win._resize_edge(QtCore.QPoint(1, 1)) == 13       # HTTOPLEFT
    assert win._resize_edge(QtCore.QPoint(1199, 799)) == 17  # HTBOTTOMRIGHT
    assert win._resize_edge(QtCore.QPoint(600, 400)) == 0    # interior, no resize
