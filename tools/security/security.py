"""
security.py -- heuristic hardware-security ruleset over the netlist DAG.

Five rules:

1. **COMB_LOOP** -- non-trivial strongly connected component in the
   combinational sub-graph (Tarjan SCC). Severity: HIGH. Combinational
   loops cause unpredictable evaluation order and are a classic vector
   for malicious oscillators ("ring-oscillator trojans").

2. **RESET_GATING** -- a net whose name matches ``reset|rst|rstn|reset_n``
   reaches a register only AFTER passing through at least one
   combinational gate. Severity: HIGH. Gating reset with functional
   logic creates a data-dependent reset path -- a known
   fault-injection / privilege-escalation surface.

3. **ASYNC_RESET_NO_SYNC** -- a reset-like net drives a register
   directly from a primary input with no intervening register stages
   (no 2-FF synchronizer). Severity: MEDIUM. Async-reset removal
   without synchronization is metastable and exploitable by glitch
   attacks.

4. **DANGLING_LOGIC** -- combinational node with no forward path to any
   primary output or register. Severity: LOW for isolated nodes,
   MEDIUM if the dangling cone is >= 5 nodes (large dead cones can hide
   a trojan payload that is only activated by a side-channel).

5. **MULTI_DRIVER** -- a signal net with more than one incoming edge
   from distinct gate/register nodes. Severity: HIGH. Multi-driver
   nets cause X-propagation in simulation and glitch / contention in
   silicon -- both observable, both exploitable.

This is a HEURISTIC analyzer, not a formal proof. False positives are
expected; the goal is to surface candidates for human review.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

import networkx as nx

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

# Reset-like net-name pattern. Conservative on purpose.
_RESET_RE = re.compile(r"(?:^|[/_])(?:reset|rst|resetn|rstn|reset_n|rst_n)(?:$|[/_])",
                       re.IGNORECASE)

# Combinational primitive kinds we levelize through.
_COMB_KINDS = {"and", "or", "nand", "nor", "xor", "xnor", "not", "buf",
               "inst", "net"}

_REG_KINDS = {"reg"}
_IO_KINDS = {"input", "output"}


class Severity(Enum):
    """Three-level severity ranking. Used for sort + count + UI color."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.name


@dataclass(frozen=True)
class SecurityFinding:
    """One rule violation. ``locus`` is a node id or short node-list string."""
    rule_id: str
    severity: Severity
    locus: str
    description: str
    suggestion: str


@dataclass
class SecurityReport:
    """Aggregate result of :func:`audit`."""
    findings: list[SecurityFinding] = field(default_factory=list)

    @property
    def by_severity(self) -> dict[Severity, int]:
        out = {s: 0 for s in Severity}
        for f in self.findings:
            out[f.severity] += 1
        return out

    @property
    def total(self) -> int:
        return len(self.findings)


# ---------------------------------------------------------------------------
# Combinational view (registers cut)
# ---------------------------------------------------------------------------

def _combinational_view(g: nx.DiGraph) -> nx.DiGraph:
    """DAG with edges touching register nodes removed."""
    h = g.copy()
    to_remove = [
        (u, v) for u, v in h.edges()
        if h.nodes.get(u, {}).get("kind") == "reg"
        or h.nodes.get(v, {}).get("kind") == "reg"
    ]
    h.remove_edges_from(to_remove)
    return h


def _is_reset_name(name: str) -> bool:
    return bool(_RESET_RE.search(name))


def _is_comb(g: nx.DiGraph, n: str) -> bool:
    return g.nodes.get(n, {}).get("kind") in _COMB_KINDS


# ---------------------------------------------------------------------------
# Rule 1: combinational loops
# ---------------------------------------------------------------------------

def _check_combinational_loops(g: nx.DiGraph) -> list[SecurityFinding]:
    comb = _combinational_view(g)
    findings: list[SecurityFinding] = []
    for scc in nx.strongly_connected_components(comb):
        if len(scc) < 2:
            continue
        sample = ", ".join(sorted(scc)[:4])
        if len(scc) > 4:
            sample += f", +{len(scc) - 4} more"
        findings.append(SecurityFinding(
            rule_id="COMB_LOOP",
            severity=Severity.HIGH,
            locus=sample,
            description=f"Combinational loop of {len(scc)} nodes detected "
                        f"(Tarjan SCC in the combinational sub-graph).",
            suggestion="Break the cycle by inserting a register, or confirm "
                       "the loop is an intentional latch / async memory.",
        ))
    return findings


# ---------------------------------------------------------------------------
# Rule 2 + 3: reset path analysis
# ---------------------------------------------------------------------------

def _reset_source_nodes(g: nx.DiGraph) -> list[str]:
    """Primary-input nodes whose name matches the reset pattern."""
    return [
        n for n, d in g.nodes(data=True)
        if d.get("kind") == "input" and _is_reset_name(n)
    ]


