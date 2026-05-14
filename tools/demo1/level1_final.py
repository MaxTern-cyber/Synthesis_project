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
        self.modules = {}  # Store module definitions
        
    def parse_and_build(self):
        """Parses Verilog netlist and builds the DiGraph."""
        with open(self.verilog_path, 'r') as f:
            content = f.read()
        
        # Remove comments
        content = re.sub(r'//.*?\n', '\n', content)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Find all module definitions
        module_pattern = r'module\s+(\w+)\s*(?:\(.*?\))?\s*;(.*?)endmodule'
        modules = re.findall(module_pattern, content, re.DOTALL)
        
        for module_name, module_body in modules:
            self.modules[module_name] = module_body
            self.dag.add_node(module_name)
        
        # Find all module instantiations and create edges
        for module_name, module_body in modules:
            # Pattern for module instantiation: module_type instance_name (connections);
            inst_pattern = r'(\w+)\s+(\w+)\s*\('
            instances = re.findall(inst_pattern, module_body)
            
            for inst_module, inst_name in instances:
                if inst_module in self.modules:
                    # Edge from instantiated module to parent module
                    self.dag.add_edge(inst_module, module_name)
                    # Also add instance as a node
                    instance_node = f"{module_name}.{inst_name}"
                    self.dag.add_node(instance_node)
                    self.dag.add_edge(instance_node, module_name)

    def export_pyvis(self, output_path):
        """Generates 2D interactive graph."""
        net = Network(height="750px", width="100%", notebook=False, directed=True)
        net.from_nx(self.dag)
        net.toggle_physics(True) # Enabled for better initial layout
        net.save_graph(output_path)

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
    
    tool.export_pyvis("interactive_2d.html")
    # tool.export_plotly_3d("interactive_3d.html")
