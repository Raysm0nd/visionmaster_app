"""Node implementations. Importing this package registers all built-in nodes.

Each submodule registers its node classes via ``@register_node`` at import
time, so ``import visionpower.nodes`` is enough to populate the registry.
"""

from visionpower.nodes import analysis, filters, sinks, sources  # noqa: F401

__all__ = ["sources", "filters", "analysis", "sinks"]
