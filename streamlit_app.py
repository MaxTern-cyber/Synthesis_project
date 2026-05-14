"""
streamlit_app.py
================
Entry point for Streamlit Cloud deployment of Synthesis_project.

What it does:
    1. Pick a built-in sample design OR upload a `.v` file.
    2. Parse it into a `networkx.DiGraph` via `launchers/generate_sample_outputs.build_graph`.
    3. Show stats: node count, edge count, primary I/O, gate breakdown.
    4. Render the DAG interactively via PyVis (embedded in the page).
    5. Surface a few graph-algorithm queries:
         - longest topological path  (proxy for critical path on unit weights)
         - cone-of-influence (forward / backward reachability from any node)
         - SCC detection (combinational loop check)

Run locally:
    streamlit run streamlit_app.py

Deploy:
    push to GitHub -> https://share.streamlit.io -> point to this file.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import networkx as nx
import streamlit as st
from pyvis.network import Network

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "launchers"))

import generate_sample_outputs as gso  # noqa: E402

SAMPLES_DIR = REPO_ROOT / "samples"

# ----------------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Synthesis_project - DAG Analyzer",
    page_icon="[*]",
    layout="wide",
)

st.title("Synthesis_project -- interactive DAG analyzer")
st.caption(
    "Verilog netlist -> NetworkX DiGraph -> graph algorithms + interactive "
    "PyVis visualization. Local-first, browser-only, no API keys. "
    "[GitHub](https://github.com/MaxTern-cyber/Synthesis_project)."
)

with st.sidebar:
    st.header("About")
    st.markdown(
        "This is the **live demo** of the analyzer module of "
        "[Synthesis_project](https://github.com/MaxTern-cyber/Synthesis_project) -- "
        "an open-source EDA prototype built around treating the post-synthesis "
        "netlist as a first-class graph object."
    )
    st.markdown("---")
    st.subheader("Algorithms exposed here")
    st.markdown(
        "- **Reverse BFS** for fanin-cone\n"
        "- **Forward BFS** for fanout-cone\n"
        "- **Topological-sort + DP** for longest-path on the combinational DAG\n"
        "- **Tarjan SCC** for combinational-loop detection\n"
        "- **STA-lite** -- arrival / required / slack DP with kind-keyed delays\n"
        "- **Parallelism profile** -- levelization + Brent's-bound speedup (GL0AM-inspired)\n"
        "- **Security audit** -- 5-rule heuristic ruleset (comb-loops, reset gating, async-reset sync, dangling logic, multi-driver)\n"
    )
    st.markdown("---")
    st.markdown(
        "**Full repo (7 tools, docs, samples):** "
        "[MaxTern-cyber/Synthesis_project]"
        "(https://github.com/MaxTern-cyber/Synthesis_project)"
    )


# ----------------------------------------------------------------------------
# Input source
# ----------------------------------------------------------------------------
st.subheader("1. Pick a design")

samples = sorted(p.name for p in SAMPLES_DIR.glob("*.v"))
default_idx = samples.index("array_mult8.v") if "array_mult8.v" in samples else 0

col_a, col_b = st.columns([2, 1])
with col_a:
    choice = st.selectbox(
        "Built-in sample design",
        options=["<upload your own .v>"] + samples,
        index=default_idx + 1,
    )
with col_b:
    uploaded = st.file_uploader("...or upload a Verilog file", type=["v", "sv"])

if uploaded is not None:
    src = uploaded.read().decode("utf-8", errors="replace")
    title = uploaded.name
elif choice != "<upload your own .v>":
    src = (SAMPLES_DIR / choice).read_text(encoding="utf-8")
    title = choice
else:
    st.info("Pick a sample from the dropdown or upload a `.v` file to start.")
    st.stop()

# ----------------------------------------------------------------------------
# Parse + build graph
# ----------------------------------------------------------------------------
with st.spinner(f"Parsing {title} and building the DAG..."):
    g, meta = gso.build_graph(src)


# ----------------------------------------------------------------------------
# Stats
# ----------------------------------------------------------------------------
st.subheader("2. Graph statistics")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Modules", len(meta["modules"]))
m2.metric("Gates", meta["gates"])
m3.metric("Registers", meta["regs"])
m4.metric("Sub-instances", meta["instances"])
m5.metric("Total nodes", g.number_of_nodes())

st.write(
    f"**Total edges:** `{g.number_of_edges()}`  |  "
    f"**Modules parsed:** `{', '.join(meta['modules'])}`"
)

# Kind breakdown
kinds: dict[str, int] = {}
for _, data in g.nodes(data=True):
    k = data.get("kind", "unknown")
    kinds[k] = kinds.get(k, 0) + 1
if kinds:
    st.write("**Node-kind breakdown:**  " + "  ".join(
        f"`{k}={v}`" for k, v in sorted(kinds.items(), key=lambda x: -x[1])
    ))


# ----------------------------------------------------------------------------
# Graph algorithm queries
# ----------------------------------------------------------------------------
st.subheader("3. Graph-algorithm queries")

q1, q2 = st.columns(2)

with q1:
    st.markdown("**Combinational loop check (Tarjan SCC)**")
    sccs = [c for c in nx.strongly_connected_components(g) if len(c) > 1]
    if sccs:
        st.error(f"Found {len(sccs)} combinational loop(s).")
        for i, c in enumerate(sccs[:3], start=1):
            st.code("\n".join(sorted(c)[:8]), language="text")
    else:
        st.success("No combinational loops detected.")

with q2:
    st.markdown("**Longest topological path (depth proxy)**")
    try:
        # only valid on a DAG
        if nx.is_directed_acyclic_graph(g):
            path = nx.dag_longest_path(g)
            st.write(f"Length: `{len(path)}` nodes.")
            with st.expander("Show path"):
                st.code(" -> ".join(path), language="text")
        else:
            st.warning("Graph has cycles -- longest-path skipped.")
    except Exception as e:
        st.warning(f"Could not compute longest path: {e}")


# Cone-of-influence picker
st.markdown("**Cone-of-influence (BFS)**")
all_nodes = sorted(g.nodes())
node_pick = st.selectbox("Select a node:", options=all_nodes, index=0)
direction = st.radio("Direction:", ["Fanin (predecessors)", "Fanout (successors)"], horizontal=True)
depth = st.slider("Depth limit:", min_value=1, max_value=10, value=3)

if direction.startswith("Fanin"):
    reachable = nx.single_source_shortest_path_length(g.reverse(), node_pick, cutoff=depth)
else:
    reachable = nx.single_source_shortest_path_length(g, node_pick, cutoff=depth)

st.write(
    f"Reachable within depth {depth}: **{len(reachable)} nodes** "
    f"(out of {g.number_of_nodes()})."
)


# ----------------------------------------------------------------------------
# STA-lite: educational static timing analysis
# ----------------------------------------------------------------------------
from tools.sta_lite import analyze, top_n_slowest_endpoints, DEFAULT_DELAYS  # noqa: E402

st.subheader("4. STA-lite (educational static timing analysis)")
st.caption(
    "Forward + backward DP over the DAG with kind-keyed unit delays "
    "(NAND=0.10ns, AND=0.12ns, OR=0.15ns, XOR=0.20ns, NOT=0.05ns, "
    "submodule=0.30ns, register=boundary). Numbers are illustrative."
)

if not nx.is_directed_acyclic_graph(g):
    st.warning("Graph has cycles outside register boundaries -- STA skipped.")
else:
    clock_ns = st.slider(
        "Target clock period (ns):",
        min_value=0.10, max_value=5.00, value=1.00, step=0.05,
    )
    rep = analyze(g, clock_period=clock_ns)

    sta_c1, sta_c2, sta_c3 = st.columns(3)
    sta_c1.metric("Worst slack", f"{rep.worst_slack:+.3f} ns",
                  delta="VIOLATED" if rep.worst_slack < 0 else "MET",
                  delta_color="inverse" if rep.worst_slack < 0 else "normal")
    sta_c2.metric("Critical-path length", f"{len(rep.critical_path)} nodes")
    sta_c3.metric("Worst endpoint", str(rep.worst_endpoint or "-").split("/")[-1])

    st.markdown("**Top-5 slowest endpoints (by arrival time)**")
    top = top_n_slowest_endpoints(g, rep.arrivals, n=5)
    if top:
        import pandas as pd
        df = pd.DataFrame(
            [(n, f"{a:.3f} ns", f"{rep.slacks.get(n, 0.0):+.3f} ns") for n, a in top],
            columns=["Endpoint", "Arrival", "Slack"],
        )
        st.dataframe(df, use_container_width=True, hide_index=True)

    with st.expander("Show critical path"):
        if rep.critical_path:
            st.code(" ->\n".join(rep.critical_path), language="text")
        else:
            st.write("(no critical path found)")


# ----------------------------------------------------------------------------
# Parallelism profile (GL0AM-inspired)
# ----------------------------------------------------------------------------
from tools.parallelism import profile as par_profile  # noqa: E402

st.subheader("5. Parallelism profile (GL0AM-inspired)")
st.caption(
    "Levelize the DAG, count gates per topological level, and compute the "
    "theoretical maximum parallel speedup (Brent's bound = |gates| / "
    "critical-path-length). This is the upper bound on speedup achievable "
    "by ANY parallel simulator -- GPU (e.g. NVIDIA GL0AM), multi-threaded "
    "CPU, or FPGA emulator -- on this netlist. Inspired by "
    "[GL0AM (Zhang & Ren, NVIDIA Research)]"
    "(https://github.com/NVlabs/GL0AM)."
)

par = par_profile(g)

p1, p2, p3, p4 = st.columns(4)
p1.metric("Theoretical speedup", f"{par.theoretical_speedup:.2f}x",
          help="|gates| / critical-path-length (Brent's bound)")
p2.metric("Max parallel width", f"{par.max_width}",
          help="Largest number of gates evaluable in one parallel step")
p3.metric("Critical-path depth", f"{par.critical_path_length}")
p4.metric("Combinational cones", f"{par.partitions}",
          help="Register-bounded independent simulation units")

# Verdict banner
if "excellent" in par.verdict.lower():
    st.success(f"**Verdict:** {par.verdict}")
elif "moderate" in par.verdict.lower():
    st.info(f"**Verdict:** {par.verdict}")
else:
    st.warning(f"**Verdict:** {par.verdict}")

# Width-per-level chart
if par.width_per_level:
    import pandas as pd  # noqa: E402
    df_widths = pd.DataFrame(
        {
            "Level (topological depth)": list(par.width_per_level.keys()),
            "Gates at this level": list(par.width_per_level.values()),
        }
    )
    st.markdown("**Gates simulable in parallel at each level**")
    st.bar_chart(df_widths, x="Level (topological depth)", y="Gates at this level")
    st.caption(
        f"Wide & shallow shape => lots of parallelism. Tall & narrow => "
        f"serial-bound. This design: avg={par.avg_width:.1f} gates/level, "
        f"max={par.max_width}, levels={par.critical_path_length}."
    )


# ----------------------------------------------------------------------------
# Hardware-security audit
# ----------------------------------------------------------------------------
from tools.security import Severity, audit as sec_audit  # noqa: E402

st.subheader("6. Hardware-security audit")
st.caption(
    "Five heuristic rules over the DAG: combinational loops, reset gating, "
    "async-reset-without-synchronizer, dangling logic (potential trojan), "
    "and multi-driver nets. Static analysis only -- false positives expected; "
    "surfaces candidates for human review."
)

sec_report = sec_audit(g)
sec_counts = sec_report.by_severity

s1, s2, s3, s4 = st.columns(4)
s1.metric("Total findings", sec_report.total)
s2.metric("HIGH", sec_counts[Severity.HIGH])
s3.metric("MEDIUM", sec_counts[Severity.MEDIUM])
s4.metric("LOW", sec_counts[Severity.LOW])

if sec_report.total == 0:
    st.success("Clean: no rule violations detected.")
elif sec_counts[Severity.HIGH] > 0:
    st.error(f"{sec_counts[Severity.HIGH]} HIGH-severity finding(s) -- review recommended.")
else:
    st.warning(f"{sec_report.total} finding(s) -- review recommended.")

if sec_report.findings:
    import pandas as _pd  # noqa: E402
    df_sec = _pd.DataFrame(
        [
            {
                "Severity": str(f.severity),
                "Rule": f.rule_id,
                "Locus": f.locus,
                "Description": f.description,
                "Suggested fix": f.suggestion,
            }
            for f in sec_report.findings
        ]
    )
    st.dataframe(df_sec, use_container_width=True, hide_index=True)


# ----------------------------------------------------------------------------
# Visualization
# ----------------------------------------------------------------------------
st.subheader("7. Interactive DAG")

max_nodes = st.slider(
    "Cap nodes shown (large graphs render slowly in the browser):",
    min_value=50, max_value=max(50, g.number_of_nodes()),
    value=min(500, g.number_of_nodes()),
    step=50,
)

if g.number_of_nodes() > max_nodes:
    # Keep the highest-degree nodes (most "interesting") plus their neighbours
    top = sorted(g.degree, key=lambda x: -x[1])[:max_nodes // 2]
    keep = set(n for n, _ in top)
    for n, _ in top:
        keep.update(list(g.successors(n))[:3])
        keep.update(list(g.predecessors(n))[:3])
    g_view = g.subgraph(list(keep)[:max_nodes]).copy()
    st.info(f"Rendering a {g_view.number_of_nodes()}-node sample (high-degree neighbourhood).")
else:
    g_view = g

net = Network(
    height="650px", width="100%", directed=True,
    notebook=False, cdn_resources="remote",
    bgcolor="#ffffff", font_color="#222222",
)
net.barnes_hut(gravity=-6000, central_gravity=0.3, spring_length=110,
               spring_strength=0.002, damping=0.09)

for n, data in g_view.nodes(data=True):
    kind = data.get("kind", "net")
    color = gso.COLOR.get(kind, "#cccccc")
    shape = "diamond" if kind == "reg" else ("box" if kind == "inst" else "dot")
    net.add_node(n, label=n.split("/")[-1], color=color, shape=shape, title=f"{n}\nkind={kind}")
for s, t in g_view.edges():
    net.add_edge(s, t)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as tf:
    net.write_html(tf.name, notebook=False, open_browser=False)
    html = Path(tf.name).read_text(encoding="utf-8")

st.components.v1.html(html, height=680, scrolling=True)

st.caption(
    "Pre-generated HTML versions of every sample live in the "
    "[`outputs/`](https://github.com/MaxTern-cyber/Synthesis_project/tree/main/outputs) "
    "folder of the repo. Right-click a node in the canvas above to drag, scroll to zoom."
)