def _check_reset_paths(g: nx.DiGraph) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    reset_inputs = _reset_source_nodes(g)
    if not reset_inputs:
        return findings

    regs = {n for n, d in g.nodes(data=True) if d.get("kind") == "reg"}
    if not regs:
        return findings

    for src in reset_inputs:
        # Walk forward from this reset input until we hit a register.
        # Track the longest combinational chain length traversed.
        # If chain length >= 1 *with a combinational gate node on it*,
        # that is reset gating.
        for reg in regs:
            if not nx.has_path(g, src, reg):
                continue
            # Look at one shortest path -- representative enough.
            try:
                path = nx.shortest_path(g, src, reg)
            except nx.NetworkXNoPath:  # pragma: no cover - guarded above
                continue
            interior = path[1:-1]  # drop source + target
            comb_hops = [n for n in interior if _is_comb(g, n)]
            reg_hops = [n for n in interior if g.nodes.get(n, {}).get("kind") == "reg"]

            if comb_hops:
                findings.append(SecurityFinding(
                    rule_id="RESET_GATING",
                    severity=Severity.HIGH,
                    locus=f"{src} -> ... -> {reg}",
                    description=f"Reset input '{src}' reaches register "
                                f"'{reg}' through {len(comb_hops)} "
                                f"combinational gate(s): "
                                f"{', '.join(comb_hops[:3])}"
                                f"{'...' if len(comb_hops) > 3 else ''}.",
                    suggestion="Connect reset directly to the register's "
                               "asynchronous-reset pin; do not AND/OR it "
                               "with functional logic.",
                ))
            elif not reg_hops:
                # Direct reset_in -> reg edge, no synchronizer stage.
                # Exception: if this reg has a downstream register
                # successor, IT is acting as the synchronizer's first
                # flop -- don't flag.
                downstream_regs = [
                    s for s in g.successors(reg)
                    if g.nodes.get(s, {}).get("kind") == "reg"
                ]
                if downstream_regs:
                    continue
                findings.append(SecurityFinding(
                    rule_id="ASYNC_RESET_NO_SYNC",
                    severity=Severity.MEDIUM,
                    locus=f"{src} -> {reg}",
                    description=f"Reset input '{src}' drives register "
                                f"'{reg}' with no intervening synchronizer "
                                f"stage.",
                    suggestion="Insert a 2-flop synchronizer on the reset "
                               "net to prevent metastability and glitch "
                               "injection.",
                ))
    return findings


# ---------------------------------------------------------------------------
# Rule 4: dangling logic
# ---------------------------------------------------------------------------

def _check_dangling_logic(g: nx.DiGraph) -> list[SecurityFinding]:
    # Observable sinks: primary outputs + registers.
    sinks = {
        n for n, d in g.nodes(data=True)
        if d.get("kind") in _IO_KINDS - {"input"} or d.get("kind") == "reg"
    }
    # All ancestors of any sink = reachable-to-observable set.
    observable: set[str] = set()
    for s in sinks:
        observable.add(s)
        observable.update(nx.ancestors(g, s))

    # Dangling = combinational/inst nodes NOT in observable.
    dangling = [
        n for n, d in g.nodes(data=True)
        if d.get("kind") in _COMB_KINDS and n not in observable
    ]
    if not dangling:
        return []

    # Group by weakly-connected component within the dangling set so we
    # report cones, not individual gates.
    sub = g.subgraph(dangling).to_undirected()
    findings: list[SecurityFinding] = []
    for cone in nx.connected_components(sub):
        size = len(cone)
        severity = Severity.MEDIUM if size >= 5 else Severity.LOW
        sample = ", ".join(sorted(cone)[:3])
        if size > 3:
            sample += f", +{size - 3} more"
        findings.append(SecurityFinding(
            rule_id="DANGLING_LOGIC",
            severity=severity,
            locus=sample,
            description=f"Dangling cone of {size} combinational node(s) "
                        f"with no forward path to any primary output or "
                        f"register.",
            suggestion="Delete the dead logic, or, if intentional, document "
                       "why it exists. Large dead cones are a known "
                       "hardware-trojan hiding place.",
        ))
    return findings


# ---------------------------------------------------------------------------
# Rule 5: multi-driver nets
# ---------------------------------------------------------------------------

def _check_multi_driver(g: nx.DiGraph) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    for n, d in g.nodes(data=True):
        kind = d.get("kind")
        # Net-like sinks only (raw nets + primary outputs).
        if kind not in {"net", "output"}:
            continue
        drivers = [
            u for u in g.predecessors(n)
            if g.nodes.get(u, {}).get("kind") not in _IO_KINDS - {"output"}
        ]
        if len(drivers) <= 1:
            continue
        sample = ", ".join(sorted(drivers)[:3])
        if len(drivers) > 3:
            sample += f", +{len(drivers) - 3} more"
        findings.append(SecurityFinding(
            rule_id="MULTI_DRIVER",
            severity=Severity.HIGH,
            locus=n,
            description=f"Net '{n}' has {len(drivers)} distinct drivers: "
                        f"{sample}.",
            suggestion="Resolve contention by removing redundant drivers, "
                       "or replace with an explicit mux / tri-state if the "
                       "shared driver pattern is intentional.",
        ))
    return findings


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def audit(g: nx.DiGraph) -> SecurityReport:
    """Run all five rules and return a consolidated report."""
    findings: list[SecurityFinding] = []
    findings += _check_combinational_loops(g)
    findings += _check_reset_paths(g)
    findings += _check_dangling_logic(g)
    findings += _check_multi_driver(g)
    # Sort: severity desc, then rule_id asc, then locus asc.
    findings.sort(key=lambda f: (-f.severity.value, f.rule_id, f.locus))
    return SecurityReport(findings=findings)


def format_report(report: SecurityReport) -> str:
    """Pretty-print a security report as ASCII text."""
    if not report.findings:
        return "Security audit: no findings. (5 rules checked.)\n"
    counts = report.by_severity
    lines = [
        "Security audit",
        "=" * 60,
        f"Total findings: {report.total}  "
        f"(HIGH={counts[Severity.HIGH]}, "
        f"MEDIUM={counts[Severity.MEDIUM]}, "
        f"LOW={counts[Severity.LOW]})",
        "",
    ]
    for f in report.findings:
        lines.append(f"[{f.severity}] {f.rule_id}  @  {f.locus}")
        lines.append(f"    {f.description}")
        lines.append(f"    fix: {f.suggestion}")
        lines.append("")
    return "\n".join(lines)
