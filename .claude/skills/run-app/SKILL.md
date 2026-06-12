---
name: run-app
description: Launch the VisionPower PySide6 desktop app, or run its workflow engine headless. Use when asked to start/run the app or execute a saved workflow.
---

# Run VisionPower

## Desktop app (developer machine with a display)

```bash
uv sync --extra gui          # one-time: install PySide6 + NodeGraphQt
uv run python main.py        # or: uv run visionpower
```

In the window: double-click a node in the **Nodes** palette to add it, drag
between ports to connect, select a node to edit its params in **Properties** and
see its image output in **Preview**. Toolbar: **Demo Flow** builds the sample
LoadImage→…→Viewer pipeline; **Run** executes; **Save/Load** persist the workflow
to JSON. Editing a parameter re-runs automatically (only changed nodes recompute).

## Headless server (no display, e.g. this Windows Server box)

Set the offscreen Qt platform so Qt does not require a display:

```bash
QT_QPA_PLATFORM=offscreen uv run python main.py   # runs but nothing visible
```

For headless you usually want the **engine**, not the window — build and run a
graph directly (no Qt needed at all):

```python
from visionpower.core import Graph, Scheduler, create_node, load_graph
import visionpower.nodes  # registers built-in nodes

graph = load_graph("flow.json")          # or build with create_node + graph.connect
results = Scheduler().run(graph)
for nid, r in results.items():
    print(nid, "OK" if r.ok else r.error, f"{r.elapsed_ms:.1f}ms")
```

## Notes
- Pure-engine work never needs the `gui` extra; `uv sync` (core only) is enough.
- To visually confirm a UI change without a display, use the `gui-verify` skill.
