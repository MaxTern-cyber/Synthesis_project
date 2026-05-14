"""Parallelism profiler: DAG levelization + Brent's-bound speedup analysis.

Inspired by NVIDIA GL0AM (gate-level GPU simulator). Static analysis only.
"""
from .parallelism import (  # noqa: F401
    ParallelismReport,
    format_report,
    levelize,
    profile,
)
