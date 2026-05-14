"""
sta.py -- STA-lite (Static Timing Analysis) over the Verilog DAG.

This is a deliberately small / illustrative timing analyzer for educational use.
It does NOT replace a real industrial STA engine. What it does:

1. Tags each edge with a `delay` derived from a unit-delay model keyed by the
   driver-node `kind` (nand=0.10ns, and=0.12ns, or=0.15ns, xor=0.20ns,
   not=0.05ns, generic instance=0.30ns, register=0.0ns boundary). Numbers are
   educational defaults, not silicon-accurate.
2. Forward DP over topological order -> arrival time for every node.
3. Backward DP from primary outputs / register inputs -> required time, given
   a target clock period.
4. Per-node slack = required - arrival. Negative slack = timing violation.
5. Backtracking yields the top-N longest (= slowest) paths.

Inputs are plain `networkx.DiGraph`s as produced by
`launchers.generate_sample_outputs.build_graph`. Cycles (e.g. a register
feedback loop) are handled by cutting at register nodes -- registers terminate
both the forward and backward sweep, which is the standard textbook treatment
for setup-time STA.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import networkx as nx

# ---------------------------------------------------------------------------
# Delay model
# ---------------------------------------------------------------------------

# Default per-kind gate delay (nanoseconds).
# Kept conservative + monotonic in fan-in count.
DEFAULT_DELAYS: dict[str, float] = {
    "nand":   0.10,
    "and":    0.12,
    "or":     0.15,
    "nor":    0.15,
    "xor":    0.20,
    "xnor":   0.20,
    "not":    0.05,
    "buf":    0.04,
    "inst":   0.30,   # opaque submodule -- assume worst-case combinational
    "reg":    0.00,   # boundary node; arrival resets at register
    "input":  0.00,
    "output": 0.00,
    "net":    0.00,
}


def edge_delay(g: nx.DiGraph, u: str, delays: dict[str, float]) -> float:
    """Delay attributed to driving node `u`."""
    kind = g.nodes.get(u, {}).get("kind", "net")
    return float(delays.get(kind, 0.0))


# ---------------------------------------------------------------------------
# Cycle cutting (cut at registers)
# ---------------------------------------------------------------------------

def _is_register(g: nx.DiGraph, n: str) -> bool:
    return g.nodes.get(n, {}).get("kind") == "reg"


def _combinational_dag(g: nx.DiGraph) -> nx.DiGraph:
    """
    Return a view-equivalent DAG with edges crossing register boundaries
    removed. Registers themselves remain as nodes (sources / sinks).
    """
    h = g.copy()
    # Cut outgoing register edges (register -> Q) and incoming register edges
    # (D -> register). After cutting both, the register becomes an isolated
    # node in the timing graph, which is exactly what we want: it terminates
    # both forward and backward sweeps.
    to_remove = [
        (u, v) for u, v in h.edges()
        if _is_register(h, u) or _is_register(h, v)
    ]
    h.remove_edges_from(to_remove)
    return h


# ---------------------------------------------------------------------------
# Forward + backward sweeps
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TimingReport:
    arrivals: dict[str, float]
    requireds: dict[str, float]
    slacks: dict[str, float]
    clock_period: float
    worst_slack: float
    worst_endpoint: str | None
    critical_path: list[str]
    delays: dict[str, float]


def compute_arrival_times(
    g: nx.DiGraph,
    delays: dict[str, float] | None = None,
    input_arrival: float = 0.0,
) -> dict[str, float]:
    """
    Forward DP: arrival[v] = max over predecessors u of (arrival[u] + delay(u)).
    Primary inputs / register outputs start at `input_arrival`.
    """
    delays = delays or DEFAULT_DELAYS
    h = _combinational_dag(g)
    arr: dict[str, float] = {}
    for v in nx.topological_sort(h):
        preds = list(h.predecessors(v))
        if not preds:
            arr[v] = input_arrival
        else:
            arr[v] = max(arr[u] + edge_delay(g, u, delays) for u in preds)
    return arr


def compute_required_times(
    g: nx.DiGraph,
    arrivals: dict[str, float],
    clock_period: float,
    delays: dict[str, float] | None = None,
) -> dict[str, float]:
    """
    Backward DP: required[u] = min over successors v of (required[v] - delay(u)).
    Endpoints (no successors in the combinational graph) take `clock_period`.
    """
    delays = delays or DEFAULT_DELAYS
    h = _combinational_dag(g)
    req: dict[str, float] = {}
    for v in reversed(list(nx.topological_sort(h))):
        succs = list(h.successors(v))
        if not succs:
            req[v] = clock_period
        else:
            d = edge_delay(g, v, delays)
            req[v] = min(req[s] - d for s in succs)
    return req


def compute_slacks(
    arrivals: dict[str, float],
    requireds: dict[str, float],
) -> dict[str, float]:
    return {n: requireds[n] - arrivals[n] for n in arrivals if n in requireds}


# ---------------------------------------------------------------------------
# Critical-path backtrace
# ---------------------------------------------------------------------------

def critical_path(
    g: nx.DiGraph,
    arrivals: dict[str, float],
    delays: dict[str, float] | None = None,
) -> list[str]:
    """
    Reconstruct the longest path through the combinational DAG by walking
    backwards from the worst endpoint along edges that tighten arrival.
    """
    delays = delays or DEFAULT_DELAYS
    h = _combinational_dag(g)
    endpoints = [n for n in h.nodes if h.out_degree(n) == 0 and n in arrivals]
    if not endpoints:
        return []
    end = max(endpoints, key=lambda n: arrivals[n])
    path = [end]
    cur = end
    while True:
        preds = list(h.predecessors(cur))
        if not preds:
            break
        # Pick predecessor that produced cur's arrival
        best = max(preds, key=lambda u: arrivals.get(u, 0.0) + edge_delay(g, u, delays))
        path.append(best)
        cur = best
    return list(reversed(path))


def analyze(
    g: nx.DiGraph,
    clock_period: float = 1.0,
    delays: dict[str, float] | None = None,
    input_arrival: float = 0.0,
) -> TimingReport:
    """One-shot wrapper: arrivals + requireds + slacks + critical path."""
    delays = delays or DEFAULT_DELAYS
    arr = compute_arrival_times(g, delays, input_arrival)
    req = compute_required_times(g, arr, clock_period, delays)
    slk = compute_slacks(arr, req)
    # Worst slack is reported AT THE ENDPOINT (out-degree-0 node), which is
    # the standard STA convention -- not at internal nodes or primary inputs.
    h = _combinational_dag(g)
    endpoint_slacks = {n: slk[n] for n in slk if h.out_degree(n) == 0}
    if endpoint_slacks:
        worst_ep = min(endpoint_slacks, key=lambda n: endpoint_slacks[n])
        worst = endpoint_slacks[worst_ep]
    else:
        worst_ep, worst = None, 0.0
    return TimingReport(
        arrivals=arr,
        requireds=req,
        slacks=slk,
        clock_period=clock_period,
        worst_slack=worst,
        worst_endpoint=worst_ep,
        critical_path=critical_path(g, arr, delays),
        delays=delays,
    )


# ---------------------------------------------------------------------------
# Top-N slowest endpoints
# ---------------------------------------------------------------------------

def top_n_slowest_endpoints(
    g: nx.DiGraph,
    arrivals: dict[str, float],
    n: int = 5,
) -> list[tuple[str, float]]:
    """Return [(endpoint, arrival)] for the N slowest endpoints."""
    h = _combinational_dag(g)
    endpoints = [
        (node, arrivals[node])
        for node in h.nodes
        if h.out_degree(node) == 0 and node in arrivals
    ]
    endpoints.sort(key=lambda x: -x[1])
    return endpoints[:n]


def format_report(report: TimingReport, max_path_nodes: int = 12) -> str:
    """Human-readable summary for CLI / Streamlit display."""
    lines = [
        f"STA-lite report",
        f"  Clock period      : {report.clock_period:.3f} ns",
        f"  Worst endpoint    : {report.worst_endpoint}",
        f"  Worst slack       : {report.worst_slack:+.3f} ns "
        f"({'VIOLATED' if report.worst_slack < 0 else 'MET'})",
        f"  Critical-path len : {len(report.critical_path)} nodes",
    ]
    if report.critical_path:
        shown = report.critical_path
        if len(shown) > max_path_nodes:
            head = shown[: max_path_nodes // 2]
            tail = shown[-max_path_nodes // 2 :]
            shown_disp: Iterable[str] = head + ["...({} hidden)...".format(len(shown) - max_path_nodes)] + tail
        else:
            shown_disp = shown
        lines.append("  Critical path     :")
        for i, n in enumerate(shown_disp):
            lines.append(f"    [{i:3d}]  {n}")
    return "\n".join(lines)
