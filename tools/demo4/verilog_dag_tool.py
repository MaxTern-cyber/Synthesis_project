import networkx as nx
import re
from pyvis.network import Network
import plotly.graph_objects as go
import plotly.io as pio
import os

class VerilogDagTool:
    def __init__(self, verilog_path):
        self.verilog_path = verilog_path
        self.dag = nx.DiGraph()
        self.signal_drivers = {}  # Maps signal to the gate that drives it (output)
        self.signal_readers = {}  # Maps signal to gates that read it (inputs)
        
    def parse_and_build(self):
        """Parses gate-level Verilog netlist and builds signal connectivity DAG."""
        with open(self.verilog_path, 'r') as f:
            content = f.read()
        
        # Remove comments
        content = re.sub(r'//.*?\n', '\n', content)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Pattern to match gate instances: GATE_TYPE instance_name(.PORT (signal), ...);
        # Example: NAND2X2 g5536(.A (n_48), .B (n_185), .Y (n_186));
        gate_pattern = r'(\w+)\s+(\w+)\s*\((.*?)\);'
        
        for match in re.finditer(gate_pattern, content, re.DOTALL):
            gate_type = match.group(1)
            instance_name = match.group(2)
            connections = match.group(3)
            
            # Add the gate instance as a node
            self.dag.add_node(instance_name, gate_type=gate_type)
            
            # Parse port connections: .PORT (signal)
            port_pattern = r'\.(\w+)\s*\(([^)]+)\)'
            ports = re.findall(port_pattern, connections)
            
            inputs = []
            outputs = []
            
            for port_name, signal in ports:
                signal = signal.strip()
                
                # Common output port names
                if port_name in ['Y', 'Q', 'QN', 'CO', 'S', 'SO', 'Z']:
                    outputs.append(signal)
                    # This gate drives this signal
                    self.signal_drivers[signal] = instance_name
                else:
                    # Input ports (A, B, C, D, CK, D, etc.)
                    inputs.append(signal)
                    if signal not in self.signal_readers:
                        self.signal_readers[signal] = []
                    self.signal_readers[signal].append(instance_name)
            
            # Create edges: from input signals to this gate
            for input_signal in inputs:
                if input_signal in self.signal_drivers:
                    # Edge from the gate that drives this signal to current gate
                    driver_gate = self.signal_drivers[input_signal]
                    self.dag.add_edge(driver_gate, instance_name, signal=input_signal)
            
            # Note: Edges from this gate to readers will be created when we process those readers
    
    # ============= CRITICAL PATH ANALYSIS =============
    def find_critical_paths(self, top_n=10):
        """Find longest paths in the design (critical paths)."""
        print(f"\n{'='*60}")
        print("CRITICAL PATH ANALYSIS")
        print(f"{'='*60}")
        
        try:
            # Find longest paths using topological sort
            longest_paths = []
            
            # Get all source nodes (no predecessors)
            sources = [n for n in self.dag.nodes() if self.dag.in_degree(n) == 0]
            # Get all sink nodes (no successors)
            sinks = [n for n in self.dag.nodes() if self.dag.out_degree(n) == 0]
            
            print(f"Source nodes (primary inputs): {len(sources)}")
            print(f"Sink nodes (primary outputs): {len(sinks)}")
            
            # Sample paths from sources to sinks
            for source in sources[:5]:  # Limit to first 5 sources for performance
                for sink in sinks[:5]:  # Limit to first 5 sinks
                    try:
                        paths = list(nx.all_simple_paths(self.dag, source, sink, cutoff=50))
                        for path in paths:
                            longest_paths.append((len(path), path))
                    except:
                        pass
            
            # Sort by path length
            longest_paths.sort(reverse=True, key=lambda x: x[0])
            
            print(f"\nTop {min(top_n, len(longest_paths))} Critical Paths:")
            for i, (length, path) in enumerate(longest_paths[:top_n], 1):
                print(f"\n{i}. Path Length: {length} gates")
                print(f"   Start: {path[0]} ({self.dag.nodes[path[0]]['gate_type']})")
                print(f"   End: {path[-1]} ({self.dag.nodes[path[-1]]['gate_type']})")
                if length <= 10:
                    print(f"   Path: {' -> '.join(path)}")
                else:
                    print(f"   Path: {' -> '.join(path[:3])} -> ... -> {' -> '.join(path[-3:])}")
        except Exception as e:
            print(f"Error in critical path analysis: {e}")
    
    def calculate_logic_depth(self):
        """Calculate logic depth/level for each gate."""
        print(f"\n{'='*60}")
        print("LOGIC DEPTH ANALYSIS")
        print(f"{'='*60}")
        
        # Use topological generations to find levels
        levels = {}
        for node in nx.topological_sort(self.dag):
            # Level is max of predecessor levels + 1
            pred_levels = [levels[pred] for pred in self.dag.predecessors(node) if pred in levels]
            levels[node] = max(pred_levels, default=-1) + 1
        
        max_level = max(levels.values(), default=0)
        print(f"Maximum logic depth: {max_level} levels")
        
        # Count gates at each level
        level_counts = {}
        for node, level in levels.items():
            level_counts[level] = level_counts.get(level, 0) + 1
        
        print(f"\nGates per level:")
        for level in sorted(level_counts.keys())[:10]:  # Show first 10 levels
            print(f"  Level {level}: {level_counts[level]} gates")
        
        return levels
    
    # ============= CONE OF INFLUENCE ANALYSIS =============
    def backward_cone(self, gate_or_signal, max_depth=None):
        """Find all gates that influence this gate/signal (backward trace)."""
        print(f"\n{'='*60}")
        print(f"BACKWARD CONE OF INFLUENCE: {gate_or_signal}")
        print(f"{'='*60}")
        
        # Find the gate
        if gate_or_signal in self.signal_drivers:
            start_gate = self.signal_drivers[gate_or_signal]
            print(f"Signal '{gate_or_signal}' driven by gate: {start_gate}")
        elif gate_or_signal in self.dag.nodes():
            start_gate = gate_or_signal
        else:
            print(f"Gate/signal '{gate_or_signal}' not found!")
            return set()
        
        # Get all ancestors (backward trace)
        ancestors = nx.ancestors(self.dag, start_gate)
        ancestors.add(start_gate)
        
        print(f"\nTotal gates in backward cone: {len(ancestors)}")
        
        # Categorize by gate type
        gate_types = {}
        for gate in ancestors:
            gtype = self.dag.nodes[gate].get('gate_type', 'unknown')
            gate_types[gtype] = gate_types.get(gtype, 0) + 1
        
        print(f"\nGate types in cone:")
        for gtype, count in sorted(gate_types.items(), key=lambda x: -x[1])[:10]:
            print(f"  {gtype}: {count}")
        
        # Find direct predecessors
        direct_preds = list(self.dag.predecessors(start_gate))
        if direct_preds:
            print(f"\nDirect inputs ({len(direct_preds)} gates):")
            for pred in direct_preds[:10]:  # Show first 10
                edge_data = self.dag.get_edge_data(pred, start_gate)
                signal = edge_data.get('signal', 'N/A')
                print(f"  {pred} ({self.dag.nodes[pred]['gate_type']}) -> signal: {signal}")
        
        return ancestors
    
    def forward_cone(self, gate_or_signal, max_depth=None):
        """Find all gates affected by this gate/signal (forward trace)."""
        print(f"\n{'='*60}")
        print(f"FORWARD CONE OF INFLUENCE: {gate_or_signal}")
        print(f"{'='*60}")
        
        # Find the gate
        if gate_or_signal in self.signal_drivers:
            start_gate = self.signal_drivers[gate_or_signal]
            print(f"Signal '{gate_or_signal}' driven by gate: {start_gate}")
        elif gate_or_signal in self.dag.nodes():
            start_gate = gate_or_signal
        else:
            print(f"Gate/signal '{gate_or_signal}' not found!")
            return set()
        
        # Get all descendants (forward trace)
        descendants = nx.descendants(self.dag, start_gate)
        descendants.add(start_gate)
        
        print(f"\nTotal gates in forward cone: {len(descendants)}")
        
        # Categorize by gate type
        gate_types = {}
        for gate in descendants:
            gtype = self.dag.nodes[gate].get('gate_type', 'unknown')
            gate_types[gtype] = gate_types.get(gtype, 0) + 1
        
        print(f"\nGate types in cone:")
        for gtype, count in sorted(gate_types.items(), key=lambda x: -x[1])[:10]:
            print(f"  {gtype}: {count}")
        
        # Find direct successors
        direct_succs = list(self.dag.successors(start_gate))
        if direct_succs:
            print(f"\nDirect outputs ({len(direct_succs)} gates):")
            for succ in direct_succs[:10]:  # Show first 10
                edge_data = self.dag.get_edge_data(start_gate, succ)
                signal = edge_data.get('signal', 'N/A')
                print(f"  {start_gate} -> {succ} ({self.dag.nodes[succ]['gate_type']}) via: {signal}")
        
        return descendants
    
    def export_cone_subgraph(self, gates, output_path):
        """Export a subgraph containing only specified gates."""
        subgraph = self.dag.subgraph(gates)
        net = Network(height="750px", width="100%", notebook=False, directed=True)
        
        for node in subgraph.nodes():
            gate_type = subgraph.nodes[node].get('gate_type', 'unknown')
            label = f"{node}\n({gate_type})"
            net.add_node(node, label=label, title=f"{node}: {gate_type}")
        
        for source, target, data in subgraph.edges(data=True):
            signal = data.get('signal', '')
            net.add_edge(source, target, title=f"signal: {signal}", label=signal)
        
        net.toggle_physics(True)
        net.save_graph(output_path)
        print(f"\nSubgraph saved to {output_path}")
    
    # ============= COMBINATIONAL LOOP DETECTION =============
    def detect_combinational_loops(self):
        """Detect cycles in the DAG (combinational loops - critical bug!)."""
        print(f"\n{'='*60}")
        print("COMBINATIONAL LOOP DETECTION")
        print(f"{'='*60}")
        
        try:
            cycles = list(nx.simple_cycles(self.dag))
            
            if cycles:
                print(f"\n⚠️  WARNING: {len(cycles)} COMBINATIONAL LOOP(S) DETECTED!")
                print("This is a critical design error!\n")
                
                for i, cycle in enumerate(cycles[:10], 1):  # Show first 10 cycles
                    print(f"\nLoop {i}: {len(cycle)} gates")
                    if len(cycle) <= 10:
                        print(f"  Path: {' -> '.join(cycle)} -> {cycle[0]}")
                    else:
                        print(f"  Path: {' -> '.join(cycle[:5])} -> ... -> {' -> '.join(cycle[-5:])} -> {cycle[0]}")
                    
                    # Show gate types in loop
                    gate_types = [self.dag.nodes[g]['gate_type'] for g in cycle[:5]]
                    print(f"  Gate types: {', '.join(gate_types)}")
                
                return cycles
            else:
                print("✓ No combinational loops detected. Design is acyclic.")
                return []
        except Exception as e:
            print(f"Error in loop detection: {e}")
            return []
    
    # ============= SIGNAL TRACING =============
    def trace_signal_path(self, start_signal, end_signal):
        """Trace all paths from start signal to end signal."""
        print(f"\n{'='*60}")
        print(f"SIGNAL PATH TRACE: {start_signal} -> {end_signal}")
        print(f"{'='*60}")
        
        # Find gates driving these signals
        if start_signal not in self.signal_drivers:
            print(f"Start signal '{start_signal}' not found or is a primary input!")
            return
        if end_signal not in self.signal_drivers:
            print(f"End signal '{end_signal}' not found or is a primary input!")
            return
        
        start_gate = self.signal_drivers[start_signal]
        end_gate = self.signal_drivers[end_signal]
        
        print(f"Start gate: {start_gate} ({self.dag.nodes[start_gate]['gate_type']})")
        print(f"End gate: {end_gate} ({self.dag.nodes[end_gate]['gate_type']})")
        
        try:
            # Find all simple paths
            paths = list(nx.all_simple_paths(self.dag, start_gate, end_gate, cutoff=20))
            
            if not paths:
                print(f"\nNo path found between {start_signal} and {end_signal}")
                return
            
            print(f"\nFound {len(paths)} path(s):")
            for i, path in enumerate(paths[:5], 1):  # Show first 5 paths
                print(f"\nPath {i} ({len(path)} gates):")
                if len(path) <= 8:
                    for gate in path:
                        gtype = self.dag.nodes[gate]['gate_type']
                        print(f"  {gate} ({gtype})")
                else:
                    print(f"  {path[0]} -> ... ({len(path)-2} gates) ... -> {path[-1]}")
        except Exception as e:
            print(f"Error tracing path: {e}")

    def export_pyvis(self, output_path):
        """Generates 2D interactive graph with gate types and signals."""
        net = Network(height="750px", width="100%", notebook=False, directed=True)
        
        # Add nodes with labels showing gate type
        for node in self.dag.nodes():
            gate_type = self.dag.nodes[node].get('gate_type', 'unknown')
            label = f"{node}\n({gate_type})"
            net.add_node(node, label=label, title=f"{node}: {gate_type}")
        
        # Add edges with signal labels
        for source, target, data in self.dag.edges(data=True):
            signal = data.get('signal', '')
            net.add_edge(source, target, title=f"signal: {signal}", label=signal)
        
        net.toggle_physics(True)
        net.save_graph(output_path)
    
    def verify_gate(self, instance_name):
        """Verify connectivity for a specific gate instance."""
        if instance_name not in self.dag.nodes():
            print(f"Gate {instance_name} not found in DAG")
            return
        
        gate_type = self.dag.nodes[instance_name].get('gate_type', 'unknown')
        print(f"\nGate: {instance_name} (Type: {gate_type})")
        
        # Show inputs (predecessors)
        predecessors = list(self.dag.predecessors(instance_name))
        if predecessors:
            print(f"  Inputs from gates:")
            for pred in predecessors:
                edge_data = self.dag.get_edge_data(pred, instance_name)
                signal = edge_data.get('signal', 'N/A')
                pred_type = self.dag.nodes[pred].get('gate_type', 'unknown')
                print(f"    {pred} ({pred_type}) -> signal: {signal}")
        else:
            print(f"  Inputs: Primary inputs (no predecessor gates)")
        
        # Show outputs (successors)
        successors = list(self.dag.successors(instance_name))
        if successors:
            print(f"  Outputs to gates:")
            for succ in successors:
                edge_data = self.dag.get_edge_data(instance_name, succ)
                signal = edge_data.get('signal', 'N/A')
                succ_type = self.dag.nodes[succ].get('gate_type', 'unknown')
                print(f"    {instance_name} -> {succ} ({succ_type}) via signal: {signal}")
        else:
            print(f"  Outputs: Primary outputs (no successor gates)")

    def export_plotly_3d(self, output_path):
        """Generates 3D interactive graph."""
        pos = nx.spring_layout(self.dag, dim=3, seed=42)
        
        # Edge lines
        edge_x, edge_y, edge_z = [], [], []
        for edge in self.dag.edges():
            x0, y0, z0 = pos[edge[0]]
            x1, y1, z1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_z.extend([z0, z1, None])

        # Node points
        node_x, node_y, node_z = zip(*[pos[node] for node in self.dag.nodes()])
        
        fig = go.Figure(data=[
            go.Scatter3d(x=edge_x, y=edge_y, z=edge_z, mode='lines', line=dict(color='black', width=1)),
            go.Scatter3d(x=node_x, y=node_y, z=node_z, mode='markers', 
                         marker=dict(size=5, color='blue'), text=list(self.dag.nodes()))
        ])
        pio.write_html(fig, output_path)

if __name__ == "__main__":
    # Update these paths
    input_verilog = "netlist.v"  # Your Verilog netlist file
    
    tool = VerilogDagTool(input_verilog)
    tool.parse_and_build()
    
    print(f"Nodes: {tool.dag.number_of_nodes()} | Edges: {tool.dag.number_of_edges()}")
    
    # Verify specific gate (the example you provided)
    tool.verify_gate("g2705")
    
    # Verify another gate to show the flow
    print("\n" + "="*60)
    tool.verify_gate("g5536")
    
    tool.export_pyvis("interactive_2d.html")
    print("\nVisualization saved to interactive_2d.html")
    # tool.export_plotly_3d("interactive_3d.html")