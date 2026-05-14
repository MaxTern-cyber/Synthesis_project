"""
generate_sample_outputs.py
==========================
Generate interactive PyVis HTML visualizations for every Verilog file under
samples/. Outputs go to outputs/<basename>.html.

Handles both styles used by the sample designs:
  1. Structural primitive gates:      and (y, a, b);
                                      xor (sum, a, b, cin);
  2. Named module instantiation:      full_adder fa0 (.a(a[0]), ...);
  3. Behavioral RTL (registers):      always @(posedge clk) ... <= ...;

This is intentionally simple and dependency-free apart from networkx + pyvis,
both already in requirements.txt.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

import networkx as nx
from pyvis.network import Network


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLES_DIR = REPO_ROOT / "samples"
OUTPUTS_DIR = REPO_ROOT / "outputs"

PRIMITIVES = {"and", "or", "nand", "nor", "xor", "xnor", "not", "buf"}
COLOR = {
    "and": "#45B7D1", "nand": "#FF6B6B",
    "or": "#F7DC6F",  "nor": "#FFA07A",
    "xor": "#BB8FCE", "xnor": "#BB8FCE",
    "not": "#98D8C8", "buf": "#98D8C8",
    "reg": "#4ECDC4",
    "input": "#A8E6CF", "output": "#A8E6CF",
    "inst": "#F8B88B",
}


def strip_comments(src: str) -> str:
    src = re.sub(r"//.*?\n", "\n", src)
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    return src


def parse_ports(module_body: str) -> tuple[list[str], list[str]]:
    inputs, outputs = [], []
    for m in re.finditer(r"\binput\b\s*(?:wire\s*)?(?:\[[^\]]+\]\s*)?([\w\s,]+);", module_body):
        inputs += [s.strip() for s in m.group(1).split(",") if s.strip()]
    for m in re.finditer(r"\boutput\b\s*(?:reg\s*|wire\s*)?(?:\[[^\]]+\]\s*)?([\w\s,]+);", module_body):
        outputs += [s.strip() for s in m.group(1).split(",") if s.strip()]
    # Also accept ANSI-style port lists in header
    return inputs, outputs


def parse_primitive_gates(module_body: str) -> list[tuple[str, list[str]]]:
    """Return list of (prim_type, [out, in1, in2, ...]) for primitive gate calls."""
    out = []
    # Pattern: prim (sig, sig, sig);  or prim name (sig, sig);
    pat = re.compile(
        r"\b(" + "|".join(PRIMITIVES) + r")\b\s+(?:\w+\s+)?\(\s*([^;]+?)\s*\)\s*;",
        re.IGNORECASE,
    )
    for m in pat.finditer(module_body):
        prim = m.group(1).lower()
        args = [a.strip() for a in m.group(2).split(",")]
        if len(args) >= 2:
            out.append((prim, args))
    return out


def parse_module_instances(module_body: str, known_modules: set[str]) -> list[tuple[str, str, dict]]:
    """Return list of (module_type, instance_name, {port: net}) for sub-module instances."""
    out = []
    pat = re.compile(r"\b(\w+)\s+(\w+)\s*\(([^;]*?)\)\s*;", re.DOTALL)
    for m in pat.finditer(module_body):
        mtype, inst, body = m.group(1), m.group(2), m.group(3)
        if mtype.lower() in PRIMITIVES:
            continue
        if mtype.lower() in {"module", "input", "output", "wire", "reg", "assign",
                              "always", "if", "else", "case", "endcase", "begin",
                              "end", "initial", "localparam", "parameter", "default"}:
            continue
        if mtype not in known_modules:
            continue
        ports = {}
        for pm in re.finditer(r"\.(\w+)\s*\(([^)]*)\)", body):
            ports[pm.group(1)] = pm.group(2).strip()
        out.append((mtype, inst, ports))
    return out


def parse_registers(module_body: str) -> list[tuple[str, list[str]]]:
    """Return list of (reg_signal, [driver_signals]) for posedge always blocks."""
    out: list[tuple[str, list[str]]] = []
    for blk in re.finditer(r"always\s*@\s*\(\s*posedge[^)]*\)(.*?)(?=always\s*@|endmodule)",
                            module_body, re.DOTALL | re.IGNORECASE):
        body = blk.group(1)
        # Identifiers referenced anywhere in the block become drivers (rough heuristic)
        idents = set(re.findall(r"\b([A-Za-z_]\w*)\b", body))
        # Drop Verilog keywords / numeric literal artifacts
        idents -= {"if", "else", "begin", "end", "case", "endcase", "default",
                    "negedge", "posedge", "or", "and", "not"}
        for m in re.finditer(r"\b(\w+)\s*<=", body):
            sig = m.group(1)
            drivers = sorted(i for i in idents if i != sig)
            out.append((sig, drivers))
    return out


def parse_comb_always(module_body: str) -> list[tuple[str, list[str]]]:
    """Return list of (signal, [drivers]) for blocking-assigns in always @(*) blocks."""
    out: list[tuple[str, list[str]]] = []
    for blk in re.finditer(r"always\s*@\s*\(\s*\*\s*\)(.*?)(?=always\s*@|endmodule)",
                            module_body, re.DOTALL | re.IGNORECASE):
        body = blk.group(1)
        idents = set(re.findall(r"\b([A-Za-z_]\w*)\b", body))
        idents -= {"if", "else", "begin", "end", "case", "endcase", "default"}
        for m in re.finditer(r"\b(\w+)\s*=(?!=)", body):
            sig = m.group(1)
            drivers = sorted(i for i in idents if i != sig)
            out.append((sig, drivers))
    return out


def build_graph(src: str) -> tuple[nx.DiGraph, dict]:
    src = strip_comments(src)

    modules = {}
    for m in re.finditer(r"module\s+(\w+)\s*(?:\([^)]*\))?\s*;(.*?)endmodule",
                         src, re.DOTALL):
        modules[m.group(1)] = m.group(2)

    g = nx.DiGraph()
    stats: dict[str, Any] = {"modules": list(modules), "gates": 0, "regs": 0, "instances": 0}

    for mname, body in modules.items():
        inputs, outputs = parse_ports(body)
        for n in inputs:
            g.add_node(f"{mname}/{n}", kind="input")
        for n in outputs:
            g.add_node(f"{mname}/{n}", kind="output")

        # Primitive gates
        for i, (prim, args) in enumerate(parse_primitive_gates(body)):
            gate_id = f"{mname}/{prim}_{i}"
            g.add_node(gate_id, kind=prim)
            # First arg = output, rest = inputs
            out_sig, ins = args[0], args[1:]
            g.add_edge(gate_id, f"{mname}/{out_sig}")
            for s in ins:
                g.add_edge(f"{mname}/{s}", gate_id)
            stats["gates"] += 1

        # Module instances
        for mtype, inst, ports in parse_module_instances(body, set(modules)):
            inst_id = f"{mname}/{inst}({mtype})"
            g.add_node(inst_id, kind="inst")
            for port, net in ports.items():
                if not net:
                    continue
                # Heuristic: short port names like Y, Q, OUT, SUM, COUT considered output
                if port.lower() in {"y", "q", "qn", "out", "sum", "cout", "co", "s"}:
                    g.add_edge(inst_id, f"{mname}/{net}")
                else:
                    g.add_edge(f"{mname}/{net}", inst_id)
            stats["instances"] += 1

        # Registers (from always @(posedge ...))
        for r, drivers in parse_registers(body):
            reg_id = f"{mname}/{r}_reg"
            g.add_node(reg_id, kind="reg")
            g.add_edge(reg_id, f"{mname}/{r}")
            for d in drivers:
                # Only connect to signals that look like real nets (already nodes or new)
                src = f"{mname}/{d}"
                if src != reg_id:
                    g.add_edge(src, reg_id)
            stats["regs"] += 1

        # Combinational always @(*) blocks
        for sig, drivers in parse_comb_always(body):
            target = f"{mname}/{sig}"
            g.add_node(target, kind=g.nodes.get(target, {}).get("kind", "net"))
            for d in drivers:
                src = f"{mname}/{d}"
                if src != target:
                    g.add_edge(src, target)

    return g, stats


def export_html(g: nx.DiGraph, out_path: Path, title: str) -> None:
    net = Network(height="800px", width="100%", directed=True, notebook=False,
                  cdn_resources="remote", bgcolor="#ffffff", font_color="#222222")
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=120,
                   spring_strength=0.002, damping=0.09)
    for n, d in g.nodes(data=True):
        kind = d.get("kind", "net")
        color = COLOR.get(kind, "#cccccc")
        shape = "box" if kind in {"input", "output"} else ("diamond" if kind == "reg" else "dot")
        label = n.split("/", 1)[-1]
        net.add_node(n, label=label, color=color, shape=shape, size=15,
                     title=f"{n}<br>kind: {kind}")
    for u, v in g.edges():
        net.add_edge(u, v, color="#888888", arrows="to")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = net.generate_html()
    html = html.replace("<head>", f"<head><title>{title}</title>")
    out_path.write_text(html, encoding="utf-8")


def main() -> int:
    OUTPUTS_DIR.mkdir(exist_ok=True)
    sample_files = sorted(SAMPLES_DIR.glob("*.v"))
    if not sample_files:
        print(f"No samples found in {SAMPLES_DIR}", file=sys.stderr)
        return 1

    print(f"{'sample':25s} {'modules':>8s} {'gates':>6s} {'regs':>5s} {'inst':>5s} {'nodes':>6s} {'edges':>6s}")
    print("-" * 75)
    for v_path in sample_files:
        g, stats = build_graph(v_path.read_text(encoding="utf-8"))
        out_path = OUTPUTS_DIR / (v_path.stem + ".html")
        export_html(g, out_path, title=f"{v_path.stem} - DAG")
        print(f"{v_path.name:25s} {len(stats['modules']):8d} "
              f"{stats['gates']:6d} {stats['regs']:5d} {stats['instances']:5d} "
              f"{g.number_of_nodes():6d} {g.number_of_edges():6d}")
    print(f"\nOutputs written to: {OUTPUTS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
