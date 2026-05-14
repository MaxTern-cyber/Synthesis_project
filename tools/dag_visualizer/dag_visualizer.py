"""
STANDALONE DAG VISUALIZER - Netlist to DAG HTML Generator
Generates interactive 3D DAG visualizations from Verilog netlists
"""

import streamlit as st
import networkx as nx
import re
from pyvis.network import Network
from datetime import datetime
import os
from pathlib import Path
import sys

# Parse command-line arguments for netlist file
netlist_arg = None
if len(sys.argv) > 1:
    netlist_arg = sys.argv[1]

st.set_page_config(
    page_title="DAG Visualizer",
    page_icon="🌐",
    layout="wide"
)

st.title("🌐 Interactive DAG Visualizer")
st.caption("Generate interactive 3D DAG visualizations from Verilog netlists")

# Session state
if 'dag' not in st.session_state:
    st.session_state.dag = None
if 'stats' not in st.session_state:
    st.session_state.stats = {}
if 'auto_loaded' not in st.session_state:
    st.session_state.auto_loaded = False

# Auto-load from command-line argument
if not st.session_state.auto_loaded and netlist_arg:
    try:
        netlist_path = Path(netlist_arg)
        if netlist_path.exists():
            with open(netlist_path, 'r') as f:
                content = f.read()
            visualizer = DAGVisualizer(content)
            visualizer.parse()
            st.session_state.dag = visualizer
            st.session_state.stats = {
                'gates': len(visualizer.gates),
                'nodes': visualizer.dag.number_of_nodes(),
                'edges': visualizer.dag.number_of_edges()
            }
            st.session_state.auto_loaded = True
            st.toast(f"✅ Loaded {netlist_path.name}!", icon="✅")
        else:
            st.error(f"❌ File not found: {netlist_arg}")
    except Exception as e:
        st.error(f"Auto-load error: {e}")
    st.session_state.auto_loaded = True

class DAGVisualizer:
    def __init__(self, content):
        self.content = content
        self.dag = nx.DiGraph()
        self.gates = {}
        self.signals = {}
        
    def parse(self):
        """Parse netlist and build DAG"""
        # Remove comments
        clean_content = re.sub(r'//.*?\n', '\n', self.content)
        clean_content = re.sub(r'/\*.*?\*/', '', clean_content, flags=re.DOTALL)
        
        # Extract gates
        gate_pattern = r'(\w+)\s+(\w+)\s*\((.*?)\);'
        
        count = 0
        max_gates = 10000
        
        for match in re.finditer(gate_pattern, clean_content, re.DOTALL):
            if count >= max_gates:
                break
                
            gate_type = match.group(1)
            instance = match.group(2)
            connections = match.group(3)
            
            # Skip Verilog keywords
            if gate_type.lower() in ['input', 'output', 'wire', 'reg', 'parameter', 'assign', 'module']:
                continue
            
            conn_dict = self._parse_connections(connections)
            
            self.gates[instance] = {
                'type': gate_type,
                'connections': conn_dict
            }
            
            # Add node to DAG
            self.dag.add_node(instance, node_type='gate', gate_type=gate_type, label=f"{instance}\\n({gate_type})")
            count += 1
        
        # Build edges
        signal_drivers = {}
        signal_readers = {}
        
        for gate_name, gate_info in self.gates.items():
            for port, signal in gate_info['connections'].items():
                # Output ports
                if port in ['Y', 'Q', 'QN', 'CO', 'S', 'SO', 'Z', 'OUT']:
                    signal_drivers[signal] = gate_name
                else:
                    if signal not in signal_readers:
                        signal_readers[signal] = []
                    signal_readers[signal].append(gate_name)
        
        # Create edges
        for signal, readers in signal_readers.items():
            if signal in signal_drivers:
                driver = signal_drivers[signal]
                for reader in readers:
                    self.dag.add_edge(driver, reader, signal=signal, label=signal)
        
        st.success(f"✅ Parsed {len(self.gates)} gates, {self.dag.number_of_edges()} connections")
    
    def _parse_connections(self, conn_str):
        """Parse gate connections"""
        connections = {}
        port_pattern = r'\.(\w+)\s*\(([^)]+)\)'
        for port, signal in re.findall(port_pattern, conn_str):
            signal = signal.strip()
            connections[port] = signal
        return connections
    
    def export_html(self, filename, physics_enabled=True):
        """Export DAG to interactive HTML"""
        net = Network(height="800px", width="100%", directed=True, notebook=False)
        
        # Configure physics
        if physics_enabled:
            net.barnes_hut(
                gravity=-8000,
                central_gravity=0.3,
                spring_length=100,
                spring_strength=0.001,
                damping=0.09
            )
        else:
            net.toggle_physics(False)
        
        # Add nodes
        for node in self.dag.nodes():
            gate_type = self.dag.nodes[node].get('gate_type', 'GATE')
            
            # Color by gate type
            color = self._get_gate_color(gate_type)
            
            net.add_node(
                node,
                label=f"{node}\n{gate_type}",
                title=f"Gate: {node}<br>Type: {gate_type}",
                color=color,
                size=15
            )
        
        # Add edges
        for source, target, data in self.dag.edges(data=True):
            signal = data.get('signal', '')
            net.add_edge(source, target, title=f"Signal: {signal}", color='#888888')
        
        # Save
        net.write_html(filename)
        return filename
    
    def _get_gate_color(self, gate_type):
        """Assign color based on gate type"""
        gate_type = gate_type.upper()
        
        if 'DFF' in gate_type or 'REG' in gate_type:
            return '#4ECDC4'  # Teal for flip-flops
        elif 'NAND' in gate_type:
            return '#FF6B6B'  # Red
        elif 'NOR' in gate_type:
            return '#FFA07A'  # Orange
        elif 'AND' in gate_type:
            return '#45B7D1'  # Blue
        elif 'OR' in gate_type:
            return '#F7DC6F'  # Yellow
        elif 'XOR' in gate_type or 'XNOR' in gate_type:
            return '#BB8FCE'  # Purple
        elif 'INV' in gate_type or 'NOT' in gate_type:
            return '#98D8C8'  # Mint
        elif 'MUX' in gate_type:
            return '#F8B88B'  # Peach
        else:
            return '#A8E6CF'  # Light green (default)

