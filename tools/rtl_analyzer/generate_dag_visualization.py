#!/usr/bin/env python3
"""
Standalone DAG Visualization Generator for RTL Designs
Reads a Verilog file and generates an interactive HTML visualization

Usage:
    python generate_dag_visualization.py <verilog_file> [options]
    
Example:
    python generate_dag_visualization.py netlist.v --layout hierarchical --output dag.html
"""

import sys
import os
import re
import argparse
import networkx as nx
from pyvis.network import Network

class VerilogDAGGenerator:
    """Generates DAG visualization from Verilog files"""
    
    def __init__(self, verilog_file):
        self.verilog_file = verilog_file
        self.module_name = ""
        self.ports = {}
        self.wires = []
        self.regs = []
        self.assign_statements = []
        self.sequential_logic = []
        self.clock_signals = set()
        self.clock_domains = {}
        self.dag_graph = nx.DiGraph()
        
    def parse_verilog(self):
        """Parse the Verilog file"""
        print(f">> Parsing Verilog file: {self.verilog_file}")
        
        with open(self.verilog_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Remove comments
        content = re.sub(r'//.*?\n', '\n', content)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Extract module name
        module_match = re.search(r'module\s+(\w+)', content)
        if module_match:
            self.module_name = module_match.group(1)
            print(f"   Module: {self.module_name}")
        
        # Extract ports
        port_patterns = [
            (r'input\s+(?:wire\s+)?(?:\[\d+:\d+\])?\s*(\w+)', 'input'),
            (r'output\s+(?:reg\s+|wire\s+)?(?:\[\d+:\d+\])?\s*(\w+)', 'output'),
            (r'inout\s+(?:wire\s+)?(?:\[\d+:\d+\])?\s*(\w+)', 'inout')
        ]
        
        for pattern, direction in port_patterns:
            for match in re.finditer(pattern, content):
                port_name = match.group(1)
                self.ports[port_name] = {'direction': direction}
        
        print(f"   Ports: {len(self.ports)}")
        
        # Extract wires and regs
        for match in re.finditer(r'wire\s+(?:\[\d+:\d+\])?\s*(\w+)', content):
            self.wires.append(match.group(1))
        
        for match in re.finditer(r'reg\s+(?:\[\d+:\d+\])?\s*(\w+)', content):
            self.regs.append(match.group(1))
        
        # Extract assign statements
        for match in re.finditer(r'assign\s+(\w+)\s*=\s*([^;]+);', content):
            self.assign_statements.append({
                'lhs': match.group(1),
                'rhs': match.group(2)
            })
        
        # Extract sequential logic (always @(posedge/negedge))
        for match in re.finditer(r'always\s*@\s*\(([^)]+)\)\s*begin(.*?)end', content, re.DOTALL):
            sensitivity = match.group(1)
            body = match.group(2)
            
            # Identify clock signals
            clock_match = re.findall(r'(?:posedge|negedge)\s+(\w+)', sensitivity)
            if clock_match:
                self.clock_signals.update(clock_match)
            
            # Extract driven signals
            driven = re.findall(r'(\w+)\s*(?:<=|=)', body)
            
            self.sequential_logic.append({
                'sensitivity': sensitivity,
                'body': body,
                'driven_signals': driven
            })
        
        print(f"   Clocks: {len(self.clock_signals)}")
        print(f"   Sequential blocks: {len(self.sequential_logic)}")
        print(f"   Assign statements: {len(self.assign_statements)}")
        
    def build_dag(self):
        """Build a netlist-style graph using explicit connection pairs.
        
        Algorithm:
        1. Parse and store all nodes with metadata
        2. Store all connections as [source, destination] pairs
        3. Create all nodes in graph
        4. Create all edges from stored pairs
        """
        print(f"\n>> Building netlist-style graph...")
        
        # Data structures to store everything
        nodes = {}           # node_id -> {node_type, cell_type, label, ...}
        connections = []     # List of [source_id, dest_id, net_name, ...]
        net_drivers = {}     # net_name -> node_id that drives it
        
        instance_id = 0
        
        # ========== STEP 1: Parse and store all nodes ==========
        
        # PRIMARY INPUTS
        for port_name, port_info in self.ports.items():
            if port_info['direction'] == 'input':
                node_id = f"PI_{port_name}"
                nodes[node_id] = {
                    'node_type': 'primary_input',
                    'port_name': port_name,
                    'label': port_name
                }
                net_drivers[port_name] = node_id
        
        # PRIMARY OUTPUTS
        output_nets = []
        for port_name, port_info in self.ports.items():
            if port_info['direction'] == 'output':
                node_id = f"PO_{port_name}"
                nodes[node_id] = {
                    'node_type': 'primary_output',
                    'port_name': port_name,
                    'label': port_name
                }
                output_nets.append(port_name)
        
        # FLIP-FLOPS
        ff_connections = {}  # ff_id -> [list of input nets]
        for block in self.sequential_logic:
            has_clock = any(clk in block['sensitivity'] for clk in self.clock_signals)
            if has_clock:
                clock_sig = None
                for clk in self.clock_signals:
                    if clk in block['sensitivity']:
                        clock_sig = clk
                        break
                
                for driven_sig in block['driven_signals']:
                    instance_id += 1
                    node_id = f"DFF_{instance_id}"
                    
                    # Parse D inputs from always block (skip reset initialization)
                    d_input_nets = set()  # Use set to avoid duplicates
                    body = block['body']
                    
                    # Skip reset block - look for 'else' clause with actual signal logic
                    in_reset_block = False
                    in_else_block = False
                    
                    for line in body.split('\n'):
                        # Track if we're in reset or operational block
                        if 'if' in line and ('!rst' in line or '~rst' in line):
                            in_reset_block = True
                            in_else_block = False
                        elif 'else' in line and in_reset_block:
                            in_reset_block = False
                            in_else_block = True
                        
                        # Only process lines in the else block (operational logic)
                        if in_else_block and driven_sig in line and ('=' in line or '<=' in line):
                            if '<=' in line:
                                parts = line.split('<=')
                            else:
                                parts = line.split('=')
                            if len(parts) > 1:
                                # Get RHS (everything after = or <=)
                                rhs = parts[1].split(';')[0].strip()
                                
                                # Remove bit slices and literals to extract base signal names
                                cleaned = re.sub(r'\[.*?\]', '', rhs)  # Remove [bit:range]
                                cleaned = re.sub(r"[0-9]+'[bdh][0-9a-fA-F_]+", '', cleaned)  # Remove literals
                                cleaned = re.sub(r'[{}()?:,&|^~!+\-*/<>=]', ' ', cleaned)  # Replace operators
                                
                                # Extract identifiers
                                signals = re.findall(r'\b([a-zA-Z_]\w*)\b', cleaned)
                                print(f"      Line: {line.strip()[:70]}")
                                print(f"      Extracted signals: {signals}")
                                
                                # Filter valid signal names (ports, wires, regs)
                                for sig in signals:
                                    if sig in ['if', 'else', 'begin', 'end', 'case', 'default', 'posedge', 'negedge', 'endcase']:
                                        continue
                                    if sig in self.ports:
                                        d_input_nets.add(sig)
                                        print(f"      ✓ Found PORT signal: {sig}")
                                    elif sig in self.wires:
                                        d_input_nets.add(sig)
                                        print(f"      ✓ Found WIRE signal: {sig}")
                                    elif sig in self.regs:
                                        d_input_nets.add(sig)
                                        print(f"      ✓ Found REG signal: {sig}")
                    
                    d_input_nets = list(d_input_nets)
                    print(f"   {node_id} ({driven_sig}) D inputs: {d_input_nets}")
                    
                    # Store FF node
                    nodes[node_id] = {
                        'node_type': 'flip_flop',
                        'cell_type': 'DFF',
                        'instance_name': node_id,
                        'output_net': driven_sig,
                        'clock_net': clock_sig,
                        'label': f"DFF\\n{driven_sig}"
                    }
                    
                    # Register output
                    net_drivers[driven_sig] = node_id
                    
                    # Store connections for later
                    ff_connections[node_id] = d_input_nets
        
        # COMBINATIONAL LOGIC
        comb_connections = {}  # comb_id -> [list of input nets]
        for assign in self.assign_statements:
            lhs = assign['lhs']
            rhs = assign['rhs']
            
            instance_id += 1
            node_id = f"COMB_{instance_id}"
            
            # Determine gate type
            if '&' in rhs:
                cell_type = 'AND'
            elif '|' in rhs:
                cell_type = 'OR'
            elif '^' in rhs:
                cell_type = 'XOR'
            elif '~' in rhs:
                cell_type = 'INV'
            elif '?' in rhs:
                cell_type = 'MUX'
            elif '+' in rhs or '-' in rhs:
                cell_type = 'ARITH'
            elif '==' in rhs or '!=' in rhs:
                cell_type = 'CMP'
            else:
                cell_type = 'BUF'
            
            # Store COMB node
            nodes[node_id] = {
                'node_type': 'combinational',
                'cell_type': cell_type,
                'instance_name': node_id,
                'output_net': lhs,
                'expression': rhs[:50],
                'label': f"{cell_type}\\n→{lhs}"
            }
            
            # Register output
            net_drivers[lhs] = node_id
            
            # Extract and store input nets
            input_signals = re.findall(r'\b([a-zA-Z_]\w*)\b', rhs)
            comb_connections[node_id] = [s for s in input_signals 
                                         if s not in ['and', 'or', 'not', 'xor', 'nand', 'nor']]
        
        # ========== STEP 2: Build connection pairs [source, dest] ==========
        
        # FF input connections: [driver, FF]
        for ff_id, input_nets in ff_connections.items():
            print(f"   DEBUG: {ff_id} needs inputs: {input_nets}")
            for net in input_nets:
                if net in net_drivers:
                    print(f"      ✓ Connecting {net_drivers[net]} → {ff_id} via {net}")
                    connections.append({
                        'source': net_drivers[net],
                        'dest': ff_id,
                        'net_name': net,
                        'pin': 'D'
                    })
                else:
                    print(f"      ✗ Net '{net}' has no driver!")
        
        # COMB input connections: [driver, COMB]
        for comb_id, input_nets in comb_connections.items():
            for net in input_nets:
                if net in net_drivers:
                    connections.append({
                        'source': net_drivers[net],
                        'dest': comb_id,
                        'net_name': net
                    })
        
        # Output connections: [driver, PO]
        for output_net in output_nets:
            if output_net in net_drivers:
                connections.append({
                    'source': net_drivers[output_net],
                    'dest': f"PO_{output_net}",
                    'net_name': output_net
                })
        
        # ========== STEP 3: Create all nodes in graph ==========
        for node_id, node_data in nodes.items():
            self.dag_graph.add_node(node_id, **node_data)
        
        # ========== STEP 4: Create all edges from connection pairs ==========
        for conn in connections:
            edge_attrs = {k: v for k, v in conn.items() if k not in ['source', 'dest']}
            self.dag_graph.add_edge(conn['source'], conn['dest'], **edge_attrs)


        
        # Identify clock domains
        for clk in self.clock_signals:
            self.clock_domains[clk] = []
            for block in self.sequential_logic:
                if clk in block['sensitivity']:
                    self.clock_domains[clk].extend(block['driven_signals'])
        
        print(f"   Nodes: {self.dag_graph.number_of_nodes()}")
        print(f"   Edges: {self.dag_graph.number_of_edges()}")
        print(f"   Clock domains: {len(self.clock_domains)}")
        
    def generate_html(self, output_file="dag_visualization.html", layout="hierarchical", show_labels=True):
        """Generate the HTML visualization"""
        print(f"\n>> Generating visualization...")
        
        # Create PyVis network
        net = Network(height="900px", width="100%", directed=True, 
                     notebook=False, cdn_resources='in_line',
                     bgcolor="#ffffff", font_color="black")
        
        # Configure physics based on layout
        if layout == "hierarchical":
            net.set_options("""
            {
              "layout": {
                "hierarchical": {
                  "enabled": true,
                  "direction": "UD",
                  "sortMethod": "directed",
                  "levelSeparation": 150,
                  "nodeSpacing": 200
                }
              },
              "physics": {
                "enabled": true,
                "hierarchicalRepulsion": {
                  "nodeDistance": 120,
                  "centralGravity": 0.0
                },
                "solver": "hierarchicalRepulsion",
                "stabilization": {
                  "enabled": true,
                  "iterations": 30,
                  "updateInterval": 10,
                  "fit": true
                },
                "timestep": 0.5,
                "adaptiveTimestep": true
              }
            }
            """)
        elif layout == "force":
            net.set_options("""
            {
              "physics": {
                "enabled": true,
                "forceAtlas2Based": {
                  "gravitationalConstant": -50,
                  "centralGravity": 0.01,
                  "springLength": 100,
                  "springConstant": 0.08,
                  "damping": 0.95
                },
                "maxVelocity": 50,
                "minVelocity": 0.75,
                "solver": "forceAtlas2Based",
                "stabilization": {
                  "enabled": true,
                  "iterations": 50,
                  "updateInterval": 10,
                  "fit": true
                },
                "timestep": 0.5,
                "adaptiveTimestep": true
              }
            }
            """)
        
        # Color palette for clock domains
        clock_colors = {}
        color_palette = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', 
                        '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788']
        for idx, clk in enumerate(self.clock_domains.keys()):
            clock_colors[clk] = color_palette[idx % len(color_palette)]
        
        # Scale node sizes for large graphs
        num_nodes = self.dag_graph.number_of_nodes()
        size_scale = 1.0
        if num_nodes > 100:
            size_scale = 0.7
        if num_nodes > 500:
            size_scale = 0.5
        if num_nodes > 1000:
            size_scale = 0.3
        
        # Render nodes as netlist cells
        for node in self.dag_graph.nodes():
            node_data = self.dag_graph.nodes[node]
            node_type = node_data.get('node_type', 'unknown')
            cell_type = node_data.get('cell_type', '')
            label = node_data.get('label', node)
            
            # Style based on netlist element type (like a schematic view)
            if node_type == 'primary_input':
                # Input pads - Blue triangles
                color = '#3498DB'
                shape = 'triangleDown'
                size = int(40 * size_scale)
                border_width = 3
                title = f"📥 PRIMARY INPUT\\n{node_data.get('port_name', '')}"
                group = 'inputs'
                
            elif node_type == 'primary_output':
                # Output pads - Red triangles
                color = '#E74C3C'
                shape = 'triangle'
                size = int(40 * size_scale)
                border_width = 3
                title = f"📤 PRIMARY OUTPUT\\n{node_data.get('port_name', '')}"
                group = 'outputs'
                
            elif node_type == 'flip_flop':
                # Sequential cells - Green boxes
                color = '#27AE60'
                shape = 'box'
                size = int(50 * size_scale)
                border_width = 4
                output_net = node_data.get('output_net', '')
                clock_net = node_data.get('clock_net', '')
                title = f"⏱️ D FLIP-FLOP\\n{node}\\nQ: {output_net}\\nCLK: {clock_net}"
                group = 'sequential'
                
            elif node_type == 'combinational':
                # Combinational gates - Color by gate type
                cell = node_data.get('cell_type', 'LOGIC')
                output_net = node_data.get('output_net', '')
                expr = node_data.get('expression', '')
                
                gate_colors = {
                    'AND': '#F39C12',    # Orange
                    'OR': '#E67E22',     # Dark orange  
                    'XOR': '#9B59B6',    # Purple
                    'INV': '#34495E',    # Dark gray
                    'MUX': '#16A085',    # Teal
                    'BUF': '#95A5A6',    # Light gray
                    'ARITH': '#D35400',  # Red-orange
                    'CMP': '#8E44AD'     # Dark purple
                }
                color = gate_colors.get(cell, '#F39C12')
                shape = 'ellipse'
                size = int(45 * size_scale)
                border_width = 2
                title = f"⚡ {cell} GATE\\n{node}\\nY: {output_net}\\n{expr}"
                group = 'combinational'
                
            else:
                color = '#95A5A6'
                shape = 'diamond'
                size = int(30 * size_scale)
                border_width = 2
                title = node
                group = None
            
            # Add styled node
            if show_labels:
                display_label = label
            else:
                display_label = ""
            
            net.add_node(node, 
                        label=display_label,
                        color={'border': color, 'background': f"{color}40", 
                               'highlight': {'border': color, 'background': f"{color}80"}},
                        shape=shape,
                        size=size,
                        borderWidth=border_width,
                        title=title,
                        font={'size': int(14 * size_scale), 'face': 'monospace', 'bold': True},
                        group=group)
        
        # Add edges (nets/wires in netlist)
        for edge in self.dag_graph.edges(data=True):
            src, dst, edge_data = edge
            net_name = edge_data.get('net_name', '')
            pin = edge_data.get('pin', '')
            
            # Get node types for styling
            src_node = self.dag_graph.nodes[src]
            dst_node = self.dag_graph.nodes[dst]
            
            src_type = src_node.get('node_type', 'unknown')
            dst_type = dst_node.get('node_type', 'unknown')
            
            # Wire styling based on connection type (like schematic)
            if dst_type == 'flip_flop':
                # Net feeding flip-flop input - solid blue
                color = '#3498DB'
                width = 2.5
                dashes = False
                arrows = 'to'
                title = f"Net: {net_name}\\nTo: {pin} pin"
            elif dst_type == 'combinational':
                # Net feeding combinational gate - dashed orange
                color = '#E67E22'
                width = 1.5
                dashes = True
                arrows = 'to'
                title = f"Net: {net_name}"
            elif dst_type == 'primary_output':
                # Net to output port - solid red
                color = '#E74C3C'
                width = 2.5
                dashes = False
                arrows = 'to'
                title = f"Output Net: {net_name}"
            else:
                # Default net - gray
                color = '#95A5A6'
                width = 1
                dashes = False
                arrows = 'to'
                title = f"Net: {net_name}"
            
            # Wire label (net name)
            if show_labels and net_name:
                edge_label = net_name
            else:
                edge_label = ""
            
            net.add_edge(src, dst,
                        color={'color': color, 'highlight': color},
                        width=width,
                        dashes=dashes,
                        arrows=arrows,
                        title=title,
                        label=edge_label,
                        font={'size': 10, 'align': 'middle', 'background': 'white'})
        
        # Generate HTML content
        print(f"   Saving to: {output_file}")
        
        html_content = None
        
        # Try to save directly first
        try:
            net.save_graph(output_file)
            print(f"   Initial save successful")
            # Read it back
            with open(output_file, 'r', encoding='utf-8', errors='replace') as f:
                html_content = f.read()
        except Exception as e:
            print(f"   Direct save failed: {e}")
            # Try generating HTML directly
            try:
                print(f"   Generating HTML directly from PyVis")
                html_content = net.generate_html()
            except Exception as e2:
                print(f"   Generate HTML failed: {e2}")
                raise Exception(f"Failed to generate HTML: {e2}")
        
        if not html_content or len(html_content) < 100:
            raise Exception("Generated HTML is empty or too short")
        
        # Add title and info
        title_html = f"""
<div style="position: fixed; top: 10px; left: 10px; z-index: 1000; background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); max-width: 300px;">
    <h3 style="margin: 0 0 10px 0; color: #333;">Netlist Visualization</h3>
    <p style="margin: 0; font-size: 14px; color: #666;">
        <strong>Module:</strong> {self.module_name}<br>
        <strong>Instances:</strong> {num_nodes}<br>
        <strong>Nets:</strong> {self.dag_graph.number_of_edges()}<br>
        <strong>Clock Domains:</strong> {len(self.clock_domains)}
    </p>
</div>
"""
        
        loading_bar_css = """
<style>
#loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.95);
    z-index: 9999;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    font-family: Arial, sans-serif;
}
#loading-text {
    font-size: 24px;
    margin-bottom: 20px;
    color: #333;
}
#loading-bar-container {
    width: 60%;
    height: 30px;
    background: #e0e0e0;
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
#loading-bar {
    width: 0%;
    height: 100%;
    background: linear-gradient(90deg, #4ECDC4, #45B7D1);
    transition: width 0.3s ease;
}
#loading-percentage {
    position: absolute;
    color: #333;
    font-size: 18px;
    font-weight: bold;
    margin-top: 80px;
}
#loading-time-info {
    position: absolute;
    color: #666;
    font-size: 14px;
    margin-top: 120px;
    font-family: monospace;
}
</style>
"""
        
        loading_bar_html = """
<div id="loading-overlay">
    <div id="loading-text">🔄 Loading DAG Visualization...</div>
    <div id="loading-bar-container">
        <div id="loading-bar"></div>
    </div>
    <div id="loading-percentage">0%</div>
    <div id="loading-time-info">⏱️ Elapsed: 0.0s | Estimated: calculating...</div>
</div>
"""
        
        control_panel_html = """
<div id="control-panel" style="position: fixed; top: 10px; right: 10px; z-index: 1000; background: white; padding: 10px; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); display: none;">
    <button id="freeze-btn" onclick="togglePhysics()" style="padding: 8px 15px; background: #4ECDC4; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
        ❄️ Freeze Layout
    </button>
    <button id="reset-btn" onclick="resetZoom()" style="padding: 8px 15px; background: #45B7D1; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; margin-left: 5px;">
        🔍 Reset Zoom
    </button>
</div>
"""
        
        loading_bar_js = """
<script type="text/javascript">
var loadingOverlay = document.getElementById('loading-overlay');
var loadingBar = document.getElementById('loading-bar');
var loadingPercentage = document.getElementById('loading-percentage');
var loadingTimeInfo = document.getElementById('loading-time-info');
var controlPanel = document.getElementById('control-panel');
var freezeBtn = document.getElementById('freeze-btn');
var startTime = Date.now();
var physicsEnabled = true;
var lastProgress = 0;
var lastUpdateTime = Date.now();

loadingBar.style.width = '5%';
loadingPercentage.textContent = '5%';

// Update time display every 100ms
var timeUpdateInterval = setInterval(function() {
    var elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    var currentProgress = parseInt(loadingBar.style.width);
    
    // Calculate estimated time remaining
    var estimatedTotal = 'calculating...';
    if (currentProgress > 10 && currentProgress < 100) {
        var progressRate = currentProgress / (Date.now() - startTime);
        var remainingProgress = 100 - currentProgress;
        var estimatedRemaining = (remainingProgress / progressRate / 1000).toFixed(1);
        estimatedTotal = estimatedRemaining + 's remaining';
    } else if (currentProgress >= 100) {
        estimatedTotal = 'complete!';
        clearInterval(timeUpdateInterval);
    }
    
    loadingTimeInfo.textContent = '⏱️ Elapsed: ' + elapsed + 's | ' + estimatedTotal;
}, 100);

function togglePhysics() {
    if (typeof network !== 'undefined') {
        physicsEnabled = !physicsEnabled;
        network.setOptions({physics: {enabled: physicsEnabled}});
        freezeBtn.textContent = physicsEnabled ? '❄️ Freeze Layout' : '▶️ Enable Physics';
        freezeBtn.style.background = physicsEnabled ? '#4ECDC4' : '#E74C3C';
    }
}

function resetZoom() {
    if (typeof network !== 'undefined') {
        network.fit();
    }
}

setTimeout(function() {
    if (typeof network !== 'undefined') {
        network.on("stabilizationProgress", function(params) {
            var progress = Math.round((params.iterations / params.total) * 100);
            loadingBar.style.width = progress + '%';
            loadingPercentage.textContent = progress + '%';
            lastProgress = progress;
            lastUpdateTime = Date.now();
        });
        
        network.on("stabilizationIterationsDone", function() {
            loadingBar.style.width = '100%';
            loadingPercentage.textContent = '100%';
            var elapsedTime = ((Date.now() - startTime) / 1000).toFixed(2);
            loadingTimeInfo.textContent = '⏱️ Total time: ' + elapsedTime + 's';
            
            setTimeout(function() {
                clearInterval(timeUpdateInterval);
                loadingOverlay.style.display = 'none';
                controlPanel.style.display = 'block';
                console.log('Visualization loaded in ' + elapsedTime + ' seconds');
                setTimeout(function() {
                    if (physicsEnabled) {
                        togglePhysics();
                    }
                }, 2000);
            }, 500);
        });
        
        setTimeout(function() {
            if (loadingOverlay.style.display !== 'none') {
                clearInterval(timeUpdateInterval);
                loadingOverlay.style.display = 'none';
                controlPanel.style.display = 'block';
            }
        }, 30000);
    }
}, 100);
</script>
"""
        
        # Inject everything
        html_content = html_content.replace('</head>', loading_bar_css + '\n</head>')
        html_content = html_content.replace('<body>', '<body>\n' + loading_bar_html + title_html + control_panel_html)
        html_content = html_content.replace('</body>', loading_bar_js + '\n</body>')
        
        # Write back
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n>> Visualization generated successfully!")
        print(f">> Open {output_file} in your browser to view")
        

def main():
    parser = argparse.ArgumentParser(description='Generate DAG visualization from Verilog')
    parser.add_argument('verilog_file', help='Path to Verilog file')
    parser.add_argument('--layout', choices=['hierarchical', 'force'], default='hierarchical',
                       help='Layout algorithm (default: hierarchical)')
    parser.add_argument('--output', '-o', default='dag_visualization.html',
                       help='Output HTML file (default: dag_visualization.html)')
    parser.add_argument('--no-labels', action='store_true',
                       help='Hide signal names on nodes')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.verilog_file):
        print(f"❌ Error: File not found: {args.verilog_file}")
        sys.exit(1)
    
    print("=" * 60)
    print("  RTL DAG Visualization Generator")
    print("=" * 60)
    
    generator = VerilogDAGGenerator(args.verilog_file)
    generator.parse_verilog()
    generator.build_dag()
    generator.generate_html(args.output, args.layout, show_labels=not args.no_labels)
    
    print("=" * 60)
    print(">> Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
