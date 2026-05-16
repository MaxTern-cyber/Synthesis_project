"""
Smoke tests for the Verilog parser + DAG builder used in
launchers/generate_sample_outputs.py.

These tests intentionally only check coarse, stable properties (node counts,
edge counts, presence of expected node kinds) so they don't break on every
minor parser tweak. They are fast (sub-second) and dependency-light.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "launchers"))

import generate_sample_outputs as gso  # noqa: E402

SAMPLES = REPO_ROOT / "samples"


# (filename, min_nodes, min_edges, must_have_kinds)
CASES = [
    ("c17.v",            10, 10, {"nand"}),
    ("c432.v",          300, 400, {"nand", "not"}),
    ("c1908.v",         800, 1200, {"nand", "and", "not"}),
    ("c6288.v",        4000, 6000, {"and", "nor", "not"}),
    ("adder4.v",         10, 10, {"inst"}),
    ("decoder2to4.v",   10, 10, {"and", "not"}),
    ("mux4to1.v",       10, 10, {"and", "or", "not"}),
    ("fsm_traffic.v",    3,  3, {"reg"}),
    ("pipeline3.v",      3,  3, {"reg"}),
    ("array_mult8.v",  200, 300, {"and", "inst"}),
    ("array_mult16.v", 800, 1500, {"and", "inst"}),
]


@pytest.mark.parametrize("fname,min_nodes,min_edges,kinds", CASES)
def test_sample_graph(fname: str, min_nodes: int, min_edges: int, kinds: set[str]) -> None:
    src_path = SAMPLES / fname
    assert src_path.exists(), f"missing sample: {src_path}"
    src = src_path.read_text(encoding="utf-8")
    g, _meta = gso.build_graph(src)

    assert g.number_of_nodes() >= min_nodes, (
        f"{fname}: expected >= {min_nodes} nodes, got {g.number_of_nodes()}"
    )
    assert g.number_of_edges() >= min_edges, (
        f"{fname}: expected >= {min_edges} edges, got {g.number_of_edges()}"
    )

    present_kinds = {data.get("kind") for _, data in g.nodes(data=True)}
    missing = kinds - present_kinds
    assert not missing, f"{fname}: missing expected node kinds {missing}"


def test_strip_comments_removes_line_and_block_comments() -> None:
    src = "module m;\n// line comment\n  wire a; /* block\nspans */ wire b;\nendmodule\n"
    out = gso.strip_comments(src)
    assert "line comment" not in out
    assert "block" not in out
    assert "wire a;" in out
    assert "wire b;" in out


def test_parse_ports_basic() -> None:
    # The parser targets the body-style (non-ANSI) port declarations that
    # appear inside a module after the `;`, e.g.:
    #   input  wire        a;
    #   output reg  [7:0]  z;
    body = """
    input  wire        a;
    input  wire [3:0]  b;
    output reg         y;
    output wire [7:0]  z;
    """
    ins, outs = gso.parse_ports(body)
    assert "a" in ins and "b" in ins
    assert "y" in outs and "z" in outs


def test_array_mult_generator_produces_parseable_verilog(tmp_path: Path) -> None:
    """Round-trip: generator -> parser. Catches regressions in either."""
    sys.path.insert(0, str(REPO_ROOT / "samples"))
    import generate_array_mult as gen  # noqa: E402

    src = gen.emit(4)  # tiny 4x4 keeps the test fast
    g, _ = gso.build_graph(src)
    assert g.number_of_nodes() > 20, "4x4 multiplier should yield > 20 graph nodes"
