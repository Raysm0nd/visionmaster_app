"""Phase 5 (Red): self-drawn node canvas — hit-test, zoom, exec state machine."""

from __future__ import annotations

from visionpower.app.canvas import NodeCanvas, NodeView

_COLORS = ["#2DD4BF", "#5AA0E6", "#A78BFA", "#FBBF24", "#F472B6", "#34D399"]
_GLYPHS = ["image", "aim", "blob", "ocr", "str", "send"]


def _views(n: int = 6) -> list[NodeView]:
    return [
        NodeView(id=f"n{i}", index=i + 1, name=f"節點{i}", color=_COLORS[i], glyph=_GLYPHS[i])
        for i in range(n)
    ]


def test_set_nodes_populates_canvas(qapp):
    c = NodeCanvas()
    c.set_nodes(_views())
    assert len(c.nodes) == 6


def test_select_index_emits_node_id(qapp):
    c = NodeCanvas()
    c.set_nodes(_views())
    got = []
    c.nodeSelected.connect(got.append)
    c.select_index(2)
    assert c.selected_index == 2
    assert got == ["n2"]


def test_selection_is_single(qapp):
    c = NodeCanvas()
    c.set_nodes(_views())
    c.select_index(1)
    c.select_index(4)
    assert c.selected_index == 4


def test_hit_test_round_trips_card_centre(qapp):
    c = NodeCanvas()
    c.set_nodes(_views())
    c.resize(800, 902)
    for i in (0, 2, 5):
        centre = c._card_rect(i).center()
        widget_pt = c._content_to_widget(centre)
        assert c.node_at(widget_pt) == i


def test_hit_test_misses_empty_space(qapp):
    from PySide6 import QtCore

    c = NodeCanvas()
    c.set_nodes(_views())
    c.resize(800, 902)
    assert c.node_at(QtCore.QPoint(5, 5)) == -1


def test_zoom_in_out_reset(qapp):
    c = NodeCanvas()
    assert c.zoom == 100
    c.zoom_in()
    assert c.zoom == 125
    c.zoom_out()
    c.zoom_out()
    assert c.zoom == 75
    c.zoom_reset()
    assert c.zoom == 100
    assert c.zoom_label() == "100%"


def test_zoom_clamps_to_range(qapp):
    c = NodeCanvas()
    for _ in range(30):
        c.zoom_out()
    assert c.zoom == 25
    for _ in range(40):
        c.zoom_in()
    assert c.zoom == 400


def test_exec_state_machine_steps_through_nodes(qapp):
    c = NodeCanvas()
    c.set_nodes(_views())
    c.begin_run(0)
    assert c.running and c.ran_step == 0 and c.run_from == 0
    for expected in (1, 2, 3, 4, 5):
        assert c.advance_step() is True
        assert c.ran_step == expected
    assert c.advance_step() is False  # advanced past the last node
    assert not c.running and c.ran_step == -1


def test_partial_run_starts_from_selected(qapp):
    c = NodeCanvas()
    c.set_nodes(_views())
    c.select_index(3)
    c.begin_run(c.selected_index)
    assert c.run_from == 3 and c.ran_step == 3
