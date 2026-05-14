"""STA-lite: educational static timing analyzer over Verilog DAGs."""
from .sta import (  # noqa: F401
    DEFAULT_DELAYS,
    TimingReport,
    analyze,
    compute_arrival_times,
    compute_required_times,
    compute_slacks,
    critical_path,
    format_report,
    top_n_slowest_endpoints,
)
