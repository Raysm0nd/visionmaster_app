"""Static layout data for the AXON shell — dimensions and the node-category dock.

Kept separate from ``theme`` (colours/fonts) so data tables and visual tokens
evolve independently. Values are transcribed from the approved design.
"""

from __future__ import annotations

# Fixed row/column dimensions from the design (px).
TITLE_H = 46
TOOLBAR_H = 54
STATUS_H = 30
DOCK_W = 56
RIGHT_W = 542

# Left icon dock: 12 node categories as (icon-key, 繁體中文 label) pairs.
DOCK_CATEGORIES: list[tuple[str, str]] = [
    ("camera", "影像擷取"),
    ("aim", "定位"),
    ("ruler", "量測"),
    ("scan", "辨識"),
    ("clock", "計數"),
    ("sliders", "標定"),
    ("layers", "邏輯"),
    ("bucket", "影像處理"),
    ("chart", "統計分析"),
    ("image", "顏色處理"),
    ("pencil", "標註"),
    ("branch", "條件分支"),
]
