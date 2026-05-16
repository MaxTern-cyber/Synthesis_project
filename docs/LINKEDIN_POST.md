# LinkedIn post -- v0.1.0 announcement

> Copy-paste-ready. Pick Variant A or B, attach 1-2 screenshots or the
> social-preview banner, post. Then save to **Featured** section.

---

## Variant A -- "What I shipped" hook (recommended)

> **Problem:** post-synthesis Verilog netlists carry timing, parallelism, and security signal -- but in commercial flows that signal is fragmented across half a dozen reports and proprietary tools. I wanted to see how much of it you can recover from a single graph model, in Python, running entirely offline.
>
> **Synthesis_project (v0.1.0)** treats the netlist as a `networkx.DiGraph` and layers four analyses on the same data structure:
>
> ▸ **Static Timing Analysis (STA-lite)** -- forward/backward DP for arrival, required, slack. Kind-keyed delay model, configurable clock.
> ▸ **Parallelism profile (GL0AM-inspired)** -- DAG levelization + Brent's bound. Answers "is this design worth GPU-accelerating?" Reference: NVIDIA Research's GL0AM (Zhang & Ren, DAC 2023).
> ▸ **Hardware-security audit** -- 5-rule heuristic pass: combinational loops (Tarjan SCC), reset gating, async-reset without synchronizer, dangling logic (trojan-candidate cones), multi-driver nets.
> ▸ **Interactive DAG visualization** -- PyVis + Streamlit, in-browser.
>
> **Measured on ISCAS-85 benchmarks (single-thread, commodity laptop):**
> ▸ `c432` -- 378 nodes, 9.2× theoretical parallel speedup, worst slack -1.21 ns
> ▸ `c1908` (16-bit single-error-corrector) -- 991 nodes, **14.4× speedup**
> ▸ `c6288` (16×16 Braun multiplier) -- **4,738 nodes / 7,043 edges, 19.3× theoretical speedup, 256 gates evaluable in one parallel step** -- comfortably in the regime where GPU-accelerated logic simulation pays off.
>
> Local-first. No API keys. No cloud. Designs are IP -- anything that ships RTL to a third-party endpoint is a non-starter inside chip companies.
>
> **In v0.1.0:** 58 unit tests · CI on Python 3.10 / 3.11 / 3.12 · mypy-clean · PEP-621 packaging · 11 sample designs (incl. 4 ISCAS-85 benchmarks).
>
> Stack: Python · NetworkX · PyVis · Plotly · Streamlit · pytest · mypy · GitHub Actions
>
> **Live demo (no install):** https://synthesisproject-5ax4oq8wquyjmdgp6z9rvy.streamlit.app/
> **Repo + release notes:** https://github.com/MaxTern-cyber/Synthesis_project/releases/tag/v0.1.0
>
> Research prototype, not production EDA. Next on the roadmap: a local Ollama-backed LLM agent that summarizes fanout cones in plain English, and a GNN experiment to predict critical-path location from structural features.
>
> If you work in EDA, formal verification, hardware security, GPU simulation, or AI-for-chip-design -- I'd genuinely value your feedback.
>
> #VLSI #EDA #Verilog #RTL #StaticTimingAnalysis #HardwareSecurity #GPUComputing #AIforChipDesign #OpenSource #GraphAlgorithms #NetworkX

---

## Variant B -- Builder hook

> Spent a few weeks asking a simple question:
>
> **How much of a commercial netlist analyzer can you reproduce with NetworkX, PyVis, and Streamlit -- running 100% locally, in a browser?**
>
> [paste screenshot: parallelism profile + security audit side-by-side]
>
> The answer, in v0.1.0:
> ▸ Parser (Verilog primitives + named instances + behavioral RTL) → `networkx.DiGraph`
> ▸ STA-lite (arrival / required / slack DP -- linear time)
> ▸ Parallelism profile (DAG levelization + Brent's bound -- GL0AM-inspired)
> ▸ Hardware-security audit (5-rule heuristic over the DAG)
> ▸ Interactive PyVis visualization
> ▸ Live Streamlit demo
>
> All algorithms are textbook. The point isn't novelty -- it's how much you get for free once your data model is a graph.
>
> Algorithms in one line each:
> fanout cone = forward BFS · longest combinational path = topological sort + DP · combinational loops = Tarjan SCC · clock-domain propagation = attribute-tagging DFS · parallelism = level = 1 + max(level of predecessors).
>
> Headline benchmark: on **ISCAS-85 c6288** (16×16 Braun multiplier, 4,738 nodes / 7,043 edges), the parallelism profile reports **19.3× theoretical speedup with 256 gates evaluable in one parallel step** -- exactly the size class where GPU-accelerated logic simulation (cf. NVIDIA GL0AM) starts paying off.
>
> v0.1.0 tagged: 58 tests, CI on 3 Python versions, mypy clean, live Streamlit demo, full release notes.
>
> https://github.com/MaxTern-cyber/Synthesis_project/releases/tag/v0.1.0
> https://synthesisproject-5ax4oq8wquyjmdgp6z9rvy.streamlit.app/
>
> Open to feedback from anyone in EDA, formal verification, or AI-for-chip-design.
>
> #EDA #Verilog #RTL #HardwareDesign #AIforEDA #OpenSource #GraphAlgorithms

---

## Suggested first comment (boosts engagement)

> A few questions I'd love feedback on:
> 1. Which of the four modules looks most useful in your day-to-day flow -- STA-lite, parallelism profile, hardware-security audit, or interactive DAG?
> 2. Anyone using local LLMs (Ollama / Llama-3 / Phi-3) inside an EDA loop today? That's the next module I want to ship (issue #3 on the repo).
> 3. Open-source designs you'd want me to test the analyzer on next? ISCAS-85 c17, c432, c1908, c6288 are already in the benchmark table -- ISCAS-89 sequentials and OpenCores IP are next.

## Posting checklist

- [ ] Attach the social-preview banner (`docs/images/social-preview.png`) or a 30-second screen recording of the live demo
- [ ] Add 1-2 screenshots: parallelism profile + security audit
- [ ] Tag 3-5 connections who work in EDA / VLSI / GPU computing
- [ ] Save to **Featured** section of your profile
- [ ] Repost a shorter version to X/Twitter the next day
- [ ] Pin the link to your GitHub profile README (already done)
