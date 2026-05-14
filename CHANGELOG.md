# Changelog

All notable changes to this project are documented here.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
on a best-effort basis (research prototype).

## [Unreleased]

### Added

- **Hardware-security audit** ([`tools/security/`](tools/security/)) --
  5-rule heuristic static-analysis pass over the netlist DAG:
  `COMB_LOOP` (Tarjan SCC), `RESET_GATING` (combinational gates on the
  reset path), `ASYNC_RESET_NO_SYNC` (no 2-FF synchronizer), `DANGLING_LOGIC`
  (cones with no observable sink -- a trojan hiding place), and
  `MULTI_DRIVER` (net contention). Findings carry severity (HIGH / MEDIUM /
  LOW), locus, description, and concrete suggested fix. Wired into the
  Streamlit app as Section 6.
- 16 new tests in `tests/test_security.py` covering every rule's positive
  and negative cases. Total test count: **52** (was 36).
- README section §2d documenting the ruleset, algorithm, and severity table.

### Changed

- CI mypy step now type-checks `tools/security` alongside the other modules.

## [0.1.0] - 2026-05-15

First tagged release. Established the project as a research prototype for
AI-assisted semiconductor design workflows.

### Added

- **Parser + DAG builder** ([`launchers/generate_sample_outputs.py`](launchers/generate_sample_outputs.py))
  -- regex-based Verilog parser handling structural primitive gates, named
  module instantiation, and behavioral RTL (registers + always blocks).
- **STA-lite** ([`tools/sta_lite/`](tools/sta_lite/)) -- educational static
  timing analyzer with forward/backward DP for arrival, required, and slack
  computation. Kind-keyed delay model (NAND=0.10ns, AND=0.12ns, ...).
- **Parallelism profile** ([`tools/parallelism/`](tools/parallelism/)) --
  GL0AM-inspired levelization + Brent's-bound theoretical-speedup analysis.
  Quantifies "is this design worth GPU-accelerating?"
- **DAG visualizer** ([`tools/dag_visualizer/`](tools/dag_visualizer/)) --
  interactive PyVis-based netlist explorer.
- **Streamlit Cloud demo** ([live](https://synthesisproject-5ax4oq8wquyjmdgp6z9rvy.streamlit.app/))
  -- unified entry point with sample picker, stats, queries, STA-lite,
  parallelism profile, and interactive DAG.
- **9 sample designs** including 2 ISCAS-85 benchmarks (`c17`, `c432`),
  5 textbook designs, and 2 parameterized array multipliers (the 16x16
  variant produces a 1278-node / 1985-edge graph).
- **36 unit tests** across parser, STA-lite, and parallelism modules.
- **CI workflow** -- pytest + mypy on Python 3.10 / 3.11 / 3.12.
- **PEP-621 packaging** -- `pip install -e .` with three console scripts.
- **Documentation** -- README with "Why this matters", architecture diagram,
  algorithms section, benchmarks tables, design decisions, limitations,
  and roadmap. Plus CREDITS, CONTRIBUTING, samples/README, outputs/README.

### Headline benchmark numbers

| Sample | Nodes | Critical path | Worst slack @ 1ns | Theoretical parallel speedup |
|---|---:|---:|---:|---:|
| `c17` (ISCAS-85) | 17 | 7 | +0.700 ns (MET) | 2.4x |
| `c432` (ISCAS-85) | 378 | 41 | -1.210 ns | **9.2x** |
| `array_mult16` | **1278** | 91 | -12.320 ns | **14.0x (GL0AM regime)** |

### Documented but not implemented (roadmap)

- Local-LLM agent (Ollama + Llama-3.2 / Phi-3) -- [#3](https://github.com/MaxTern-cyber/Synthesis_project/issues/3)
- GNN inference experiment -- [#4](https://github.com/MaxTern-cyber/Synthesis_project/issues/4)
- Hardware-security ruleset, GraphML / DEF export, larger ISCAS-85 designs

### Acknowledgements

Inspired by published research:

- **Yanqing Zhang, Mark Haoxing Ren (NVIDIA Research)** -- *"GL0AM:
  GPU-Accelerated Gate-Level Logic Simulator"* (DAC 2023). Open source:
  <https://github.com/NVlabs/GL0AM>. The `tools/parallelism` module
  implements static-analysis half of GL0AM's idea on CPU; it does not
  perform GPU simulation.
- ISCAS-85 benchmark suite (Brglez & Fujiwara, ISCAS 1985).

See [CREDITS.md](CREDITS.md) for full attribution.

[0.1.0]: https://github.com/MaxTern-cyber/Synthesis_project/releases/tag/v0.1.0
