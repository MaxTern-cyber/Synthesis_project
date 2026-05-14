"""
Enhanced Verilog DAG Tool - Test Script
Demonstrates all the new features:
1. Critical Path Analysis
2. Cone of Influence (Forward/Backward)
3. Combinational Loop Detection
4. Interactive Interface
"""

import os, sys
# Anchor to repo root (this file lives at <repo>/tools/demo1/)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Load the tool implementation from the sibling file
_here = os.path.dirname(__file__)
exec(open(os.path.join(_here, 'level1_final.py'), encoding='utf-8').read().replace("if __name__", "if False"), globals())

if __name__ == "__main__":
    input_verilog = "netlist.v"
    
    print("="*70)
    print("ENHANCED VERILOG DAG TOOL - DEBUG SUITE")
    print("="*70)
    print("\nLoading netlist...")
    
    tool = VerilogDagTool(input_verilog)
    tool.parse_and_build()
    
    print(f"\n{'='*70}")
    print(f"✓ Netlist loaded successfully!")
    print(f"  Total Gates: {tool.dag.number_of_nodes()}")
    print(f"  Total Connections: {tool.dag.number_of_edges()}")
    print(f"{'='*70}")
    
    # Feature 1: Combinational Loop Detection
    tool.detect_combinational_loops()
    
    # Feature 2: Backward Cone of Influence
    print("\n" + "="*70)
    print("FEATURE DEMO: Backward Cone of Influence")
    print("="*70)
    tool.backward_cone("g2705")
    
    # Feature 3: Forward Cone of Influence  
    print("\n" + "="*70)
    print("FEATURE DEMO: Forward Cone of Influence")
    print("="*70)
    tool.forward_cone("g5536")
    
    # Feature 4: Critical Path Analysis
    tool.find_critical_paths(top_n=5)
    
    # Feature 5: Logic Depth
    tool.calculate_logic_depth()
    
    # Feature 6: Signal Tracing
    print("\n" + "="*70)
    print("FEATURE DEMO: Signal Path Tracing")
    print("="*70)
    tool.trace_signal_path("n_186", "n_243")
    
    # Export visualization
    tool.export_pyvis("interactive_2d.html")
    print(f"\n{'='*70}")
    print("✓ Full design visualization saved to: interactive_2d.html")
    print(f"{'='*70}")
    
    # Interactive mode
    print("\n" + "="*70)
    print("STARTING INTERACTIVE DEBUG INTERFACE")
    print("="*70)
    print("\nType 'help' for available commands, 'quit' to exit\n")
    
    while True:
        try:
            cmd = input("debug> ").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split()
            command = parts[0].lower()
            
            if command in ["quit", "exit", "q"]:
                print("\nExiting debug interface. Goodbye!")
                break
            
            elif command == "help":
                print("\nAvailable Commands:")
                print("  verify <gate>              - Show gate connectivity")
                print("  backward <gate/signal>     - Backward cone analysis")
                print("  forward <gate/signal>      - Forward cone analysis")
                print("  trace <sig1> <sig2>        - Trace signal path")
                print("  critical [n]               - Find critical paths (default: 10)")
                print("  loops                      - Detect combinational loops")
                print("  depth                      - Calculate logic depth")
                print("  export_cone <gate> <file>  - Export cone subgraph")
                print("  stats                      - Show design statistics")
                print("  quit                       - Exit interface\n")
            
            elif command == "verify":
                if len(parts) < 2:
                    print("Usage: verify <gate>")
                else:
                    tool.verify_gate(parts[1])
            
            elif command == "backward":
                if len(parts) < 2:
                    print("Usage: backward <gate/signal>")
                else:
                    tool.backward_cone(parts[1])
            
            elif command == "forward":
                if len(parts) < 2:
                    print("Usage: forward <gate/signal>")
                else:
                    tool.forward_cone(parts[1])
            
            elif command == "trace":
                if len(parts) < 3:
                    print("Usage: trace <signal1> <signal2>")
                else:
                    tool.trace_signal_path(parts[1], parts[2])
            
            elif command == "critical":
                n = int(parts[1]) if len(parts) > 1 else 10
                tool.find_critical_paths(top_n=n)
            
            elif command == "loops":
                tool.detect_combinational_loops()
            
            elif command == "depth":
                tool.calculate_logic_depth()
            
            elif command == "export_cone":
                if len(parts) < 3:
                    print("Usage: export_cone <gate> <output.html>")
                else:
                    cone = tool.backward_cone(parts[1])
                    if cone:
                        tool.export_cone_subgraph(cone, parts[2])
            
            elif command == "stats":
                print(f"\n{'='*60}")
                print("DESIGN STATISTICS")
                print(f"{'='*60}")
                print(f"Total Gates: {tool.dag.number_of_nodes()}")
                print(f"Total Connections: {tool.dag.number_of_edges()}")
                
                gate_types = {}
                for node in tool.dag.nodes():
                    gtype = tool.dag.nodes[node].get('gate_type', 'unknown')
                    gate_types[gtype] = gate_types.get(gtype, 0) + 1
                
                print(f"\nTop 15 Gate Types:")
                for gtype, count in sorted(gate_types.items(), key=lambda x: -x[1])[:15]:
                    pct = (count / tool.dag.number_of_nodes()) * 100
                    print(f"  {gtype:20s}: {count:4d} ({pct:5.2f}%)")
                
                fanouts = [(n, tool.dag.out_degree(n)) for n in tool.dag.nodes()]
                fanouts.sort(key=lambda x: -x[1])
                
                print(f"\nTop 10 Highest Fanout Gates:")
                for gate, fanout in fanouts[:10]:
                    gtype = tool.dag.nodes[gate].get('gate_type', 'unknown')
                    print(f"  {gate:15s} ({gtype:15s}): {fanout} outputs")
            
            else:
                print(f"Unknown command: '{command}'. Type 'help' for available commands.")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'quit' to exit.")
        except Exception as e:
            print(f"Error: {e}")
