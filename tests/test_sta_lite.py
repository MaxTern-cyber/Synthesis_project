"""Tests for tools.sta_lite."""
from __future__ import annotations

import sys
from pathlib import Path

import networkx as nx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "launchers"))

import generate_sample_outputs as gso  # noqa: E402

from tools.sta_lite import (  # noqa: E402
    DEFAULT_DELAYS,
    analyze,
    compute_arrival_times,
    compute_required_times,
    compute_slacks,
    critical_path,
    top_n_slowest_endpoints,
)

SAMPLES = REPO_ROOT / "samples"


def _toy_chain() -> nx.DiGraph:
    """3-gate chain: A(input) -> g1(nand) -> g2(and) -> Y(output)."""
    g = nx.DiGraph()
    g.add_node("A", kind="input")
    g.add_node("g1", kind="nand")
    g.add_node("g2", kind="and")
    g.add_node("Y", kind="output")
    g.add_edge("A", "g1")
    g.add_edge("g1", "g2")
    g.add_edge("g2", "Y")
    return g


def test_toy_chain_arrivals() -> None:
    g = _toy_chain()
    arr = compute_arrival_times(g)
    assert arr["A"] == pytest.approx(0.0)
    # A drives g1 -> arrival(g1) = 0 + delay(A=input) = 0
    assert arr["g1"] == pytest.approx(0.0)
    # g1 drives g2 -> arrival(g2) = arrival(g1) + delay(nand) = 0.10
    assert arr["g2"] == pytest.approx(DEFAULT_DELAYS["nand"])
    # g2 drives Y -> arrival(Y) = arrival(g2) + delay(and) = 0.10 + 0.12 = 0.22
    assert arr["Y"] == pytest.approx(DEFAULT_DELAYS["nand"] + DEFAULT_DELAYS["and"])


def test_toy_chain_slack_met() -> None:
    g = _toy_chain()
    rep = analyze(g, clock_period=1.0)
    assert rep.worst_endpoint == "Y"
    # required(Y) - arrival(Y) = 1.0 - 0.22 = +0.78
    assert rep.worst_slack == pytest.approx(0.78)
    assert rep.worst_slack > 0  # MET


def test_toy_chain_slack_violated() -> None:
    g = _toy_chain()
    # Set clock too tight -> negative slack
    rep = analyze(g, clock_period=0.10)
    assert rep.worst_slack < 0


def test_critical_path_traversal() -> None:
    g = _toy_chain()
    rep = analyze(g, clock_period=1.0)
    assert rep.critical_path == ["A", "g1", "g2", "Y"]


def test_top_n_slowest_endpoints_sorted() -> None:
    g = nx.DiGraph()
    # Three independent endpoints with different depths
    g.add_node("in", kind="input")
    for i, depth in enumerate([1, 3, 2]):
        chain = [f"in"]
        for k in range(depth):
            n = f"g{i}_{k}"
            g.add_node(n, kind="and")
            chain.append(n)
        ep = f"out{i}"
        g.add_node(ep, kind="output")
        chain.append(ep)
        for a, b in zip(chain[:-1], chain[1:]):
            g.add_edge(a, b)

    arr = compute_arrival_times(g)
    top = top_n_slowest_endpoints(g, arr, n=3)
    assert len(top) == 3
    # First entry must be the deepest endpoint (chain length 3 -> out1)
    assert top[0][0] == "out1"
    # Sorted by arrival descending
    assert top[0][1] >= top[1][1] >= top[2][1]


@pytest.mark.parametrize("fname,expect_violation", [
    ("c17.v",         False),  # tiny, easy
    ("adder4.v",      True),   # 4-bit ripple-carry under 1ns -> tight
    ("array_mult8.v", True),   # 8x8 multiplier under 1ns -> violated
    ("c432.v",        True),   # ISCAS-85 under 1ns -> violated
])
def test_sample_timing(fname: str, expect_violation: bool) -> None:
    src = (SAMPLES / fname).read_text(encoding="utf-8")
    g, _ = gso.build_graph(src)
    rep = analyze(g, clock_period=1.0)
    if expect_violation:
        assert rep.worst_slack < 0, f"{fname}: expected violation"
    else:
        assert rep.worst_slack >= 0, f"{fname}: expected timing met"
    # Critical path must start at a source and end at the worst endpoint's chain
    assert len(rep.critical_path) >= 2


def test_register_terminates_sweep() -> None:
    """Registers cut the combinational graph -- arrival resets across them."""
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

    arr = compute_arrival_times(g)
    # Forward path: in -> g1 (still reaches g1)
    assert arr["g1"] == pytest.approx(0.0)
    # Register is isolated; downstream g2 starts fresh
    assert arr["g2"] == pytest.approx(0.0)


def test_required_times_pin_endpoints_to_clock() -> None:
    g = _toy_chain()
    arr = compute_arrival_times(g)
    req = compute_required_times(g, arr, clock_period=2.0)
    assert req["Y"] == pytest.approx(2.0)
    # required(g2) = required(Y) - delay(g2=and) = 2.0 - 0.12 = 1.88
    assert req["g2"] == pytest.approx(2.0 - DEFAULT_DELAYS["and"])


def test_slacks_consistent_with_arrival_required() -> None:
    g = _toy_chain()
    rep = analyze(g, clock_period=1.0)
    for n, s in rep.slacks.items():
        assert s == pytest.approx(rep.requireds[n] - rep.arrivals[n])
