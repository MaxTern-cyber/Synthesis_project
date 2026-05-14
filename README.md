# Synthesis Project -- AI-Assisted Hardware Design Analysis

> **An AI-assisted synthesis & hardware-security workflow prototype -- exploring how graph algorithms and LLM-style assistance can augment conventional EDA flows.**
>
> An open-source, local-first research prototype. Research-prototype quality, not production EDA.

[![CI](https://github.com/MaxTern-cyber/Synthesis_project/actions/workflows/ci.yml/badge.svg)](https://github.com/MaxTern-cyber/Synthesis_project/actions/workflows/ci.yml)
[![Live Demo](https://img.shields.io/badge/live%20demo-streamlit%20cloud-FF4B4B.svg)](https://synthesisproject-5ax4oq8wquyjmdgp6z9rvy.streamlit.app/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Type-checked: mypy](https://img.shields.io/badge/type--checked-mypy-2A6DB2.svg)](http://mypy-lang.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.53%2B-FF4B4B.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Topic: EDA](https://img.shields.io/badge/topic-EDA-blueviolet.svg)](#)
[![Topic: Verilog](https://img.shields.io/badge/topic-Verilog-orange.svg)](#)
[![Topic: Graph Algorithms](https://img.shields.io/badge/topic-Graph%20Algorithms-success.svg)](#)

> **Try it live:** [synthesisproject-5ax4oq8wquyjmdgp6z9rvy.streamlit.app](https://synthesisproject-5ax4oq8wquyjmdgp6z9rvy.streamlit.app/)
> -- pick a sample design (try `array_mult16.v` for the 1278-node visualization) or upload your own Verilog. Source: [streamlit_app.py](streamlit_app.py).

---

## Motivation

Modern synthesis, verification, and physical-design flows are predominantly **script-heavy** and **tool-license-locked**. Engineers spend significant time on tasks that are fundamentally **graph problems** on the netlist -- fanout exploration, cone tracing, combinational-loop detection, critical-path identification, FSM discovery -- yet day-to-day debugging is gated by commercial GUIs and TCL.

This project explores two questions:

1. **Can a local-first, open-source graph toolkit replicate the analytical core of commercial netlist analyzers** -- using only NetworkX, PyVis, and Streamlit?
2. **Where can AI-assistance plug into this flow** -- explaining waveforms, summarizing fanout cones, suggesting buffer insertions, detecting hardware-security anti-patterns (e.g. unprotected reset chains, suspicious clock-gating)?

The repo is a working prototype answering #1 today and a scaffold for #2 (`tools/demo2/ai_agent.py`, `tools/demo4/ai_agent.py`).

---

## Status

> Sample designs live in [`samples/`](samples/) -- five small textbook designs (adder, decoder, mux, traffic-light FSM, 3-stage pipeline) plus two **scale-demo** multipliers ([`array_mult8.v`](samples/array_mult8.v), [`array_mult16.v`](samples/array_mult16.v) -- the 16x16 builds to **1278 nodes / 1985 edges**). All are original public-domain designs written for this project -- zero third-party IP. Pre-generated interactive DAG visualizations live in [`outputs/`](outputs/). **Bring your own Verilog** too: any structural / gate-level `.v` works.
>
> Adding ISCAS-85 / OpenCores designs as additional samples is on the [roadmap](#roadmap).

---

## Screenshots & demo

**Scale demo -- full 16x16 array multiplier visualized as a DAG (1278 nodes / 1985 edges):**

![16x16 multiplier DAG](docs/images/scale-array_mult16.png)

| Close-up of gate-level nodes | Sequential / pipeline register graph |
|------------------------------|--------------------------------------|
| ![Multiplier node detail](docs/images/closeup-multiplier-nodes.png) | ![Pipeline registers](docs/images/pipeline-registers.png) |
| Color-coded nodes: `AND` gates (blue), `full_adder` instances (orange), signals (grey). Edges are net connections. | Diamond-shaped nodes are sequential elements (registers). Clock/reset trees fan out from `rst_n`. |

**Demo** -- 6-second walk-through of the analyzer ([download MP4](docs/media/demo.mp4)):

![Demo GIF](docs/media/demo.gif)

> *All visualizations are produced by [`launchers/generate_sample_outputs.py`](launchers/generate_sample_outputs.py) and live in [`outputs/`](outputs/). Open any `.html` file in a browser for full pan / zoom / hover.*

---

## Architecture

```mermaid
flowchart LR
 subgraph IN[Inputs]
 V[Verilog RTL / Gate-level netlist]
 X[Sample XML / IR]
 end

 subgraph PARSE[Parsing Layer]
 P1[Regex-based Verilog parser]
 P2[Instance & net extractor]
 P3[Library-cell classifier]
 end

 subgraph GRAPH[Graph Model - NetworkX DiGraph]
 G1[Nodes: gates / regs / IO]
 G2[Edges: driver -> sink nets]
 G3[Attrs: cell type, fanout, clock domain]
 end

 subgraph ALGO[Analysis Algorithms]
 A1[Fanout cone - reverse BFS]
 A2[Critical path - longest path on DAG]
 A3[Combinational loops - Tarjan SCC]
 A4[Clock-domain propagation - DFS]
 A5[FSM detection - register graph patterns]
 A6[I/O dependency chains - topological sort]
 end

 subgraph AI[AI-Assistance Layer - prototype]
 AI1[Cone summarization]
 AI2[Anomaly detection - security patterns]
 AI3[Buffer-insertion suggestions]
 end

 subgraph UI[Visualization & UI - Streamlit + PyVis + Plotly]
 U1[Interactive 2D / 3D DAG]
 U2[Per-signal drill-down]
 U3[Critical-path heatmap]
 U4[Reports - HTML / JSON]
 end

 IN --> PARSE --> GRAPH --> ALGO --> UI
 GRAPH --> AI --> UI
```

The flow is intentionally **graph-native end-to-end** -- every analysis is a query against the same `networkx.DiGraph`, which is the most general representation of a netlist after elaboration. This mirrors how modern EDA research (e.g., GNN-based timing prediction, NVIDIA's recent work on graph learning for circuits) increasingly treats post-synthesis netlists as first-class graph objects rather than HDL text.

---

## Algorithms -- Technical Depth

This is the engineering core. Each tool reuses the same `networkx.DiGraph` and composes the algorithms below.

### 1. Fanout-cone extraction -- reverse BFS

For a driver node $d$, the fanout cone is

$$\mathrm{Cone}(d) = \{ v \mid d \rightsquigarrow v \text{ in } G \}$$

Implemented as a **bounded-depth reverse BFS** (`networkx.descendants_at_distance`) so visualization stays interactive even on 10k+ gate designs. Depth-limit is a UI knob -- engineers usually care about levels 1-4.

### 2. Critical path -- longest path on DAG

Once combinational loops are broken at sequential boundaries, the timing graph is a DAG. The longest path is computed in $O(|V|+|E|)$ via topological-sort + DP -- no exponential search needed. Edge weights are unit (gate-count) by default; the architecture supports per-cell delay tables for future STA-lite extension.

### 3. Combinational-loop detection -- Tarjan's SCC

A combinational loop is a strongly connected component of size > 1 in the combinational sub-graph. Tarjan's algorithm finds all SCCs in $O(|V|+|E|)$. Each non-trivial SCC is reported with severity (CRITICAL / WARNING / INFO) based on cycle length and gate composition, with a suggestion of where to insert a register to break it.

### 4. Clock-domain propagation -- DFS with attribute tagging

Clock signals are seed-detected by regex (`clk`, `clock`, `_ck`, ...). A DFS from each clock source propagates the domain attribute through combinational nodes, halting at registers and IOs. This yields the **CDC (clock-domain-crossing) candidate set** for free -- any combinational node visited by two different domains is a CDC candidate.

### 5. FSM / pipeline detection -- register sub-graph patterns

The sub-graph induced by registers + their immediate combinational predecessors is matched against canonical FSM / pipeline templates (small strongly-connected register cliques -> FSM; long register chains -> pipeline). This is heuristic, not formal -- but it is fast and surfaces structural intent.

### 6. I/O dependency chains -- topological sort + path enumeration

For each primary input, a topological forward traversal yields all primary outputs influenced by it. The transitive-closure view exposes **dead inputs**, **dead outputs**, and **maximum logic depth per output** -- useful for both verification coverage and SoC-level timing budgeting. Detailed in [`docs/IO_CHAINS_FEATURE.md`](docs/IO_CHAINS_FEATURE.md).

### 7. AI-assistance hooks (prototype)

`tools/demo2/ai_agent.py` and `tools/demo4/ai_agent.py` provide an entry-point for LLM-driven assistance over the graph:

- **Cone summarization** -- natural-language explanation of "why is signal X high?" given the local fanin sub-graph.
- **Anomaly detection** -- pattern matching for hardware-security smells (unprotected resets, gated clocks without enable balancing, scan chains leaking into functional paths).
- **Buffer-insertion suggestions** -- heuristics over fanout x estimated load.

These are stubs today; the data model is what makes them tractable.

---

## Tooling

Seven tools, all built on the same graph core:

| # | Tool | Folder | Purpose |
|---|------|--------|---------|
| 1 | **Hardware Debug Assistant** | [`tools/demo3`](tools/demo3) | Signal tracing, fanout analysis, buffer planning |
| 2 | **Netlist Analyzer** | [`tools/demo2`](tools/demo2) | Interactive DAG + critical-path analysis + AI hooks |
| 3 | **RTL Analyzer** | [`tools/rtl_analyzer`](tools/rtl_analyzer) | Behavioral RTL analysis, FSM / pipeline detection |
| 4 | **Advanced Debugger** | [`tools/final_debugger`](tools/final_debugger) | Comprehensive debugger combining all algorithms |
| 5 | **DAG Visualizer** | [`tools/dag_visualizer`](tools/dag_visualizer) | Standalone interactive DAG generator |
| 6 | **Verilog DAG Tool** | [`tools/demo4`](tools/demo4) | Enhanced netlist analyzer variant |
| 7 | **Early prototype** | [`tools/demo1`](tools/demo1) | Original Verilog DAG / cone-tracing prototype |

---

## Repository Layout

```
.
|-- README.md # you are here
|-- LICENSE # MIT
|-- requirements.txt # Python dependencies for all tools
|-- .gitignore
|
|-- tools/ # all analyzer apps (Streamlit / Python)
| |-- demo1/ # early Verilog DAG prototype
| |-- demo2/ # Netlist Analyzer (port 8620)
| |-- demo3/ # Hardware Debug Assistant (port 8610)
| |-- demo4/ # Netlist Analyzer variant (port 8550)
| |-- rtl_analyzer/ # RTL Analyzer (port 8630)
| |-- final_debugger/ # Advanced Debugger (port 8640)
| \-- dag_visualizer/ # Standalone 3D DAG gen (port 8650)
|
|-- launchers/ # convenience scripts
|-- samples/ # textbook Verilog designs (see samples/README.md)
|-- outputs/ # pre-generated interactive DAG visualizations
|-- docs/ # extended documentation
\-- lib/ # PyVis static assets used by visualizations
```

---

## Quick Start

```powershell
# Clone
git clone https://github.com/MaxTern-cyber/Synthesis_project.git
cd Synthesis_project

# Set up environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Launch interactive menu
python launchers/PRESENTATION_LAUNCHER.py
```

### Install as a package (editable)

Prefer a proper Python package over loose scripts? The project ships a
PEP-621 [`pyproject.toml`](pyproject.toml), so you can install it in
editable mode and get console entry points on your `PATH`:

```powershell
pip install -e .                 # core install
pip install -e ".[dev,viz,export]"  # everything (tests, plots, Excel export)

# Installed console scripts:
synthesis-generate-outputs       # rebuild outputs/ for every sample
synthesis-generate-mult 24       # generate samples/array_mult24.v
synthesis-fix-unicode            # normalize stray unicode to ASCII
```

### Launch a single tool

| Tool | Command | URL |
|------|---------|-----|
| Hardware Debug Assistant | `streamlit run tools/demo3/debug_assistant.py --server.port 8610` | http://localhost:8610 |
| Netlist Analyzer | `streamlit run tools/demo2/local_analyzer.py --server.port 8620` | http://localhost:8620 |
| RTL Analyzer | `streamlit run tools/rtl_analyzer/rtl_analyzer.py --server.port 8630` | http://localhost:8630 |
| Advanced Debugger | `streamlit run tools/final_debugger/advanced_debugger.py --server.port 8640` | http://localhost:8640 |
| DAG Visualizer | `streamlit run tools/dag_visualizer/dag_visualizer.py --server.port 8650` | http://localhost:8650 |

Sample inputs: seven textbook designs ship in [`samples/`](samples/) -- try `samples/adder4.v` (critical path), `samples/decoder2to4.v` (fanout), `samples/fsm_traffic.v` (FSM detection), or **`samples/array_mult16.v`** (16x16 multiplier, ~1280 graph nodes -- scale demo). Pre-built interactive visualizations for each are in [`outputs/`](outputs/). Any other structural / gate-level Verilog `.v` works too.

### Regenerate sample outputs

```powershell
python launchers/generate_sample_outputs.py
```

### Generate a larger multiplier on demand

```powershell
python samples/generate_array_mult.py 24 # 24x24 -> ~3300 primitives
```

---

## Design Decisions

| Decision | Rationale |
|---|---|
| **NetworkX `DiGraph` as the single source of truth** | Decouples parsing from analysis; every algorithm is a graph query. Trivially swappable for `igraph` / `graph-tool` if performance demands. |
| **Regex parser, not a full SystemVerilog frontend** | Targeted at post-synthesis structural Verilog -- the format most relevant for analysis. Frees the project from an antlr/pyverilog dependency-tree and licensing concerns. |
| **Streamlit + PyVis instead of Qt/Tk** | Browser-based UI is friction-free for engineers, deploys to Streamlit Cloud with one click, and matches how modern EDA dashboards are evolving. |
| **Local-first, no cloud / no API keys** | Designs are IP. Anything that ships RTL or post-synth netlists to a third-party endpoint is a non-starter inside chip companies. AI hooks are designed to plug into **local** model backends. |
| **One folder per "demo" tool** | Each tool is an isolated Streamlit app that can be run/deployed/forked independently. |

---

## Limitations & Honest Disclaimers

- **No formal STA.** Critical path is gate-count-weighted, not delay-weighted. A delay-table plug-in is part of the roadmap.
- **Parser is structural-Verilog-only.** Generate-blocks, parameterised modules, and full SV constructs are out of scope.
- **AI-assistance hooks are scaffolds**, not production agents. They demonstrate where an LLM fits -- model selection (Llama-3, Phi-3, local Ollama) is intentionally pluggable.
- **No DRC / LVS** -- this is not a physical-design checker.
- Tested on small-to-medium open-source designs (<= ~10K gates). Scaling to multi-million-gate designs would require swapping NetworkX for a C++ graph backend.

---

## Roadmap

- ] **Delay-aware STA-lite** -- per-cell delay tables + arrival/required time propagation.
- ] **Local-LLM agent** -- Ollama-backed cone summarization (`Llama-3.2-3B-instruct`).
- ] **Hardware-security ruleset** -- codified anti-patterns for clock-gating, reset trees, scan-chain isolation.
- ] **GraphML / DEF export** -- interoperate with OpenROAD / Yosys / open-source PD flows.
- ] **GNN inference experiment** -- predict critical-path location from structural features. Inspired by recent NVIDIA Research work on graph learning for circuit analysis (NVIDIA GLOAM and related) and academic GNN-for-EDA papers -- see [CREDITS.md](CREDITS.md) for the full reference list.
- ] **CI** -- pytest suite + GitHub Actions on every push.
- ] **Streamlit Cloud deployment** -- public live demo.

Contributions and ideas welcome -- see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md) | Architecture, algorithms, internal API |
| [docs/USAGE_GUIDE.md](docs/USAGE_GUIDE.md) | Step-by-step usage examples |
| [docs/QUICK_START.md](docs/QUICK_START.md) | Fastest path to a running demo |
| [docs/IO_CHAINS_FEATURE.md](docs/IO_CHAINS_FEATURE.md) | I/O dependency-chain feature |
| [docs/ENHANCEMENTS_SUMMARY.md](docs/ENHANCEMENTS_SUMMARY.md) | Feature additions |
| [docs/LINKEDIN_POST.md](docs/LINKEDIN_POST.md) | Draft LinkedIn announcement |
| [docs/BLOG_POST.md](docs/BLOG_POST.md) | Long-form technical write-up |
| [CREDITS.md](CREDITS.md) | Sample-file provenance, third-party libraries, and academic references |

---

## Credits & references

All sample designs are original public-domain textbook circuits written
for this project. All third-party libraries are open source under
permissive licenses (BSD / MIT / Apache-2.0). See [CREDITS.md](CREDITS.md)
for the full attribution table, library license list, and academic
references underlying each algorithm.

---

## Author

**Mallikarjuna A L** -- EDA engineer building open-source tools for hardware verification.

- GitHub: [@MaxTern-cyber](https://github.com/MaxTern-cyber)
- LinkedIn: [mallikarjuna-a-l](https://www.linkedin.com/in/mallikarjuna-a-l)
- Email: mallikarjunaal.ec21@gmail.com

If you work in EDA, formal verification, synthesis, hardware security, or AI-for-chip-design -- I'd love to talk.

---

## License

[MIT](LICENSE) -- use freely, attribution appreciated.
