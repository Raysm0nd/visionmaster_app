"""Phase 6 (Red): MainWindow keeps the new UI wired to the real engine."""

from __future__ import annotations

from visionpower.app.main_window import MainWindow


def test_selecting_canvas_node_shows_its_params(qapp):
    win = MainWindow()  # demo flow seeded in __init__
    win.canvas.select_index(3)
    assert win.property_panel._node is win.bridge.nodes[3]


def test_run_all_executes_real_scheduler(qapp):
    win = MainWindow()
    win.run_all()
    assert win.results
    assert all(r.ok for r in win.results.values()), {
        k: r.error for k, r in win.results.items() if not r.ok
    }


def test_run_partial_from_selected_node(qapp):
    win = MainWindow()
    win.canvas.select_index(2)
    win.run_partial()
    assert win.results
    assert all(r.ok for r in win.results.values())


def test_param_change_triggers_incremental_rerun(qapp):
    win = MainWindow()
    win.run_all()
    thresh = next(n for n in win.bridge.nodes if n.NODE_TYPE == "filters/Threshold")
    thresh.set_param("thresh", 100)
    win._on_param_changed()
    by_type = {n.NODE_TYPE: win.results[n.id] for n in win.bridge.nodes}
    assert by_type["filters/GaussianBlur"].cached is True
    assert by_type["filters/Threshold"].cached is False
    assert by_type["analysis/FindContours"].cached is False


def test_save_load_roundtrip_rebuilds_runnable_flow(qapp, tmp_path):
    win = MainWindow()
    out = tmp_path / "flow.json"
    win.save_flow(str(out))

    win2 = MainWindow()
    win2.load_flow(str(out))
    assert [n.id for n in win2.bridge.nodes] == [n.id for n in win.bridge.nodes]
    win2.run_all()
    assert all(r.ok for r in win2.results.values())


def test_preview_updates_after_run(qapp):
    win = MainWindow()
    win.canvas.select_index(0)  # ImageSource
    win.run_all()
    # the selected node's image output should now be shown (pixmap present)
    assert win.right_panel.preview._pixmap is not None
