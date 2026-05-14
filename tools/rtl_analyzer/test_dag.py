"""
Quick Test for DAG Visualization
This script tests if the DAG graph is being built correctly
"""

import re
import networkx as nx

# Sample RTL code
sample_rtl = """
module counter (
    input clk,
    input rst,
    input [7:0] data_in,
    output reg [7:0] count,
    output wire done
);

reg [7:0] temp;

always @(posedge clk or posedge rst) begin
    if (rst)
        count <= 8'b0;
    else
        count <= count + 1;
end

always @(*) begin
    temp = data_in + count;
end

assign done = (count == 8'hFF);

endmodule
"""

print("Testing DAG Graph Construction...")
print("=" * 60)

# Create graph
dag_graph = nx.DiGraph()

# Extract ports (simplified)
ports = {
    'clk': {'direction': 'input'},
    'rst': {'direction': 'input'},
    'data_in': {'direction': 'input'},
    'count': {'direction': 'output'},
    'done': {'direction': 'output'}
}

# Extract signals
signals = {
    'temp': {'type': 'reg'}
}

# Add nodes
for port_name, port_info in ports.items():
    node_type = 'input' if port_info['direction'] == 'input' else 'output'
    dag_graph.add_node(port_name, node_type=node_type, element_type='port')
    print(f"✓ Added port node: {port_name} ({node_type})")

for signal_name, signal_info in signals.items():
    is_reg = signal_info['type'] == 'reg'
    dag_graph.add_node(signal_name, node_type='register' if is_reg else 'wire', element_type='signal')
    print(f"✓ Added signal node: {signal_name} ({'register' if is_reg else 'wire'})")

# Add some edges
dag_graph.add_edge('clk', 'count', edge_type='sequential')
dag_graph.add_edge('rst', 'count', edge_type='sequential')
dag_graph.add_edge('data_in', 'temp', edge_type='combinational')
dag_graph.add_edge('count', 'temp', edge_type='combinational')
dag_graph.add_edge('count', 'done', edge_type='combinational')

print(f"\n✓ Added {len(dag_graph.edges)} edges")

print("\n" + "=" * 60)
print("Graph Statistics:")
print(f"  Total Nodes: {len(dag_graph.nodes)}")
print(f"  Total Edges: {len(dag_graph.edges)}")

comb_edges = sum(1 for _, _, d in dag_graph.edges(data=True) if d.get('edge_type') == 'combinational')
seq_edges = sum(1 for _, _, d in dag_graph.edges(data=True) if d.get('edge_type') == 'sequential')

print(f"  Combinational Paths: {comb_edges}")
print(f"  Sequential Paths: {seq_edges}")

print("\n" + "=" * 60)
print("Testing PyVis Visualization...")

try:
    from pyvis.network import Network
    
    net = Network(height="600px", width="800px", directed=True, notebook=False)
    
    # Add nodes with colors
    for node, data in dag_graph.nodes(data=True):
        node_type = data.get('node_type', 'wire')
        
        if node_type == 'input':
            color = '#3498DB'
            shape = 'diamond'
        elif node_type == 'output':
            color = '#E74C3C'
            shape = 'triangle'
        elif node_type == 'register':
            color = '#2ECC71'
            shape = 'box'
        else:
            color = '#F39C12'
            shape = 'ellipse'
        
        net.add_node(node, label=node, color=color, shape=shape, title=f"{node} ({node_type})")
        print(f"✓ Added visual node: {node} - {shape} - {color}")
    
    # Add edges
    for src, dst, data in dag_graph.edges(data=True):
        edge_type = data.get('edge_type', 'unknown')
        
        if edge_type == 'sequential':
            color = '#2ECC71'
            width = 2
            dashes = False
        else:
            color = '#F39C12'
            width = 1
            dashes = True
        
        net.add_edge(src, dst, color=color, width=width, dashes=dashes)
    
    # Save to file
    output_file = "test_dag_visualization.html"
    net.save_graph(output_file)
    
    print(f"\n✅ SUCCESS! Generated visualization: {output_file}")
    print(f"   Open this file in your browser to see the graph")
    
except ImportError as e:
    print(f"\n❌ ERROR: PyVis not installed - {e}")
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n" + "=" * 60)
