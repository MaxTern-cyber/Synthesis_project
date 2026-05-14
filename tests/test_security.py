"""Tests for the hardware-security ruleset."""
from __future__ import annotations

import networkx as nx
import pytest

from tools.security import (
    SecurityFinding,
    SecurityReport,
    Severity,
    audit,
    format_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_rule(report: SecurityReport, rule_id: str) -> bool:
    return any(f.rule_id == rule_id for f in report.findings)


def _rule_count(report: SecurityReport, rule_id: str) -> int:
    return sum(1 for f in report.findings if f.rule_id == rule_id)


# ---------------------------------------------------------------------------
# Rule 1: combinational loops
# ---------------------------------------------------------------------------

def test_clean_combinational_chain_has_no_findings() -> None:
    g = nx.DiGraph()
    g.add_node("in", kind="input")
    g.add_node("out", kind="output")
    g.add_node("g1", kind="and")
    g.add_edge("in", "g1")
    g.add_edge("g1", "out")
    report = audit(g)
    assert report.total == 0


def test_combinational_loop_is_flagged_high() -> None:
    g = nx.DiGraph()
    g.add_node("in", kind="input")
    g.add_node("out", kind="output")
    g.add_node("a", kind="and")
    g.add_node("b", kind="and")
    g.add_edge("in", "a")
    g.add_edge("a", "b")
    g.add_edge("b", "a")  # loop
    g.add_edge("b", "out")
    report = audit(g)
    assert _has_rule(report, "COMB_LOOP")
    loops = [f for f in report.findings if f.rule_id == "COMB_LOOP"]
    assert loops[0].severity == Severity.HIGH


def test_registered_loop_is_not_flagged() -> None:
    # a -> reg -> b -> a is sequentially valid, not a combinational loop.
    g = nx.DiGraph()
    g.add_node("in", kind="input")
    g.add_node("out", kind="output")
    g.add_node("a", kind="and")
    g.add_node("r", kind="reg")
    g.add_node("b", kind="and")
    g.add_edge("in", "a")
    g.add_edge("a", "r")
    g.add_edge("r", "b")
    g.add_edge("b", "a")
    g.add_edge("b", "out")
    report = audit(g)
    assert not _has_rule(report, "COMB_LOOP")


# ---------------------------------------------------------------------------
# Rule 2: reset gating
# ---------------------------------------------------------------------------

def test_direct_reset_to_register_no_gating() -> None:
    g = nx.DiGraph()
    g.add_node("clk", kind="input")
    g.add_node("rst", kind="input")
    g.add_node("d", kind="input")
    g.add_node("q", kind="output")
    g.add_node("r", kind="reg")
    g.add_edge("clk", "r")
    g.add_edge("rst", "r")
    g.add_edge("d", "r")
    g.add_edge("r", "q")
    report = audit(g)
    assert not _has_rule(report, "RESET_GATING")


def test_reset_through_and_gate_is_flagged() -> None:
    # rst is AND-ed with a functional signal before reaching the register.
    g = nx.DiGraph()
    g.add_node("clk", kind="input")
    g.add_node("rst", kind="input")
    g.add_node("mode", kind="input")
    g.add_node("d", kind="input")
    g.add_node("q", kind="output")
    g.add_node("gate", kind="and")
    g.add_node("r", kind="reg")
    g.add_edge("clk", "r")
    g.add_edge("rst", "gate")
    g.add_edge("mode", "gate")
    g.add_edge("gate", "r")
    g.add_edge("d", "r")
    g.add_edge("r", "q")
    report = audit(g)
    assert _has_rule(report, "RESET_GATING")
    findings = [f for f in report.findings if f.rule_id == "RESET_GATING"]
    assert findings[0].severity == Severity.HIGH


# ---------------------------------------------------------------------------
# Rule 3: async reset without synchronizer
# ---------------------------------------------------------------------------

def test_async_reset_with_synchronizer_is_not_flagged() -> None:
    # rst -> sync_reg -> use_reg : has a synchronizer stage on the path.
    g = nx.DiGraph()
    g.add_node("clk", kind="input")
    g.add_node("rst", kind="input")
    g.add_node("d", kind="input")
    g.add_node("q", kind="output")
    g.add_node("sync", kind="reg")
    g.add_node("r", kind="reg")
    g.add_edge("rst", "sync")
    g.add_edge("sync", "r")
    g.add_edge("clk", "r")
    g.add_edge("d", "r")
    g.add_edge("r", "q")
    report = audit(g)
    assert not _has_rule(report, "ASYNC_RESET_NO_SYNC")


def test_reset_input_directly_to_register_flagged_async() -> None:
    # rst goes straight from input to register, no comb gates, no sync.
    g = nx.DiGraph()
    g.add_node("rst", kind="input")
    g.add_node("d", kind="input")
    g.add_node("q", kind="output")
    g.add_node("r", kind="reg")
    g.add_edge("rst", "r")
    g.add_edge("d", "r")
    g.add_edge("r", "q")
    report = audit(g)
    assert _has_rule(report, "ASYNC_RESET_NO_SYNC")
    findings = [f for f in report.findings if f.rule_id == "ASYNC_RESET_NO_SYNC"]
    assert findings[0].severity == Severity.MEDIUM


# ---------------------------------------------------------------------------
# Rule 4: dangling logic
# ---------------------------------------------------------------------------

def test_no_dangling_logic_in_simple_design() -> None:
    g = nx.DiGraph()
    g.add_node("in", kind="input")
    g.add_node("out", kind="output")
    g.add_node("g", kind="and")
    g.add_edge("in", "g")
    g.add_edge("g", "out")
    report = audit(g)
    assert not _has_rule(report, "DANGLING_LOGIC")


def test_dangling_gate_is_flagged() -> None:
    g = nx.DiGraph()
    g.add_node("in", kind="input")
    g.add_node("out", kind="output")
    g.add_node("live", kind="and")
    g.add_node("dead", kind="and")  # has no path to output
    g.add_edge("in", "live")
    g.add_edge("live", "out")
    g.add_edge("in", "dead")
    report = audit(g)
    assert _has_rule(report, "DANGLING_LOGIC")


def test_large_dangling_cone_is_medium_severity() -> None:
    g = nx.DiGraph()
    g.add_node("in", kind="input")
    g.add_node("out", kind="output")
    g.add_node("live", kind="and")
    g.add_edge("in", "live")
    g.add_edge("live", "out")
    # 5-gate dead chain off the same input.
    prev = "in"
    for i in range(5):
        nid = f"dead{i}"
        g.add_node(nid, kind="and")
        g.add_edge(prev, nid)
        prev = nid
    report = audit(g)
    dangling = [f for f in report.findings if f.rule_id == "DANGLING_LOGIC"]
    assert any(f.severity == Severity.MEDIUM for f in dangling)


# ---------------------------------------------------------------------------
# Rule 5: multi-driver nets
# ---------------------------------------------------------------------------

def test_single_driver_net_is_clean() -> None:
    g = nx.DiGraph()
    g.add_node("in", kind="input")
    g.add_node("net1", kind="net")
    g.add_node("g", kind="and")
    g.add_node("out", kind="output")
    g.add_edge("in", "g")
    g.add_edge("g", "net1")
    g.add_edge("net1", "out")
    report = audit(g)
    assert not _has_rule(report, "MULTI_DRIVER")


def test_two_gates_driving_same_net_is_flagged() -> None:
    g = nx.DiGraph()
    g.add_node("a", kind="input")
    g.add_node("b", kind="input")
    g.add_node("g1", kind="and")
    g.add_node("g2", kind="or")
    g.add_node("net1", kind="net")
    g.add_node("out", kind="output")
    g.add_edge("a", "g1")
    g.add_edge("b", "g2")
    g.add_edge("g1", "net1")  # driver 1
    g.add_edge("g2", "net1")  # driver 2
    g.add_edge("net1", "out")
    report = audit(g)
    assert _has_rule(report, "MULTI_DRIVER")


# ---------------------------------------------------------------------------
# Report formatting + aggregation
# ---------------------------------------------------------------------------

def test_format_report_for_clean_graph() -> None:
    g = nx.DiGraph()
    g.add_node("in", kind="input")
    g.add_node("out", kind="output")
    g.add_edge("in", "out")
    text = format_report(audit(g))
    assert "no findings" in text.lower()


def test_format_report_lists_severities() -> None:
    g = nx.DiGraph()
    g.add_node("a", kind="and")
    g.add_node("b", kind="and")
    g.add_edge("a", "b")
    g.add_edge("b", "a")
    text = format_report(audit(g))
    assert "HIGH" in text
    assert "COMB_LOOP" in text


def test_findings_are_sorted_high_first() -> None:
    g = nx.DiGraph()
    # Mix: a high-severity loop + a low-severity dangling gate.
    g.add_node("in", kind="input")
    g.add_node("out", kind="output")
    g.add_node("a", kind="and")
    g.add_node("b", kind="and")
    g.add_edge("in", "a")
    g.add_edge("a", "b")
    g.add_edge("b", "a")
    g.add_edge("b", "out")
    g.add_node("dead", kind="and")
    g.add_edge("in", "dead")
    report = audit(g)
    severities = [f.severity for f in report.findings]
    # First finding must be HIGH (sorted desc by severity).
    assert severities[0] == Severity.HIGH


def test_severity_summary_counts_match() -> None:
    g = nx.DiGraph()
    g.add_node("a", kind="and")
    g.add_node("b", kind="and")
    g.add_edge("a", "b")
    g.add_edge("b", "a")
    report = audit(g)
    counts = report.by_severity
    assert counts[Severity.HIGH] == _rule_count(report, "COMB_LOOP")
    assert sum(counts.values()) == report.total
