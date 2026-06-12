---
name: gui-verify
description: Visually verify a VisionPower UI change by rendering the PySide6 window offscreen and capturing a screenshot, with no display required. Use to confirm the canvas/property panel/preview actually draw after a change.
---

# Verify the GUI offscreen

The dev box is headless, so render with Qt's `offscreen` platform and grab the
window to a PNG, then open the PNG to inspect it.

## Procedure

1. Ensure the GUI stack is installed: `uv sync --extra gui --group gui-dev`.
2. Write a short throwaway script (delete it after) like:

   ```python
   import os; os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
   from PySide6 import QtWidgets

   app = QtWidgets.QApplication([])
   from visionpower.app.theme import apply_theme
   apply_theme(app)                          # dark theme + bundled CJK font

   from visionpower.app.main_window import MainWindow
   win = MainWindow(); win.resize(1500, 900); win.show()
   win.build_demo_flow()    # no args: generates 4 synthetic samples + ImageSource

   # drive the preview via the display combo / source strip as needed, e.g.:
   win._find_image_source().set_param("index", 2)
   win.source_strip.select_row(2); win.run_flow()
   for _ in range(6): app.processEvents()

   os.makedirs("artifacts", exist_ok=True)
   win.grab().save("artifacts/app.png")
   # optional: switch to the 模組結果 tab and grab again
   win._tabs.setCurrentIndex(1)
   for _ in range(3): app.processEvents()
   win.grab().save("artifacts/app_results.png")
   print("ok:", all(r.ok for r in win.results.values()))
   ```

3. Run it: `QT_QPA_PLATFORM=offscreen uv run python <script>.py`
4. **Read** `artifacts/app.png` to inspect the result (palette / canvas / preview).
5. Delete the throwaway script, `_sample.png`, and `artifacts/` when done.

## What to look for / caveats
- Preview should show the processed image (e.g. red `defect` boxes + OK/NG banner
  baked by the Viewer node / `render.draw_overlay`).
- Expected chrome (VisionMaster-style): dark theme with orange accent, left
  節點工具 palette, vertical flow canvas, right 圖像/模組結果 tabs with the
  圖像源 thumbnail strip + cursor X/Y/RGB readout, bottom 歷史結果 table.
- Text (incl. Traditional Chinese) renders correctly even offscreen **only if**
  `apply_theme(app)` ran — it registers the bundled Noto Sans TC font from
  `visionpower/app/assets/fonts/`. If you see □ boxes, the theme wasn't applied.
- For non-visual logic, prefer the headless tests in `tests/test_bridge.py`
  (`QT_QPA_PLATFORM=offscreen uv run pytest`).
