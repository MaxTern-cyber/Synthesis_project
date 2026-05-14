# Building a Local-First EDA Suite: How Far Can You Get with NetworkX?

> *A research-prototype writeup of [Synthesis_project](https://github.com/MaxTern-cyber/Synthesis_project) v0.1.0 -- an open-source, AI-assisted hardware-design analysis suite.*

## TL;DR

Modern netlist analysis -- fanout cones, critical paths, combinational-loop detection, clock-domain crossings, FSM discovery, static timing analysis, parallelism analysis, hardware-security auditing -- is, underneath the TCL and licensing, a small set of classical graph algorithms.

I built a working prototype that exposes all of these in a browser, runs 100% locally, and leaves a clean hook for an LLM-driven AI-assistance layer.

This post walks through the **representation choice**, the **algorithms** (now eight of them, end-to-end), the **measured benchmarks** on the bundled samples (including ISCAS-85), and **where AI fits in next** -- without pretending the result is production EDA.

---

## 1. The Right Representation: One Graph to Rule Them All

The single most important design decision was making `networkx.DiGraph` the **only** in-memory representation of the design.

```
parsing -> DiGraph -> algorithms -> visualization
 |
 +-> AI-assistance layer
```

Nodes are gates / registers / IO pins; edges are net connections; attributes carry cell type (`kind=and`, `kind=reg`, `kind=input`, ...), fanout, clock domain. Every subsequent question -- "what does this signal drive?", "what's the longest combinational path?", "is there a clock-domain crossing here?", "is this design worth GPU-accelerating?", "is the reset path gated with functional logic?" -- becomes a query on the same graph.

This is also how modern EDA research is increasingly framed: GNN-based timing prediction, graph-learning for circuit optimization (NVIDIA, Synopsys, MIT have all published in this space recently). The graph isn't just a debugging aid; it's the right substrate for ML and the right substrate for parallel simulation.

---

## 2. Algorithms -- All Standard, All Linear

Every analysis in the suite reduces to a textbook graph algorithm. The point of the prototype isn't algorithmic novelty -- it's showing how much of an "analyzer" you get for free once your data model is right.

### 2a. Fanout cone -- reverse BFS

For a driver $d$, the fanout cone is the set of descendants. A depth-limited BFS keeps it interactive on 10k-gate designs:

```python
def fanout_cone(G, driver, depth=3):
    return nx.bfs_tree(G, driver, depth_limit=depth)
```

That's it. The visualization, depth slider, and report all consume this.

### 2b. Critical path -- longest path on a DAG

Once the sequential boundary is cut at registers, the combinational sub-graph is a DAG. Longest path on a DAG is **O(V + E)** via topological-sort + DP -- no exponential search:

```python
def longest_path(G):
    topo = list(nx.topological_sort(G))
    dist = {v: 0 for v in topo}
    parent = {}
    for u in topo:
        for v in G.successors(u):
            if dist[v] < dist[u] + 1:
                dist[v] = dist[u] + 1
                parent[v] = u
    end = max(dist, key=dist.get)
    path = [end]
    while path[-1] in parent:
        path.append(parent[path[-1]])
    return list(reversed(path))
```

With unit weights this is gate-count critical path. Swap in a per-cell delay table and it becomes STA -- which is exactly what the next module does.

### 2c. Static timing analysis -- STA-lite

[`tools/sta_lite/`](https://github.com/MaxTern-cyber/Synthesis_project/tree/main/tools/sta_lite) extends the longest-path idea with per-cell delays and full STA semantics:

- **Forward pass:** arrival time at a node = max(arrival of predecessors) + cell delay
- **Backward pass from primary outputs:** required time = min(required of successors) - cell delay
- **Slack = required - arrival** on every node; the worst-negative-slack endpoint is the headline metric

The delay table is keyed on node `kind` (NAND=0.10 ns, AND=0.12 ns, OR=0.14 ns, XOR=0.18 ns, register=0.05 ns, ...). Clock period is configurable -- in the live demo it's a slider, and you can watch slack flip from MET to VIOLATED as you tighten it.

This isn't a replacement for PrimeTime. It is a useful educational implementation that produces the right shape of output: arrival waveform, slack histogram, worst-slack path traceback.

### 2d. Parallelism profile -- DAG levelization & Brent's-bound speedup (GL0AM-inspired)

[`tools/parallelism/`](https://github.com/MaxTern-cyber/Synthesis_project/tree/main/tools/parallelism) answers a different question on the same DAG: **"if you ran this netlist on a parallel logic simulator, how much speedup could you possibly get?"**

The approach is inspired by [NVIDIA Research's GL0AM](https://github.com/NVlabs/GL0AM) (GPU-Accelerated Gate-Level Logic Simulator, Zhang & Ren, DAC 2023). GL0AM levelizes the netlist, schedules same-level gates onto GPU streaming multiprocessors in lock-step, and uses graph partitioning to minimize synchronization overhead. This module ports the *analysis* half of that idea to CPU Python:

1. **Levelize the combinational DAG** -- `level[v] = 1 + max(level[u] for u in preds)`. All gates at the same level have no data dependency, so they are simulable in one parallel step.
2. **Width-per-level histogram** -- wide-and-shallow shape means lots of parallelism; tall-and-narrow means serial-bound.
3. **Brent's bound** -- $\text{speedup}_{\max} = |V| / L_{\max}$. Upper bound on parallel speedup for *any* parallel simulator on this design -- GPU, multi-threaded CPU, or FPGA emulator.
4. **Partition count** -- weakly-connected components in the register-cut graph. Each partition is an independent combinational cone; more partitions means easier GPU load-balancing.
5. **Verdict** -- coarse "is this design worth GPU-accelerating?" tag (trivial / serial-bound / moderate / GL0AM-regime).

Measured: `c17` is trivial (2.4×), `c432` is moderate (9.2×, 36 gates per parallel step), and **`array_mult16` lands in the GL0AM regime at 14.0× with 260 gates per parallel step at its widest level** -- exactly the size class where GPU acceleration starts paying off.

This is a research-prototype module: it identifies where GPU acceleration would be valuable; it does not perform GPU simulation itself.

### 2e. Hardware-security audit -- 5 heuristic rules over the DAG

[`tools/security/`](https://github.com/MaxTern-cyber/Synthesis_project/tree/main/tools/security) is a static-analysis pass that surfaces five well-known hardware-security and design-integrity anti-patterns. All rules run in linear time over the same DAG:

| Rule | What it catches | Severity | Algorithm |
|---|---|---|---|
| `COMB_LOOP` | Non-trivial SCC in the combinational sub-graph -- a ring oscillator or latch loop | HIGH | Tarjan SCC |
| `RESET_GATING` | A `reset` / `rst` net reaches a register only *after* a combinational gate (data-dependent reset = fault-injection surface) | HIGH | Shortest-path reset→reg, count combinational hops |
| `ASYNC_RESET_NO_SYNC` | A reset input drives a register directly with no 2-FF synchronizer chain (metastability / glitch-attack surface) | MEDIUM | Downstream-register check on the target reg |
| `DANGLING_LOGIC` | Combinational nodes with no forward path to any primary output or register (classic trojan hiding place) | LOW or MEDIUM | Ancestor-set complement; cone-size threshold |
| `MULTI_DRIVER` | Net with > 1 driver (X-propagation / glitch / contention) | HIGH | In-degree check on net nodes |

Findings are sorted HIGH → LOW with a concrete `suggestion:` field on each one. The ruleset is heuristic -- false positives are expected; the value is in surfacing candidates for human review, not in formal proof. Reset detection uses a conservative name pattern (`reset | rst | reset_n | rstn`); for production use you would replace this with a proper port-attribute lookup.

### 2f. Combinational-loop detection -- Tarjan's SCC

A combinational loop is a strongly connected component of size > 1 in the combinational sub-graph. Tarjan's algorithm finds all SCCs in $O(|V|+|E|)$. Each non-trivial SCC is reported with severity based on cycle length and gate composition, plus a suggestion of where to insert a register to break it. This is reused by `RESET_GATING` and `MULTI_DRIVER` rules above.

### 2g. Clock-domain propagation -- DFS with attribute tagging

Clock signals are seed-detected by regex (`clk`, `clock`, `_ck`, ...). A DFS from each clock source propagates the domain attribute through combinational nodes, halting at registers and IOs. This yields the **CDC (clock-domain-crossing) candidate set** for free -- any combinational node visited by two different domains is a CDC candidate.

### 2h. I/O dependency chains -- topological forward traversal

For each primary input, a forward topological traversal yields all primary outputs influenced by it. The transitive-closure view exposes **dead inputs**, **dead outputs**, and **maximum logic depth per output** -- useful for both verification coverage and SoC-level timing budgeting.

---

## 3. Benchmarks -- Measured Numbers on Real Designs

End-to-end results on the bundled sample designs in v0.1.0 (single-thread, Python 3.12, no caching). Parse + DAG build + full STA-lite sweep + parallelism profile + security audit, on commodity laptop hardware:

| Sample | Source | Nodes | Edges | Critical path | Worst slack @ 1 ns | Parallel speedup | Security findings |
|---|---|---:|---:|---:|---:|---:|---:|
| `c17.v` | ISCAS-85 | 17 | 18 | 7 | +0.700 ns (MET) | 2.4× | 0 |
| `decoder2to4.v` | textbook | 15 | 20 | 5 | +0.830 ns (MET) | 3.0× | 0 |
| `mux4to1.v` | textbook | 20 | 25 | 7 | +0.680 ns (MET) | 2.9× | 0 |
| `adder4.v` | textbook | 34 | 37 | 9 | -0.200 ns (4-bit ripple-carry) | 3.8× | 0 |
| `pipeline3.v` | textbook | 12 | 20 | 1 | +1.000 ns (MET) | 3.0× | 0 |
| `fsm_traffic.v` | textbook | 9 | 10 | 1 | +1.000 ns (MET) | 1.0× | 0 |
| **`c432.v`** | **ISCAS-85** | **378** | **518** | **41** | **-1.210 ns at `N421`** | **9.2×** | 0 |
| `array_mult8.v` | generated | 326 | 489 | 43 | -5.120 ns at `s_7_7` | 7.6× | 0 |
| **`array_mult16.v`** | **generated** | **1278** | **1985** | **91** | **-12.320 ns at `s_15_15`** | **14.0× (GL0AM regime)** | 0 |

Worst-slack numbers use the illustrative delay model in `tools/sta_lite/sta.py`; they are not silicon-accurate but they are reproducible and they correctly track design complexity (a 16×16 multiplier critical path is **91 gates deep** vs. the adder's 9). The headline: as netlists scale, **available parallelism grows faster than the critical path** -- exactly the economic case for GPU-accelerated logic simulation.

**Total CI runtime: under 5 seconds for the full 52-test suite.**

---

## 4. Where AI Fits Next

Today, the AI hooks in the repo are scaffolds, not agents. But the data model already supports three high-value LLM applications:

### (a) Cone summarization

> *"Why is signal `q_out_b` high?"*

The local fanin sub-graph is small (depth-bounded). It fits in a prompt. A local LLM can produce a natural-language causal explanation grounded in actual gate types and connections. Tracked as **issue #3** on the repo -- Ollama + Llama-3.2-3B-instruct or Phi-3.5 is the realistic backend.

### (b) Hardware-security explanation layer

The 5-rule audit catches the patterns; an LLM can *explain* each finding to a developer who hasn't read the literature. "Reset gating" gets a fix suggestion today; an LLM can turn that into a 3-paragraph design-review note grounded in CWE / hardware-CWE references.

### (c) GNN criticality prediction

Tracked as **issue #4**. Train a small GraphSAGE / GAT on the bundled samples; predict per-node criticality (a proxy for "would STA flag this?") from structural features only -- no delay table. The training data is free: STA-lite gives you ground-truth slack on every node of every sample.

**The crucial constraint: all of this runs locally.** Designs are IP. Anything that ships RTL to a third-party endpoint is a non-starter inside chip companies.

---

## 5. What It Isn't

Honest limitations, as written in the README:

- Not a formal STA tool -- paths are gate-count weighted with an illustrative delay model unless you plug in a calibrated `.lib`.
- Not a full SystemVerilog parser -- targeted at post-synthesis structural Verilog plus a small subset of behavioral RTL.
- Not a DRC / LVS / placement tool.
- Not validated at multi-million-gate scale -- NetworkX would need to be swapped for a C++ graph backend (`igraph`, `graph-tool`, or a custom CSR representation).
- The hardware-security ruleset is heuristic, not formal -- it surfaces candidates for human review; it does not prove the absence of vulnerabilities.

These are limitations, not bugs. They define the slice the prototype goes after.

---

## 6. Roadmap

Shipped in v0.1.0 (covered above):
- Parser + DAG builder
- STA-lite
- Parallelism profile (GL0AM-inspired)
- Hardware-security audit
- DAG visualization
- Streamlit Cloud demo
- 9 sample designs (incl. ISCAS-85 c17, c432)
- 52 unit tests, CI on Python 3.10 / 3.11 / 3.12, mypy-clean, PEP-621 packaging

In progress / next:
- Local-LLM agent (Ollama + Llama-3.2 / Phi-3.5) over the DAG -- [issue #3](https://github.com/MaxTern-cyber/Synthesis_project/issues/3)
- GNN inference experiment for criticality prediction -- [issue #4](https://github.com/MaxTern-cyber/Synthesis_project/issues/4)
- Larger ISCAS-85 designs (`c1908`, `c6288`)
- GraphML / DEF export to interoperate with Yosys / OpenROAD

---

## 7. Closing Thought

Commercial EDA is excellent at what it does, and there's no realistic path to replacing it with a hobby project. But there's a large middle ground -- **interactive exploration, AI-assisted debug, security-pattern hunting, parallelism analysis, educational STA** -- where a graph-native open-source tool is faster, cheaper, and easier to extend than the incumbent flow.

That's the slice this prototype goes after, and v0.1.0 is the baseline.

If you work in EDA, formal verification, synthesis, hardware security, GPU-accelerated simulation, or AI-for-chip-design -- open an issue, drop a comment, or reach out. Feedback wanted.

> [github.com/MaxTern-cyber/Synthesis_project](https://github.com/MaxTern-cyber/Synthesis_project) · [Live demo](https://synthesisproject-5ax4oq8wquyjmdgp6z9rvy.streamlit.app/) · [v0.1.0 release notes](https://github.com/MaxTern-cyber/Synthesis_project/releases/tag/v0.1.0)

---

## Acknowledgements

- **Yanqing Zhang, Mark Haoxing Ren (NVIDIA Research)** -- *GL0AM: GPU-Accelerated Gate-Level Logic Simulator* (DAC 2023). The `tools/parallelism` module implements the analysis half of GL0AM's idea on CPU; it does not perform GPU simulation. Open source: [github.com/NVlabs/GL0AM](https://github.com/NVlabs/GL0AM).
- **Brglez & Fujiwara** -- ISCAS-85 combinational benchmark suite (ISCAS 1985). `c17` and `c432` are bundled with the repo.

---

*Tags: `eda` `verilog` `rtl` `synthesis` `static-timing-analysis` `formal-verification` `hardware-security` `gpu-computing` `ai-for-chip-design` `graph-algorithms` `networkx` `open-source`*
