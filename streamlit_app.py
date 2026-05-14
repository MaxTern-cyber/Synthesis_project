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
# Visualization
# ----------------------------------------------------------------------------
st.subheader("4. Interactive DAG")

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
