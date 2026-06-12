"""DAG scheduler with incremental caching and per-node error isolation.

Incremental cache (the live-tuning UX core): each node gets a *signature*
derived from its type, its parameters, and the signatures of its upstream
producers. Because outputs are a pure function of inputs, the signature fully
determines the outputs. When you tweak one node's parameter, only that node's
signature (and its descendants') changes; unaffected upstream nodes hit the
cache and are NOT re-executed. ``NodeResult.cached`` reports this per node.

Error isolation: a failing node records its error; nodes downstream of a
failure (or of an unconnected required input) are reported as skipped rather
than crashing the whole run.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from visionpower.core.graph import Graph
from visionpower.core.node import NodeContext, NodeResult


class Scheduler:
    def __init__(self) -> None:
        # node_id -> (signature, outputs)
        self._cache: dict[str, tuple[str, dict[str, Any]]] = {}

    def invalidate(self, node_id: str | None = None) -> None:
        """Drop cached outputs for one node, or all if ``node_id`` is None."""

        if node_id is None:
            self._cache.clear()
        else:
            self._cache.pop(node_id, None)

    def run(self, graph: Graph, ctx: NodeContext | None = None) -> dict[str, NodeResult]:
        ctx = ctx or NodeContext()
        order = graph.topo_order()
        sigs: dict[str, str] = {}
        outputs_map: dict[str, dict[str, Any]] = {}
        results: dict[str, NodeResult] = {}

        for nid in order:
            node = graph.nodes[nid]
            conns = graph.inputs_of(nid)

            inputs, upstream_sigs, blocked = self._gather_inputs(
                node, conns, results, outputs_map, sigs
            )
            if blocked is not None:
                results[nid] = NodeResult(nid, {}, error=blocked)
                sigs[nid] = f"error:{nid}:{blocked}"
                outputs_map[nid] = {}
                continue

            sig = self._signature(node.NODE_TYPE, node.params, upstream_sigs)
            cached = self._cache.get(nid)
            if cached is not None and cached[0] == sig:
                outputs = cached[1]
                results[nid] = NodeResult(nid, outputs, cached=True)
            else:
                outputs, result = self._execute(node, ctx, inputs)
                self._cache[nid] = (sig, outputs)
                results[nid] = result

            sigs[nid] = sig
            outputs_map[nid] = outputs

        return results

    # -- helpers -----------------------------------------------------------
    @staticmethod
    def _gather_inputs(node, conns, results, outputs_map, sigs):
        """Collect input values + upstream signatures, or a 'blocked' reason."""

        inputs: dict[str, Any] = {}
        upstream_sigs: list[str] = []
        for port in node.INPUTS:
            conn = conns.get(port.name)
            if conn is None:
                if port.optional:
                    inputs[port.name] = None
                    upstream_sigs.append("none")
                    continue
                return inputs, upstream_sigs, f"required input {port.name!r} not connected"
            src_node, src_port = conn
            src_result = results.get(src_node)
            if src_result is None or not src_result.ok:
                return inputs, upstream_sigs, f"upstream {src_node!r} unavailable"
            inputs[port.name] = outputs_map[src_node][src_port]
            upstream_sigs.append(sigs[src_node])
        return inputs, upstream_sigs, None

    @staticmethod
    def _signature(node_type: str, params: dict, upstream_sigs: list[str]) -> str:
        blob = json.dumps(params, sort_keys=True, default=str)
        raw = f"{node_type}|{blob}|{'>'.join(upstream_sigs)}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _execute(node, ctx, inputs) -> tuple[dict, NodeResult]:
        t0 = time.perf_counter()
        try:
            outputs = node.run(ctx, inputs) or {}
            elapsed = (time.perf_counter() - t0) * 1000.0
            return outputs, NodeResult(node.id, outputs, elapsed_ms=elapsed)
        except Exception as exc:  # noqa: BLE001 - per-node isolation is intentional
            elapsed = (time.perf_counter() - t0) * 1000.0
            ctx.log(f"node {node.id} ({node.NODE_TYPE}) failed: {exc}")
            return {}, NodeResult(
                node.id, {}, elapsed_ms=elapsed, error=f"{type(exc).__name__}: {exc}"
            )
