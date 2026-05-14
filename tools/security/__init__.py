"""Hardware-security ruleset: heuristic static analysis over the netlist DAG.

Five rules: combinational loops, reset gating, async reset without
synchronizer, dangling logic (potential trojan), and multi-driver nets.
"""
from .security import (  # noqa: F401
    SecurityFinding,
    SecurityReport,
    Severity,
    audit,
    format_report,
)
