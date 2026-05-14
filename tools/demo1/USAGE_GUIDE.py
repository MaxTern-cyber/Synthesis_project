"""
QUICK START GUIDE - Enhanced Verilog DAG Tool
==============================================

This script shows you how to use all the new features step by step.
"""

import os, sys
# Anchor to repo root (this file lives at <repo>/tools/demo1/)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import the tool
exec(open(r"import networkx as nx.py", encoding='utf-8').read().replace("if __name__", "if False"), globals())

print("="*70)
print("QUICK START GUIDE - Enhanced Verilog DAG Tool")
print("="*70)

# Step 1: Load your netlist
print("\n[STEP 1] Loading netlist...")
tool = VerilogDagTool("netlist.v")
tool.parse_and_build()
print(f"✓ Loaded: {tool.dag.number_of_nodes()} gates, {tool.dag.number_of_edges()} connections")

# ============================================================================
# FEATURE 1: Verify a specific gate
# ============================================================================
print("\n" + "="*70)
print("FEATURE 1: VERIFY GATE CONNECTIVITY")
print("="*70)
print("Use this to see what connects to a specific gate")
print("\nExample: tool.verify_gate('g2705')")
print("-"*70)
tool.verify_gate("g2705")

# ============================================================================
# FEATURE 2: Backward Cone (What affects this gate?)
# ============================================================================
print("\n" + "="*70)
print("FEATURE 2: BACKWARD CONE - What affects this gate/signal?")
print("="*70)
print("Use this to find root causes - what gates could cause a bug here?")
print("\nExample: tool.backward_cone('g5536')")
print("-"*70)
cone = tool.backward_cone("g5536")
print(f"\n✓ Found {len(cone)} gates that can affect g5536")

# ============================================================================
# FEATURE 3: Forward Cone (What does this gate affect?)
# ============================================================================
print("\n" + "="*70)
print("FEATURE 3: FORWARD CONE - What does this gate affect?")
print("="*70)
print("Use this to see impact - if this gate is wrong, what else breaks?")
print("\nExample: tool.forward_cone('g2705')")
print("-"*70)
cone = tool.forward_cone("g2705")
print(f"\n✓ Gate g2705 affects {len(cone)} gates downstream")

# ============================================================================
# FEATURE 4: Export Cone as separate visualization
# ============================================================================
print("\n" + "="*70)
print("FEATURE 4: EXPORT CONE SUBGRAPH")
print("="*70)
print("Save a cone as a separate HTML file for easier viewing")
print("\nExample: tool.export_cone_subgraph(cone, 'cone_g2705.html')")
print("-"*70)
tool.export_cone_subgraph(cone, "cone_g2705.html")

# ============================================================================
# FEATURE 5: Detect Combinational Loops
# ============================================================================
print("\n" + "="*70)
print("FEATURE 5: DETECT COMBINATIONAL LOOPS")
print("="*70)
print("Critical! Finds cycles in your design (unintended latches)")
print("\nExample: tool.detect_combinational_loops()")
print("-"*70)
loops = tool.detect_combinational_loops()
print(f"\n✓ Found {len(loops)} loops (flip-flop feedback is normal)")

# ============================================================================
# FEATURE 6: Trace Signal Path
# ============================================================================
print("\n" + "="*70)
print("FEATURE 6: TRACE SIGNAL PATH")
print("="*70)
print("Find all paths between two signals - great for timing analysis")
print("\nExample: tool.trace_signal_path('n_186', 'n_243')")
print("-"*70)
tool.trace_signal_path("n_186", "n_243")

# ============================================================================
# FEATURE 7: Critical Path Analysis
# ============================================================================
print("\n" + "="*70)
print("FEATURE 7: CRITICAL PATH ANALYSIS")
print("="*70)
print("Find longest paths in design - potential timing problems")
print("\nExample: tool.find_critical_paths(top_n=5)")
print("-"*70)
tool.find_critical_paths(top_n=5)

# ============================================================================
# FEATURE 8: Design Statistics
# ============================================================================
print("\n" + "="*70)
print("FEATURE 8: DESIGN STATISTICS")
print("="*70)
print("Get comprehensive stats about your design")

# Gate type statistics
gate_types = {}
for node in tool.dag.nodes():
    gtype = tool.dag.nodes[node].get('gate_type', 'unknown')
    gate_types[gtype] = gate_types.get(gtype, 0) + 1

print(f"\nTotal Gates: {tool.dag.number_of_nodes()}")
print(f"Total Connections: {tool.dag.number_of_edges()}")

print(f"\nTop 10 Gate Types:")
for gtype, count in sorted(gate_types.items(), key=lambda x: -x[1])[:10]:
    pct = (count / tool.dag.number_of_nodes()) * 100
    print(f"  {gtype:20s}: {count:4d} ({pct:5.2f}%)")

# Fanout analysis
fanouts = [(n, tool.dag.out_degree(n)) for n in tool.dag.nodes()]
fanouts.sort(key=lambda x: -x[1])

print(f"\nTop 5 Highest Fanout Gates:")
for gate, fanout in fanouts[:5]:
    gtype = tool.dag.nodes[gate].get('gate_type', 'unknown')
    print(f"  {gate:15s} ({gtype:15s}): {fanout} outputs")

# ============================================================================
# FEATURE 9: Export Full Visualization
# ============================================================================
print("\n" + "="*70)
print("FEATURE 9: EXPORT INTERACTIVE VISUALIZATION")
print("="*70)
print("Create interactive HTML graph of your entire design")
print("\nExample: tool.export_pyvis('my_design.html')")
print("-"*70)
tool.export_pyvis("netlist_visualization.html")
print("✓ Saved to: netlist_visualization.html")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*70)
print("INTERACTIVE MODE - Try it yourself!")
print("="*70)
print("\nYou can use these methods directly in Python or the interactive interface:")
print("\nMethod 1: Python Script")
print("  tool = VerilogDagTool('netlist.v')")
print("  tool.parse_and_build()")
print("  tool.backward_cone('g2705')  # Use any feature")
print("\nMethod 2: Interactive Interface")
print("  python debug_tool.py")
print("  Then type commands like: backward g2705")

print("\n" + "="*70)
print("COMMON USE CASES")
print("="*70)

print("\n1. DEBUG A FAILING OUTPUT:")
print("   tool.backward_cone('failing_signal')  # Find what could cause it")
print("   tool.verify_gate('suspect_gate')      # Check connections")

print("\n2. ANALYZE TIMING PATH:")
print("   tool.trace_signal_path('clk', 'output')  # See the path")
print("   tool.find_critical_paths(10)             # Find longest paths")

print("\n3. UNDERSTAND IMPACT OF A CHANGE:")
print("   tool.forward_cone('modified_gate')       # See what it affects")
print("   tool.export_cone_subgraph(cone, 'impact.html')  # Visualize")

print("\n4. VERIFY DESIGN QUALITY:")
print("   tool.detect_combinational_loops()  # Check for bugs")
print("   # Get gate counts, fanout stats")

print("\n" + "="*70)
print("FILES CREATED:")
print("="*70)
print("  ✓ cone_g2705.html - Subgraph visualization")
print("  ✓ netlist_visualization.html - Full design")
print("  ✓ All analysis printed above")

print("\n" + "="*70)
print("✓ DEMO COMPLETE!")
print("="*70)
print("\nNext steps:")
print("1. Open the HTML files in your browser to explore interactively")
print("2. Run: python debug_tool.py  (for interactive command mode)")
print("3. Modify this script to analyze your specific gates/signals")
