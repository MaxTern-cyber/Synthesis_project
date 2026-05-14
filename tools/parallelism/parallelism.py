"""
parallelism.py -- DAG-based parallelism profiler for gate-level netlists.

Inspired by NVIDIA Research's GL0AM (GPU-Accelerated Gate-Level Logic
Simulator, Zhang & Ren, DAC'23/IEEE'25) -- which treats the netlist as a
levelized DAG to expose gate-level parallelism for GPU scheduling.

What this module does (CPU-only, analysis-only):

1. **Levelization.** Topological level of each node = longest path length
   from any primary input. Gates at the same level have no data dependency
   between them and can be evaluated in lock-step (one SIMD/SIMT step).

2. **Parallelism profile.** Histogram of gates-per-level. A wide-and-shallow
   shape means the design has lots of exploitable parallelism; tall-and-
   narrow means it is critical-path bound and hard to accelerate.

3. **Theoretical speedup (Brent's-bound).**

       speedup_max  =  total_work / critical_path_length
                    =  |gates|    / max_level

   This is an *upper bound* on parallel speedup for ANY parallel logic
   simulator on this design -- GPU, multi-threaded CPU, FPGA, whatever.

4. **Partitions.** Count of register-bounded combinational clusters. Each
   cluster is an independent simulation unit between two clock edges; more
   clusters -> easier to load-balance across GPU SMs (the exact problem
   that GL0AM-style partitioning addresses).

5. **Verdict.** Coarse "is this design worth GPU-accelerating?" tag based
   on the theoretical speedup.

The module does NOT do GPU simulation -- only the static analysis that tells
you whether GPU acceleration would pay off.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from statistics import median

import networkx as nx

# Boundary kinds: register endpoints + primary IO. These "terminate" the
# combinational graph for the purpose of parallelism analysis -- a register
# starts a fresh combinational cone on its Q output.
_BOUNDARY_KINDS = {"reg", "input", "output"}


# ---------------------------------------------------------------------------
# Combinational view
# ---------------------------------------------------------------------------

def _combinational_view(g: nx.DiGraph) -> nx.DiGraph:
    """Return a DAG with register-crossing edges removed.

    Registers themselves remain as isolated boundary nodes -- exactly what we
    want: levelization restarts after each register.
    """
    h = g.copy()
    to_drop = [
        (u, v) for u, v in h.edges()
        if h.nodes.get(u, {}).get("kind") == "reg"
        or h.nodes.get(v, {}).get("kind") == "reg"
    ]
    h.remove_edges_from(to_drop)
    return h


# ---------------------------------------------------------------------------
# Levelization
# ---------------------------------------------------------------------------

def levelize(g: nx.DiGraph) -> dict[str, int]:
    """Assign each node its topological level (longest path from a source).

    A source is any node with in-degree 0 in the combinational view -- which
    means primary inputs and register Q-outputs. Returns a dict mapping
    node-name -> int level (0 = source).
    """
    h = _combinational_view(g)
    level: dict[str, int] = {}
    for v in nx.topological_sort(h):
        preds = list(h.predecessors(v))
        level[v] = 0 if not preds else 1 + max(level[u] for u in preds)
    return level


# ---------------------------------------------------------------------------
# Parallelism report
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ParallelismReport:
    levels: dict[str, int]                 # node -> level
    width_per_level: dict[int, int]        # level -> number of nodes at that level
    total_nodes: int                       # |V| (combinational view)
    critical_path_length: int              # max_level + 1
    max_width: int                         # max gates simulable in one parallel step
    avg_width: float                       # mean width across levels
    median_width: float                    # median width across levels
    theoretical_speedup: float             # |V| / critical_path_length
    partitions: int                        # # of register-bounded combinational components
    verdict: str = field(default="")       # human-readable summary

    def as_table_row(self, name: str) -> list[str]:
        """Format as one row of the benchmark table."""
        return [
            name,
            str(self.total_nodes),
            str(self.critical_path_length),
            str(self.max_width),
            f"{self.theoretical_speedup:.2f}x",
            str(self.partitions),
            self.verdict,
        ]


def _verdict(theoretical_speedup: float, total_nodes: int) -> str:
    """Coarse 'is GPU-acceleration worth it' tag."""
    if total_nodes < 50:
        return "trivial - parallelism moot"
    if theoretical_speedup < 3.0:
        return "serial-bound - poor GPU candidate"
    if theoretical_speedup < 10.0:
        return "moderate - some speedup possible"
    return "excellent - good GPU candidate (GL0AM regime)"


def profile(g: nx.DiGraph) -> ParallelismReport:
    """One-shot parallelism analysis on a Verilog DAG."""
    h = _combinational_view(g)
    levels = levelize(g)

    if not levels:
        return ParallelismReport(
            levels={},
            width_per_level={},
            total_nodes=0,
            critical_path_length=0,
            max_width=0,
            avg_width=0.0,
            median_width=0.0,
            theoretical_speedup=0.0,
            partitions=0,
            verdict="empty design",
        )

    width_counter = Counter(levels.values())
    width_per_level = dict(sorted(width_counter.items()))

    total = len(levels)
    cp_len = max(levels.values()) + 1  # levels are 0-indexed
    max_width = max(width_per_level.values())
    widths = list(width_per_level.values())
    avg_width = total / cp_len
    med_width = median(widths)
    speedup = total / cp_len  # = avg_width by construction; kept explicit

    # Partitions = weakly connected components of the combinational view,
    # ignoring isolated boundary nodes (registers / IOs with no edges).
    # Each non-trivial WCC is an independent combinational cone.
    partitions = sum(
        1 for c in nx.weakly_connected_components(h)
        if len(c) > 1
    )

    return ParallelismReport(
        levels=levels,
        width_per_level=width_per_level,
        total_nodes=total,
        critical_path_length=cp_len,
        max_width=max_width,
        avg_width=avg_width,
        median_width=med_width,
        theoretical_speedup=speedup,
        partitions=partitions,
        verdict=_verdict(speedup, total),
    )


# ---------------------------------------------------------------------------
# Pretty printer
# ---------------------------------------------------------------------------

def format_report(report: ParallelismReport, max_levels_shown: int = 12) -> str:
    """Human-readable summary for CLI / Streamlit display."""
    lines = [
        "Parallelism profile",
        f"  Total nodes        : {report.total_nodes}",
        f"  Critical-path len  : {report.critical_path_length}",
        f"  Max width          : {report.max_width} gates per parallel step",
        f"  Avg width          : {report.avg_width:.2f}",
        f"  Median width       : {report.median_width:.1f}",
        f"  Theoretical speedup: {report.theoretical_speedup:.2f}x  (Brent's bound)",
        f"  Partitions         : {report.partitions}  (register-bounded cones)",
        f"  Verdict            : {report.verdict}",
    ]
    if report.width_per_level:
        lines.append("  Width per level:")
        items = list(report.width_per_level.items())
        if len(items) > max_levels_shown:
            head = items[: max_levels_shown // 2]
            tail = items[-max_levels_shown // 2 :]
            for lvl, w in head:
                lines.append(f"    L{lvl:3d}: {'#' * min(w, 60)} ({w})")
            lines.append(f"    ... ({len(items) - max_levels_shown} levels hidden) ...")
            for lvl, w in tail:
                lines.append(f"    L{lvl:3d}: {'#' * min(w, 60)} ({w})")
        else:
            for lvl, w in items:
                lines.append(f"    L{lvl:3d}: {'#' * min(w, 60)} ({w})")
    return "\n".join(lines)
