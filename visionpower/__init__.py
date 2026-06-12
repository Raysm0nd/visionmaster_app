"""VisionPower — factory-floor image processing & defect detection platform.

Layered architecture (see plan):
  - ``visionpower.core``   : pure-Python engine (no Qt). Node/Graph/Scheduler.
  - ``visionpower.nodes``  : OpenCV / model / IO node implementations.
  - ``visionpower.app``    : PySide6 desktop UI (optional ``gui`` extra).
  - ``visionpower.service``: headless runner (future milestone).
"""

__version__ = "0.1.0"
