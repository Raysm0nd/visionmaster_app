# VisionPower

A factory-floor **image-processing & defect-detection platform** with a
node-based, low-code workflow editor — inspired by Hikrobot VisionMaster. Build
inspection pipelines by wiring **nodes** on a canvas (OpenCV today, CPU models
next), tune parameters with live preview, and save/load workflows as JSON.

## Architecture

The guiding principle is **engine/UI decoupling**: the workflow engine is pure
Python with **zero Qt dependency**, so it can run headless (batch / factory
service) and be fully unit-tested. The UI, a future headless service, and a
future LLM/agent layer are all just consumers of the same engine.

```
 app (PySide6 UI)      service (headless, future)      agent (LLM, future)
 ─────────────────────────────────────────────────────────────────────────
 nodes   (OpenCV / model / IO node implementations)
 ─────────────────────────────────────────────────────────────────────────
 core    (pure Python, no Qt)
   types · ports · params · node · registry · graph · scheduler · serialize · inference
```

Key ideas:
- **Self-describing nodes.** Each node declares typed ports + `ParamSpec`s. That
  one schema powers the UI palette, the auto-generated property panel,
  connection type-validation, and the future LLM layer (`core.node_schema()`).
- **Incremental cache.** The scheduler signs each node by its params + upstream
  signatures; tweaking one parameter recomputes only that node and its
  descendants — the rest hit the cache (live tuning).
- **Per-node error isolation.** A failing node is reported, not fatal; downstream
  nodes are skipped.

### Layout
- [visionpower/core/](visionpower/core/) — engine (Qt-free)
- [visionpower/nodes/](visionpower/nodes/) — built-in OpenCV nodes
- [visionpower/render.py](visionpower/render.py) — overlay/display helpers (OpenCV, no Qt)
- [visionpower/app/](visionpower/app/) — PySide6 desktop UI + NodeGraphQt bridge
- [tests/](tests/) — engine tests + headless GUI-bridge tests

## Setup & run

```bash
uv sync                       # core engine + tests (no Qt)
uv sync --extra gui           # add the desktop UI stack (PySide6 + NodeGraphQt)
uv run python main.py         # launch the app  (or: uv run visionpower)
```

The UI follows the Hikrobot VisionMaster layout: dark theme (bundled Noto Sans
TC font), left 節點工具 palette, **vertical** flow canvas, right 圖像/模組結果
tabs (preview with cursor X/Y/RGB readout + 圖像源 thumbnail strip), 屬性 panel,
bottom 歷史結果 table. **示範流程** generates 4 synthetic samples and builds an
`ImageSource → Grayscale → GaussianBlur → Threshold → FindContours → Viewer`
pipeline; click thumbnails to switch images, **全部執行** batch-runs the whole
folder, parameter edits re-run incrementally, **儲存/載入** persist to JSON.

## Test

```bash
uv run pytest                                          # engine tests (no Qt)
uv sync --extra gui --group gui-dev
QT_QPA_PLATFORM=offscreen uv run pytest                # + headless GUI-bridge tests
```

## Roadmap
- **M1 (done)** — engine + OpenCV nodes + node editor + preview + save/load.
- **M1.5 (done)** — VisionMaster-style UI: dark theme + CJK font, ImageSource
  folder node + thumbnail strip + 全部執行 batch, module-results & history panels.
- **M2** — model nodes via an `InferenceBackend` (OpenVINO on Intel CPU; ONNX fallback).
- **M3** — NAS/folder sources + watch queue + parallel batch + result export.
- **M4** — headless service for unattended factory deployment.
- **M5** — LLM/agent assistance for workflow design & parameter suggestion.

Project-specific Claude Code skills live in [.claude/skills/](.claude/skills/):
`scaffold-node`, `run-app`, `gui-verify`.
