# Building a Local-First EDA Suite: How Far Can You Get with NetworkX?

> *A research-prototype writeup of [Synthesis_project](https://github.com/MaxTern-cyber/Synthesis_project) -- an open-source AI-assisted hardware-design analysis suite.*

## TL;DR

Modern netlist analysis -- fanout cones, critical paths, combinational-loop detection, clock-domain crossings, FSM discovery -- is, underneath the TCL and licensing, a small set of classical graph algorithms. I built a working prototype that exposes all of these in a browser, runs 100% locally, and leaves a clean hook for an LLM-driven AI-assistance layer.

This post walks through the **representation choice**, the **algorithms**, and **where AI fits in** -- without pretending the result is production EDA.

---

## 1. The Right Representation: One Graph to Rule Them All

The single most important design decision was making `networkx.DiGraph` the **only** in-memory representation of the design.

```
parsing -> DiGraph -> algorithms -> visualization
 |
 +-> AI-assistance layer
```

Nodes are gates / registers / IO pins; edges are net connections; attributes carry cell type, fanout, clock domain. Every subsequent question -- "what does this signal drive?", "what's the longest combinational path?", "is there a clock-domain crossing here?" -- becomes a query on the same graph.

This is also how modern EDA research is increasingly framed: GNN-based timing prediction, graph-learning for circuit optimization (NVIDIA, Synopsys, MIT have all published in this space recently). The graph isn't just a debugging aid; it's the right substrate for ML.

---

## 2. Algorithms -- All Standard, All Linear

Every analysis in the suite reduces to a textbook graph algorithm. The point of the prototype isn't algorithmic novelty -- it's showing how much of an "analyzer" you get for free once your data model is right.

### Fanout cone -- reverse BFS

For a driver $d$, the fanout cone is the set of descendants. A depth-limited BFS keeps it interactive on 10k-gate designs:

```python
def fanout_cone(G, driver, depth=3):
 return nx.bfs_tree(G, driver, depth_limit=depth)
```

That's it. The visualization, depth slider, and report all consume this.

### Critical path -- longest path on a DAG

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

With unit weights this is gate-count critical path. Swap in a per-cell delay table and it becomes STA-lite.

### Combinational loops -- Tarjan SCC

A combinational loop is a non-trivial strongly connected component in the combinational sub-graph. Tarjan finds all SCCs in **O(V + E)**:

```python
loops = [scc for scc in nx.strongly_connected_components(G_comb) if len(scc) > 1]
```

The interesting work is in the **reporting** -- severity classification, suggesting where to insert a register to break the cycle -- not the detection.

### Clock-domain propagation -- DFS with attribute tagging

Clock seeds are detected by regex (`clk`, `clock`, `_ck`, ...). A DFS from each seed propagates the domain attribute through combinational nodes, stopping at registers/IOs. Any combinational node visited by **two distinct domains** is a CDC candidate -- falls out of the algorithm for free.

### FSM / pipeline detection -- sub-graph pattern matching

The sub-graph induced by registers + their immediate combinational predecessors is matched against canonical structures:

- Small SCC of registers -> FSM.
- Long register chain -> pipeline.
- Tree of registers fanning from a counter -> datapath.

Heuristic, not formal -- but it's fast and surfaces structural intent for a reviewer.

### I/O dependency chains -- topological forward traversal

For each primary input, a forward topological traversal yields all primary outputs influenced by it. The transitive-closure view exposes **dead inputs**, **dead outputs**, and **max logic depth per output** -- useful for both verification coverage and SoC-level timing budgeting.

---

## 3. Where AI Fits

Today, the AI hooks in [`tools/demo2/ai_agent.py`](../tools/demo2/ai_agent.py) and [`tools/demo4/ai_agent.py`](../tools/demo4/ai_agent.py) are scaffolds, not agents. But the data model already supports three high-value LLM applications:

### (a) Cone summarization
> *"Why is signal `q_out_b` high?"*
The local fanin sub-graph is small (depth-bounded). It fits in a prompt. A local LLM can produce a natural-language causal explanation grounded in actual gate types and connections.

### (b) Hardware-security anti-pattern detection
Codified patterns like *"reset signal AND-gated with anything other than power-on detection"* or *"scan chain shares nets with functional logic"* become **graph-rewrite queries**. An LLM agent can flag, explain, and propose mitigations.

### (c) Buffer-insertion / drive-strength suggestions
Given fanout count + cell-type estimated drive strength, an LLM with access to the cone can suggest concrete instance names where buffering would help.

The crucial constraint: **all of this runs locally**. Designs are IP. Anything that ships RTL to a third-party endpoint is a non-starter inside chip companies. Ollama-backed Llama-3.2-3B-instruct or Phi-3 are the realistic backends.

---

## 4. What It Isn't

- Not a formal STA tool -- paths are gate-count weighted unless a delay table is plugged in.
- Not a full SystemVerilog parser -- targeted at post-synthesis structural Verilog.
- Not a DRC / LVS / placement tool.
- Not validated at multi-million-gate scale -- NetworkX would need to be swapped for a C++ graph backend (`igraph`, `graph-tool`, or a custom CSR representation).

These are honest limitations and they're listed in the README.

---

## 5. What's Next

Roadmap:
- Delay-aware STA-lite (per-cell delay tables, arrival/required-time propagation).
- Local-LLM agent (Ollama + Llama-3.2-3B-instruct).
- Codified hardware-security ruleset.
- GraphML / DEF export to interoperate with Yosys / OpenROAD.
- GNN experiment -- predict critical-path location from structural features only.
- CI + pytest suite.
- Streamlit Cloud public demo.

---

## 6. Closing Thought

Commercial EDA is excellent at what it does, and there's no realistic path to replacing it with a hobby project. But there's a large middle ground -- **interactive exploration, AI-assisted debug, security pattern hunting** -- where a graph-native open-source tool is faster, cheaper, and easier to extend than the incumbent flow.

That's the slice this prototype goes after.

If you work in EDA, formal verification, synthesis, hardware security, or AI-for-chip-design -- open an issue, drop a comment, or reach out. Feedback wanted.

 [github.com/MaxTern-cyber/Synthesis_project](https://github.com/MaxTern-cyber/Synthesis_project)

---

*Tags: `eda` `verilog` `rtl` `synthesis` `formal-verification` `hardware-security` `ai-for-chip-design` `graph-algorithms` `networkx` `open-source`*
