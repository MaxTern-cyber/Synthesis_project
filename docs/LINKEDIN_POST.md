# LinkedIn post -- v0.1.0 announcement

> Copy-paste-ready. Pick Variant A or B, attach 1-2 screenshots or the
> social-preview banner, post. Then save to **Featured** section.

---

## Variant A -- "What I shipped" hook (recommended)

> I just tagged **v0.1.0** of an open-source EDA prototype I've been building -- and the result is a tool that asks: how much of a commercial netlist analyzer can you reproduce with Python + NetworkX, running 100% locally, in a browser?
>
> Quite a lot, it turns out.
>
> **Synthesis_project** treats the post-synthesis Verilog netlist as a first-class graph object and layers four analysis modules on the same DAG:
>
> ▸ **Static Timing Analysis (STA-lite)** -- forward/backward DP for arrival, required, and slack times. Kind-keyed delay model. Configurable clock period.
> ▸ **Parallelism profile (GL0AM-inspired)** -- DAG levelization + Brent's-bound theoretical-speedup analysis. Answers "is this design worth GPU-accelerating?" Inspired by NVIDIA Research's GL0AM (Zhang & Ren, DAC 2023).
> ▸ **Hardware-security audit** -- 5-rule heuristic ruleset (combinational loops, reset gating, async-reset-without-synchronizer, dangling logic / trojan candidates, multi-driver nets).
> ▸ **Interactive DAG visualization** -- PyVis + Plotly in a Streamlit UI.
>
> **Headline numbers on the bundled samples:**
> ▸ `c17` (ISCAS-85, 17 nodes): 2.4× theoretical parallel speedup
> ▸ `c432` (ISCAS-85, 378 nodes): 9.2× -- worst slack -1.21 ns at N421
> ▸ `array_mult16` (1278-node 16×16 multiplier): **14.0× -- GL0AM regime**, with 260 gates evaluable in one parallel step
>
> Local-first. No API keys. No cloud. Designs are IP -- anything that ships RTL to a third-party endpoint is a non-starter inside chip companies.
>
> **What's in the v0.1.0 ship:**
> 52 unit tests · CI on Python 3.10 / 3.11 / 3.12 · mypy-clean · PEP-621 packaging · 9 sample designs (incl. 2 ISCAS-85 benchmarks).
>
> **Live demo (no install):** https://synthesisproject-5ax4oq8wquyjmdgp6z9rvy.streamlit.app/
> **Repo + release notes:** https://github.com/MaxTern-cyber/Synthesis_project/releases/tag/v0.1.0
>
> Stack: Python · NetworkX · PyVis · Plotly · Streamlit · pytest · mypy · GitHub Actions
>
> Research prototype, not production EDA. Next: Ollama-backed local LLM agent over the DAG, and a GNN experiment to predict critical-path location from structural features.
>
> If you work in EDA, formal verification, hardware security, GPU simulation, or AI-for-chip-design -- I'd love your feedback.
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
> Headline benchmark: on a 1278-node 16×16 array multiplier, the parallelism profile reports **14.0× theoretical speedup** -- exactly the size class where GPU-accelerated logic simulation (cf. NVIDIA GL0AM) starts paying off.
>
> v0.1.0 tagged: 52 tests, CI on 3 Python versions, mypy clean, live Streamlit demo, full release notes.
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
> 3. Open-source designs you'd want me to test the analyzer on? c1908 and c6288 from ISCAS-85 are already on the roadmap.

## Posting checklist

- [ ] Attach the social-preview banner (`docs/images/social-preview.png`) or a 30-second screen recording of the live demo
- [ ] Add 1-2 screenshots: parallelism profile + security audit
- [ ] Tag 3-5 connections who work in EDA / VLSI / GPU computing
- [ ] Save to **Featured** section of your profile
- [ ] Repost a shorter version to X/Twitter the next day
- [ ] Pin the link to your GitHub profile README (already done)