# Dynamic file loading - skip if auto-loaded from command-line
if not (netlist_arg and st.session_state.dag):
    st.markdown("## 📂 Load Netlist File")

    tab_upload, tab_workspace = st.tabs(["📤 Upload File", "📁 From Workspace"])

    content = None

    with tab_upload:
        st.markdown("**Drag & drop or browse for your Verilog netlist**")
        uploaded_file = st.file_uploader(
            "Choose a .v/.sv file",
            type=['v', 'sv', 'verilog'],
            help="Upload synthesized gate-level netlist for DAG visualization"
        )
        
        if uploaded_file:
            content = uploaded_file.read().decode('utf-8')
            st.success(f"✅ Loaded {uploaded_file.name} ({len(content):,} characters)")

    with tab_workspace:
        st.markdown("**Load from workspace directory**")
        col1, col2 = st.columns([3, 1])
        with col1:
            workspace_file = st.text_input(
                "File path:",
                value=netlist_arg if netlist_arg else "../file.v",
                placeholder="e.g., ../file.v"
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            use_workspace = st.button("📂 Load", type="primary", use_container_width=True)
        
        if use_workspace and workspace_file:
            try:
                with open(workspace_file, 'r') as f:
                    content = f.read()
                st.success(f"✅ Loaded {workspace_file} ({len(content):,} characters)")
            except Exception as e:
                st.error(f"❌ Error loading file: {e}")
                st.info("💡 Make sure the file path is correct")

    if content:
        # Parse button
        if st.button("🔄 Parse & Build DAG", type="primary"):
            with st.spinner("Parsing netlist and building DAG..."):
                visualizer = DAGVisualizer(content)
                visualizer.parse()
                st.session_state.dag = visualizer
                st.session_state.stats = {
                    'gates': len(visualizer.gates),
                    'nodes': visualizer.dag.number_of_nodes(),
                    'edges': visualizer.dag.number_of_edges()
                }
else:
    # File was auto-loaded - just show status
    st.success(f"✅ {Path(netlist_arg).name} loaded and parsed!")
    col1, col2, col3 = st.columns(3)
    col1.metric("Gates", f"{st.session_state.stats['gates']:,}")
    col2.metric("DAG Nodes", f"{st.session_state.stats['nodes']:,}")
    col3.metric("DAG Edges", f"{st.session_state.stats['edges']:,}")
    st.markdown("---")

# If DAG is built, show visualization options
if st.session_state.dag:

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    ### DAG Visualizer
    
    Generates interactive 3D visualizations of Verilog netlists as Directed Acyclic Graphs (DAGs).
    
    **Features:**
    - Interactive node dragging
    - Pan and zoom
    - Color-coded by gate type
    - Physics simulation
    - Standalone HTML output
    
    **Usage:**
    1. Load netlist file
    2. Parse & build DAG
    3. Generate HTML
    4. Open in browser
    """)
    
    if st.session_state.dag:
        st.success("✅ DAG Ready")
        if st.button("🗑️ Clear"):
            st.session_state.dag = None
            st.session_state.stats = {}
            st.rerun()
