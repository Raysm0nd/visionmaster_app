---
name: scaffold-node
description: Scaffold a new VisionPower processing node (OpenCV/model) following the project's node convention — registered class with typed ports, ParamSpecs, a run() method, and a test. Use when adding any new node to visionpower/nodes/.
---

# Scaffold a VisionPower node

A node is a **pure, stateless** transform: given its params and input-port
values, it returns output-port values. Statelessness keeps runs reproducible and
the incremental cache correct (see [scheduler.py](../../../visionpower/core/scheduler.py)).

## Steps

1. **Pick the module** under [visionpower/nodes/](../../../visionpower/nodes/):
   `sources.py` (produce images), `filters.py` (image→image), `analysis.py`
   (image→results/verdict), `sinks.py` (visualize/collect). Create a new module
   only for a genuinely new category, and add it to
   [nodes/__init__.py](../../../visionpower/nodes/__init__.py) so it gets imported
   (importing the module is what registers the node).

2. **Write the class** using this template:

   ```python
   @register_node
   class MyThingNode(Node):
       NODE_TYPE = "filters/MyThing"   # stable id "<category>/<Name>"
       CATEGORY = "filters"
       LABEL = "My Thing"               # shown in the UI palette
       INPUTS = [Port("image", PortType.IMAGE)]
       OUTPUTS = [Port("image", PortType.IMAGE)]
       PARAMS = [
           ParamSpec("strength", ParamType.INT, 5, min=1, max=99, step=2,
                     description="..."),
       ]

       def run(self, ctx, inputs):
           image = inputs["image"]            # keyed by input port name
           # ... use cv2 / numpy; read params via self.param("strength")
           return {"image": image}            # keyed by output port name
   ```

   Rules:
   - Output dict keys MUST match `OUTPUTS` port names; inputs arrive keyed by
     `INPUTS` port names. Optional inputs (`Port(..., optional=True)`) may be
     `None`.
   - Use only the core types from [types.py](../../../visionpower/core/types.py):
     `Image`, `Region`, `Measurement`, `Detection`/`DetectionItem`, `Verdict`.
   - Every tunable value is a `ParamSpec` (drives the auto property panel + LLM
     schema). Pick the right `ParamType`: INT/FLOAT (give min/max/step),
     BOOL, CHOICE (give `choices`), STRING, PATH.
   - Do **not** import Qt anywhere under `nodes/` or `core/`. Rendering helpers
     live in [render.py](../../../visionpower/render.py).

3. **Add a test** in [tests/](../../../tests/): build a tiny `Graph` with the node,
   run it with `Scheduler().run(graph)`, assert on outputs. Mirror the patterns in
   [test_engine.py](../../../tests/test_engine.py).

## Verify

```bash
uv run pytest -q
uv run python -c "from visionpower.core import node_schema; print([e['type'] for e in __import__('visionpower.nodes') or node_schema()])"
```
The new `NODE_TYPE` must appear in the schema and all tests must pass.
