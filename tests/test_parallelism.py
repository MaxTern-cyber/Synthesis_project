"""Tests for tools.parallelism."""
from __future__ import annotations

import sys
from pathlib import Path

import networkx as nx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "launchers"))

import generate_sample_outputs as gso  # noqa: E402

from tools.parallelism import (  # noqa: E402
    levelize,
    profile,
)

SAMPLES = REPO_ROOT / "samples"


def _chain(n: int) -> nx.DiGraph:
    """A pure serial chain of n AND gates -- worst case for parallelism."""
    g = nx.DiGraph()
    g.add_node("in", kind="input")
    prev = "in"
    for i in range(n):
        node = f"g{i}"
        g.add_node(node, kind="and")
        g.add_edge(prev, node)
        prev = node
    g.add_node("out", kind="output")
    g.add_edge(prev, "out")
    return g


def _fan(n: int) -> nx.DiGraph:
    """n gates all driven by one input, all feeding one output -- best case."""
    g = nx.DiGraph()
    g.add_node("in", kind="input")
    g.add_node("out", kind="output")
    for i in range(n):
        gate = f"g{i}"
        g.add_node(gate, kind="and")
        g.add_edge("in", gate)
        g.add_edge(gate, "out")
    return g


def test_chain_is_fully_serial() -> None:
    g = _chain(10)
    r = profile(g)
    # 12 nodes (in + 10 gates + out), critical path = 12
    assert r.total_nodes == 12
    assert r.critical_path_length == 12
    assert r.max_width == 1
    assert r.theoretical_speedup == pytest.approx(1.0)


def test_fan_is_maximally_parallel() -> None:
    g = _fan(20)
    r = profile(g)
    # 22 nodes, critical path = 3 (in -> gate -> out)
    assert r.total_nodes == 22
    assert r.critical_path_length == 3
    # Middle level has 20 parallel gates
    assert r.max_width == 20
    # Speedup = 22/3 ~= 7.3
    assert r.theoretical_speedup > 7.0


def test_level_zero_is_source() -> None:
    g = _chain(3)
    levels = levelize(g)
    assert levels["in"] == 0
    assert levels["g0"] == 1
    assert levels["g1"] == 2
    assert levels["g2"] == 3
    assert levels["out"] == 4


def test_register_terminates_levelization() -> None:
    g = nx.DiGraph()
    g.add_node("in", kind="input")
    g.add_node("g1", kind="and")
    g.add_node("r", kind="reg")
    g.add_node("g2", kind="and")
    g.add_node("out", kind="output")
    g.add_edge("in", "g1")
    g.add_edge("g1", "r")
    g.add_edge("r", "g2")
    g.add_edge("g2", "out")

    levels = levelize(g)
    # Combinational view: in -> g1 isolated, r isolated, g2 -> out isolated
    # g2 has no predecessors in the combinational view -> level 0
    assert levels["g2"] == 0
    assert levels["out"] == 1


def test_partitions_count_combinational_cones() -> None:
    """Two independent combinational cones separated by a register."""
    g = nx.DiGraph()
    g.add_node("in", kind="input")
    g.add_node("g1", kind="and")
    g.add_node("r", kind="reg")
    g.add_node("g2", kind="and")
    g.add_node("out", kind="output")
    g.add_edge("in", "g1")
    g.add_edge("g1", "r")
    g.add_edge("r", "g2")
    g.add_edge("g2", "out")
    r = profile(g)
    # Two non-trivial cones: {in, g1} and {g2, out}
    assert r.partitions == 2


def test_width_per_level_sums_to_total() -> None:
    g = _fan(15)
    r = profile(g)
    assert sum(r.width_per_level.values()) == r.total_nodes


def test_verdict_categorizes_correctly() -> None:
    # Tiny -> "trivial"
    r_small = profile(_chain(3))
    assert "trivial" in r_small.verdict
    # Wide fan -> "excellent" (needs enough nodes)
    r_wide = profile(_fan(200))
    assert "excellent" in r_wide.verdict or "moderate" in r_wide.verdict


@pytest.mark.parametrize("fname,min_speedup,min_nodes", [
    ("c17.v",          2.0,    15),
    ("c432.v",         5.0,   300),
    ("array_mult8.v",  5.0,   300),
    ("array_mult16.v", 10.0, 1000),
])
def test_sample_parallelism_thresholds(fname: str, min_speedup: float, min_nodes: int) -> None:
    """Sanity-check measured speedup on real samples."""
    src = (SAMPLES / fname).read_text(encoding="utf-8")
    g, _ = gso.build_graph(src)
    r = profile(g)
    assert r.total_nodes >= min_nodes, f"{fname}: expected >= {min_nodes} nodes"
    assert r.theoretical_speedup >= min_speedup, (
        f"{fname}: speedup {r.theoretical_speedup:.2f}x below threshold {min_speedup}x"
    )


def test_array_mult16_is_gpu_candidate() -> None:
    """The headline result: 16x16 multiplier is the GL0AM-regime sweet spot."""
    src = (SAMPLES / "array_mult16.v").read_text(encoding="utf-8")
    g, _ = gso.build_graph(src)
    r = profile(g)
    assert r.theoretical_speedup > 10.0, (
        f"array_mult16 should land in GL0AM regime; got {r.theoretical_speedup:.2f}x"
    )
    assert r.max_width >= 100, (
        f"array_mult16 widest level should have >= 100 gates; got {r.max_width}"
    )
    assert "excellent" in r.verdict.lower() or "good" in r.verdict.lower()
