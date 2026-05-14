# Credits, References & Sources

This document is the single source of truth for **where everything in this
repository comes from** -- sample designs, third-party libraries, and the
algorithmic / academic references that informed the analyzers.

Everything listed here is **open source** under a permissive license
(MIT / BSD / Apache-2.0 / Public Domain). Nothing in this repository is
derived from proprietary EDA tools or NDA-covered designs.

---

## 1. Sample designs ([`samples/`](samples/))

All Verilog sample files were **written from scratch for this project** as
original textbook-style designs. They are released into the public domain
along with the rest of this repo under [MIT](LICENSE).

| File | Origin | Inspiration |
|------|--------|-------------|
| [`samples/adder4.v`](samples/adder4.v) | Original | Standard 4-bit ripple-carry adder taught in any digital-design course |
| [`samples/decoder2to4.v`](samples/decoder2to4.v) | Original | Standard 2-to-4 decoder with enable |
| [`samples/mux4to1.v`](samples/mux4to1.v) | Original | Standard 4-to-1 multiplexer |
| [`samples/fsm_traffic.v`](samples/fsm_traffic.v) | Original | Classic 4-state traffic-light controller FSM example |
| [`samples/pipeline3.v`](samples/pipeline3.v) | Original | Generic 3-stage register pipeline |
| [`samples/array_mult8.v`](samples/array_mult8.v) | Generated | Braun array multiplier topology (textbook, public domain) |
| [`samples/array_mult16.v`](samples/array_mult16.v) | Generated | Braun array multiplier topology (textbook, public domain) |
| [`samples/generate_array_mult.py`](samples/generate_array_mult.py) | Original | Parameterized generator for N x N Braun multipliers |
| [`samples/c17.v`](samples/c17.v) | Re-typed from public-domain spec | ISCAS-85 benchmark (Brglez & Fujiwara, ISCAS 1985); topology is public-domain prior art |

The Braun array multiplier is a standard textbook structure first described
in: **E. L. Braun, "Digital Computer Design," Academic Press, 1963.**
The topology is public-domain prior art -- no patent or license restrictions.

### Confirmed NOT included

This repository explicitly does **not** ship:
- Proprietary RTL from any employer or commercial design.
- Synthesized netlists produced by commercial EDA tools.
- ISCAS / OpenCores / OpenROAD designs (these are listed in
 [`samples/README.md`](samples/README.md) only as suggestions for future
 additions, with permissive-license verification required).

---

## 2. Third-party Python libraries

All runtime dependencies are open source and pinned in
[`requirements.txt`](requirements.txt). Their licenses are compatible with
this project's MIT license.

| Library | Purpose | License | Project link |
|---------|---------|---------|--------------|
| [NetworkX](https://networkx.org/) | DiGraph data model + graph algorithms | BSD-3-Clause | <https://github.com/networkx/networkx> |
| [PyVis](https://pyvis.readthedocs.io/) | Interactive HTML graph visualization | BSD-3-Clause | <https://github.com/WestHealth/pyvis> |
| [Streamlit](https://streamlit.io/) | Browser-based UI framework | Apache-2.0 | <https://github.com/streamlit/streamlit> |
| [Plotly](https://plotly.com/python/) | 2D / 3D plotting | MIT | <https://github.com/plotly/plotly.py> |
| [Pandas](https://pandas.pydata.org/) | Tabular data handling in reports | BSD-3-Clause | <https://github.com/pandas-dev/pandas> |
| [NumPy](https://numpy.org/) | Numerical primitives (transitively required) | BSD-3-Clause | <https://github.com/numpy/numpy> |

PyVis itself bundles **vis.js** (Apache-2.0) for browser-side rendering;
the generated HTML files in [`outputs/`](outputs/) reference it via CDN.

---

## 3. Algorithmic & academic references

The graph algorithms in this project are textbook-standard. The references
below are the canonical sources we relied on while implementing each module.

### Core graph algorithms

- **Breadth-first search / cone extraction** -- E. F. Moore, *"The shortest
 path through a maze,"* Proc. Internat. Sympos. Switching Theory, 1959.
- **Topological sort + longest path on a DAG** --
 T. H. Cormen, C. E. Leiserson, R. L. Rivest, C. Stein, *Introduction to
 Algorithms (CLRS)*, 4th ed., MIT Press, Ch. 22.
- **Strongly-connected components for combinational-loop detection** --
 R. E. Tarjan, *"Depth-first search and linear graph algorithms,"* SIAM J.
 Comput., 1(2):146-160, 1972.
- **Sub-graph pattern matching for FSM / pipeline detection** -- heuristic;
 inspired by structural-pattern discussion in
 J. Bhasker, *Verilog HDL Synthesis: A Practical Primer*, Star Galaxy, 1998.

### EDA / netlist-analysis background

- **Static timing analysis fundamentals** -- J. Bhasker, R. Chadha,
 *Static Timing Analysis for Nanometer Designs*, Springer, 2009.
- **Logic-cone analysis & ATPG context** -- M. L. Bushnell, V. D. Agrawal,
 *Essentials of Electronic Testing for Digital, Memory and Mixed-Signal
 VLSI Circuits*, Springer, 2000.
- **Hardware security anti-patterns (reset trees, clock-gating)** --
 S. Bhunia, M. Tehranipoor, *Hardware Security: A Hands-On Learning
 Approach*, Morgan Kaufmann, 2018.

### Graph-learning-for-EDA inspiration (roadmap items)

The "AI-assistance hooks" and the GNN-experiment roadmap item are inspired
by, but do not re-implement:

- E. Ustun et al., *"Accurate Operation Delay Prediction for FPGA HLS
 Using Graph Neural Networks,"* ICCAD 2020.
- **NVIDIA Research -- GLOAM** (Graph Learning On A Manifold) and related
 graph-learning work on circuit timing / placement prediction.
 *Exact citation to be filled in -- see project author for the latest
 reference.*
- NVIDIA Research blog posts on graph learning for circuit timing
 prediction (publicly available, 2022-2024).
- Synopsys / Cadence published whitepapers on ML-assisted PD flows
 (publicly available marketing material; no proprietary content used).

---

## 4. Tooling & ecosystem

- **Python 3.10+** -- PSF License.
- **Git** -- GPL-2.0.
- **GitHub** for hosting (Microsoft / GitHub Terms of Service).
- **Mermaid** (used for the architecture diagram in [README.md](README.md))
 -- MIT License, rendered natively by GitHub.

---

## 5. How to cite this project

If you use any part of this repository in academic work, please cite:

```
Mallikarjuna A L, "Synthesis_project: AI-Assisted Hardware Design Analysis,"
GitHub repository, https://github.com/MaxTern-cyber/Synthesis_project, 2026.
```

BibTeX:

```bibtex
@misc{synthesis_project_2026,
 author = {Mallikarjuna A L},
 title = {Synthesis\_project: AI-Assisted Hardware Design Analysis},
 year = {2026},
 howpublished = {\url{https://github.com/MaxTern-cyber/Synthesis_project}}
}
```

---

## 6. Reporting an attribution issue

If you believe any file in this repository derives from a source not listed
above, please open a GitHub issue or contact the author directly
(see [README.md](README.md#author)). Corrections will be acted on promptly.
