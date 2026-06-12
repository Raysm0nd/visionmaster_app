"""Inference backend abstraction (model nodes land in milestone 2).

The backend is abstracted from day one so model nodes never hard-code a runtime.
The factory target is OpenVINO (Intel CPU); developer machines can fall back to
ONNXRuntime / OpenCV-DNN. Only the ABC is defined now — concrete backends and
model nodes are deferred per the plan.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class InferenceBackend(ABC):
    """Minimal contract a model-execution backend must satisfy."""

    @abstractmethod
    def load(self, model_path: str) -> None:
        """Load/compile a model from ``model_path`` (e.g. ONNX or OpenVINO IR)."""

    @abstractmethod
    def infer(self, blob: np.ndarray) -> Any:
        """Run inference on a preprocessed input blob and return raw outputs."""


# Milestone 2:
#   class OpenVINOBackend(InferenceBackend): ...  # openvino.Core, CPU plugin
#   class OnnxRuntimeBackend(InferenceBackend): ...  # dev fallback
