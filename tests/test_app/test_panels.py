"""Phase 4 (Red): left dock + right inspection panel (tabs, preview, results)."""

from __future__ import annotations

import numpy as np

from visionpower.app.dock import Dock
from visionpower.app.panels import RightPanel
from visionpower.app.preview_view import PreviewView
from visionpower.core import NodeResult
from visionpower.core.types import Detection, DetectionItem, Verdict


# -------------------------------------------------------------------- Dock
def test_dock_renders_twelve_categories(qapp):
    dock = Dock()
    assert len(dock.buttons) == 12


def test_dock_select_updates_index_and_emits(qapp):
    dock = Dock()
    fired = []
    dock.categorySelected.connect(fired.append)
    dock.select(3)
    assert dock.selected_index == 3
    assert fired == [3]


# -------------------------------------------------------------- RightPanel
def test_right_panel_defaults_to_image_tab(qapp):
    panel = RightPanel()
    assert panel.current_tab() == "image"


def test_right_panel_switches_to_result_tab(qapp):
    panel = RightPanel()
    panel.show_result_tab()
    assert panel.current_tab() == "result"
    panel.show_image_tab()
    assert panel.current_tab() == "image"


def test_right_panel_has_property_tab(qapp):
    # design has 源圖/輸出結果; 屬性 added to keep node-param editing wired
    panel = RightPanel()
    assert hasattr(panel, "property_panel")


def test_result_table_renders_key_values_from_node_result(qapp):
    panel = RightPanel()
    det = Detection(items=[DetectionItem(bbox=(40, 40, 20, 20), label="blob", area=400.0)])
    result = NodeResult(
        node_id="contours",
        outputs={"detections": det, "verdict": Verdict(ok=True, reasons=[])},
        elapsed_ms=1.8,
    )
    panel.show_result("FindContours", result)
    assert panel.result_row_count() >= 1


# ------------------------------------------------------------- PreviewView
def test_preview_show_bgr_and_running_toggle_do_not_crash(qapp):
    pv = PreviewView()
    img = np.zeros((40, 60, 3), dtype=np.uint8)
    pv.show_bgr(img, "sample.png")
    pv.set_running(True)
    pv.set_running(False)
    pv.clear("無預覽")


def test_preview_emits_prev_next(qapp):
    pv = PreviewView()
    seen = []
    pv.prevImage.connect(lambda: seen.append("prev"))
    pv.nextImage.connect(lambda: seen.append("next"))
    pv.prev_btn.click()
    pv.next_btn.click()
    assert seen == ["prev", "next"]
