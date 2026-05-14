"""
LOCAL NETLIST ANALYZER - NO API REQUIRED
Combines DAG visualization with intelligent rule-based analysis
"""

import streamlit as st
import networkx as nx
import re
from pyvis.network import Network
import plotly.graph_objects as go
import tempfile
import os
from pathlib import Path
import pandas as pd
import sys

# Parse command-line arguments for netlist file
netlist_arg = None
if len(sys.argv) > 1:
    netlist_arg = sys.argv[1]

st.set_page_config(
    page_title="Local EDA Netlist Analyzer",
    page_icon="🔌",
    layout="wide"
)

st.title("🔌 Local EDA Netlist Analyzer")
st.caption("⚡ No API Required - Fully Local Analysis with DAG HTML Export")

# ==================== NETLIST PARSER ====================
class NetlistAnalyzer:
    def __init__(self, content):
        self.content = content
        self.dag = nx.DiGraph()
        self.modules = {}
        self.signals = {}
        self.gates = {}
        self.stats = {}
        
    def parse(self):
        """Parse the netlist and build data structures"""
        # Full parse with gates and signals for signal tracing
        self._full_parse()
    
    def _quick_parse(self):
        """Fast initial parse for statistics only"""
        # Quick module count
        self.stats['modules'] = len(re.findall(r'\bmodule\s+\w+', self.content))
        self.stats['module_names'] = re.findall(r'module\s+(\w+)', self.content)[:10]
        
        # Quick signal/wire count
        self.stats['signals'] = len(re.findall(r'\bwire\s+', self.content))
        
        # Quick gate count (instances)
        lines = self.content.split('\n')
        gate_count = 0
        gate_types = {}
        
        for line in lines:
            # Simple pattern for gate instances: GATETYPE instancename (
            if '(' in line and not line.strip().startswith('//'):
                match = re.match(r'\s*(\w+)\s+(\w+)\s*\(', line)
                if match:
                    gate_type = match.group(1)
                    if gate_type not in ['module', 'input', 'output', 'wire', 'reg']:
                        gate_count += 1
                        gate_types[gate_type] = gate_types.get(gate_type, 0) + 1
        
        self.stats['gates'] = gate_count
        self.stats['gate_types'] = gate_types
        self.stats['total_lines'] = len(lines)
        self.stats['dag_nodes'] = 0
        self.stats['dag_edges'] = 0
        self.stats['unconnected'] = []
    
    def _full_parse(self):
        """Full parse with DAG building (called on-demand)"""
        # Remove comments
        clean_content = re.sub(r'//.*?\n', '\n', self.content)
        clean_content = re.sub(r'/\*.*?\*/', '', clean_content, flags=re.DOTALL)
        
        # Initialize stats if not set
        if 'total_lines' not in self.stats:
            lines = self.content.split('\n')
            self.stats['total_lines'] = len(lines)
        
        # Extract modules
        module_pattern = r'module\s+(\w+)\s*\((.*?)\);(.*?)endmodule'
        modules = re.finditer(module_pattern, clean_content, re.DOTALL)
        
        for match in modules:
            module_name = match.group(1)
            ports = match.group(2)
            body = match.group(3)
            
            self.modules[module_name] = {
                'ports': self._parse_ports(ports),
                'body': body
            }
            
            # Add module as node
            self.dag.add_node(module_name, node_type='module', label=module_name)
            
        # Find signals (sample only for large files)
        if len(clean_content) > 100000:  # Large file
            self._extract_signals(clean_content[:100000])  # Sample first 100KB
        else:
            self._extract_signals(clean_content)
        
        # Find gate instances (limited)
        self._extract_gates(clean_content)
        
        # Build DAG connectivity
        self._build_dag()
        
        # Update stats after full parse
        self.stats['modules'] = len(self.modules)
        self.stats['module_names'] = list(self.modules.keys())[:10]
        self.stats['signals'] = len(self.signals)
        self.stats['gates'] = len(self.gates)
        self.stats['dag_nodes'] = self.dag.number_of_nodes()
        self.stats['dag_edges'] = self.dag.number_of_edges()
        self.stats['gate_types'] = self._count_gate_types()
        self.stats['unconnected'] = self._find_unconnected()
        
        print(f"Full parse complete: {self.stats['gates']} gates, {self.stats['signals']} signals")
        
    def _parse_ports(self, ports_str):
        """Parse port declarations"""
        ports = {'input': [], 'output': [], 'inout': []}
        
        # Find inputs
        inputs = re.findall(r'input\s+(?:\[.*?\])?\s*([\w,\s]+)', ports_str)
        for inp in inputs:
            ports['input'].extend([p.strip() for p in inp.split(',')])
        
        # Find outputs
        outputs = re.findall(r'output\s+(?:\[.*?\])?\s*([\w,\s]+)', ports_str)
        for out in outputs:
            ports['output'].extend([p.strip() for p in out.split(',')])
            
        return ports
    
    def _extract_signals(self, content):
        """Extract wire and signal declarations"""
        # Find wire declarations
        wire_pattern = r'wire\s+(?:\[(\d+):(\d+)\])?\s*([\w,\s]+);'
        for match in re.finditer(wire_pattern, content):
            width_hi = match.group(1)
            width_lo = match.group(2)
            signals = match.group(3)
            
            width = 1
            if width_hi and width_lo:
                width = int(width_hi) - int(width_lo) + 1
            
            for sig in signals.split(','):
                sig = sig.strip()
                self.signals[sig] = {
                    'type': 'wire',
                    'width': width,
                    'drivers': [],
                    'readers': []
                }
    
    def _extract_gates(self, content):
        """Extract gate instances (limited for performance)"""
        # Pattern: GATE_TYPE instance_name (.PORT(signal), ...);
        gate_pattern = r'(\w+)\s+(\w+)\s*\((.*?)\);'
        
        count = 0
        max_gates = 10000  # Increased limit
        
        for match in re.finditer(gate_pattern, content, re.DOTALL):
            if count >= max_gates:
                break
                
            gate_type = match.group(1)
            instance = match.group(2)
            connections = match.group(3)
            
            # Skip module instances, focus on gates
            if gate_type in self.modules:
                continue
            
            # Skip common Verilog keywords
            if gate_type.lower() in ['input', 'output', 'wire', 'reg', 'parameter', 'assign']:
                continue
            
            conn_dict = self._parse_connections(connections)
            
            self.gates[instance] = {
                'type': gate_type,
                'connections': conn_dict
            }
            
            # Add gate as node
            self.dag.add_node(instance, node_type='gate', gate_type=gate_type, label=f"{instance}\\n({gate_type})")
            count += 1
        
        print(f"Extracted {len(self.gates)} gates from netlist")
    
    def _parse_connections(self, conn_str):
        """Parse gate connections"""
        connections = {}
        port_pattern = r'\.(\w+)\s*\(([^)]+)\)'
        for port, signal in re.findall(port_pattern, conn_str):
            signal = signal.strip()
            connections[port] = signal
        return connections
    
    def _build_dag(self):
        """Build DAG from gate connectivity"""
        # Track signal drivers and readers
        signal_drivers = {}
        signal_readers = {}
        
        for gate_name, gate_info in self.gates.items():
            for port, signal in gate_info['connections'].items():
                # Common output ports
                if port in ['Y', 'Q', 'QN', 'CO', 'S', 'SO', 'Z', 'OUT']:
                    signal_drivers[signal] = gate_name
                else:
                    # Input port
                    if signal not in signal_readers:
                        signal_readers[signal] = []
                    signal_readers[signal].append(gate_name)
        
        # Create edges
        for signal, readers in signal_readers.items():
            if signal in signal_drivers:
                driver = signal_drivers[signal]
                for reader in readers:
                    self.dag.add_edge(driver, reader, signal=signal, label=signal)
    
    def _calculate_stats(self):
        """Calculate netlist statistics (if not already set)"""
        if 'total_lines' not in self.stats:
            self.stats = {
                'total_lines': len(self.content.split('\n')),
                'modules': len(self.modules),
                'module_names': list(self.modules.keys()),
                'signals': len(self.signals),
                'gates': len(self.gates),
                'dag_nodes': self.dag.number_of_nodes(),
                'dag_edges': self.dag.number_of_edges(),
                'unconnected': self._find_unconnected(),
                'gate_types': self._count_gate_types()
            }
    
    def _find_unconnected(self):
        """Find unconnected signals"""
        unconnected = []
        for sig_name in self.signals.keys():
            if 'UNCONNECTED' in sig_name.upper():
                unconnected.append(sig_name)
        return unconnected
    
    def _count_gate_types(self):
        """Count gates by type"""
        gate_types = {}
        for gate_info in self.gates.values():
            gt = gate_info['type']
            gate_types[gt] = gate_types.get(gt, 0) + 1
        return gate_types
    
    def get_critical_paths(self, top_n=10):
        """Find longest paths with timing estimation"""
        try:
            # Gate delay estimates (nanoseconds)
            gate_delays = {
                'NAND': 0.05, 'NOR': 0.06, 'AND': 0.06, 'OR': 0.06,
                'INV': 0.03, 'BUF': 0.04, 'XOR': 0.10, 'XNOR': 0.10,
                'MUX': 0.12, 'DFF': 0.15, 'LATCH': 0.10,
                'ADDER': 0.20, 'MULT': 0.50
            }
            
            # Find sources and sinks
            sources = [n for n in self.dag.nodes() if self.dag.in_degree(n) == 0]
            sinks = [n for n in self.dag.nodes() if self.dag.out_degree(n) == 0]
            
            paths = []
            for source in sources[:20]:  # Increased limit
                for sink in sinks[:20]:
                    try:
                        for path in nx.all_simple_paths(self.dag, source, sink, cutoff=50):
                            # Calculate delay
                            delay = 0
                            for gate in path:
                                if gate in self.gates:
                                    gate_type = self.gates[gate]['type']
                                    # Match partial gate names
                                    for key, val in gate_delays.items():
                                        if key in gate_type.upper():
                                            delay += val
                                            break
                                    else:
                                        delay += 0.05  # Default delay
                            
                            paths.append({
                                'length': len(path),
                                'delay_ns': round(delay, 3),
                                'path': path,
                                'start': source,
                                'end': sink
                            })
                    except:
                        pass
            
            # Sort by delay (most critical)
            paths.sort(reverse=True, key=lambda x: x['delay_ns'])
            return paths[:top_n]
        except Exception as e:
            print(f"Critical path error: {e}")
            return []
    
    def detect_combinational_loops(self):
        """Detect combinational feedback loops (critical design error)"""
        try:
            loops = []
            
            # Find strongly connected components (cycles)
            strongly_connected = list(nx.strongly_connected_components(self.dag))
            
            for component in strongly_connected:
                if len(component) > 1:  # True cycle
                    component_list = list(component)
                    
                    # Get the subgraph for this cycle
                    cycle_graph = self.dag.subgraph(component_list)
                    
                    # Find an actual cycle path
                    try:
                        cycle = nx.find_cycle(cycle_graph)
                        cycle_nodes = [edge[0] for edge in cycle] + [cycle[-1][1]]
                        
                        # Check if it's truly combinational (no registers)
                        has_register = False
                        gate_types = []
                        
                        for node in cycle_nodes:
                            if node in self.gates:
                                gate_type = self.gates[node]['type'].upper()
                                gate_types.append(self.gates[node]['type'])
                                
                                if any(reg in gate_type for reg in ['DFF', 'LATCH', 'REG', 'FLOP']):
                                    has_register = True
                                    break
                        
                        if not has_register:
                            # This is a combinational loop - CRITICAL ERROR
                            severity = 'CRITICAL'
                            
                            # Analyze loop characteristics
                            loop_info = {
                                'severity': severity,
                                'nodes': cycle_nodes,
                                'size': len(cycle_nodes),
                                'gate_types': gate_types,
                                'description': f'Combinational loop of {len(cycle_nodes)} gates',
                                'path': ' → '.join(cycle_nodes[:10]) + ('...' if len(cycle_nodes) > 10 else ''),
                                'impact': 'Synthesis failure, unpredictable behavior, timing violations'
                            }
                            
                            # Suggest fixes
                            suggestions = []
                            
                            # Find gates in loop that could be register insertion points
                            for i, node in enumerate(cycle_nodes[:-1]):
                                if node in self.gates:
                                    out_deg = self.dag.out_degree(node)
                                    if out_deg == 1:  # Simple point to break
                                        suggestions.append({
                                            'type': 'Insert Register',
                                            'location': f'After {node}',
                                            'reason': 'Single fanout point - easy to break loop'
                                        })
                            
                            if not suggestions:
                                suggestions.append({
                                    'type': 'Insert Register',
                                    'location': f'After {cycle_nodes[0]}',
                                    'reason': 'Break loop at first gate'
                                })
                            
                            loop_info['suggestions'] = suggestions[:3]  # Top 3 suggestions
                            loops.append(loop_info)
                    
                    except nx.NetworkXNoCycle:
                        pass
            
            return loops
            
        except Exception as e:
            print(f"Loop detection error: {e}")
            return []
    
    def analyze_clock_domains(self):
        """Identify and analyze clock domains in the design"""
        try:
            clock_domains = {}
            
            # Smart clock detection: only consider signals that are:
            # 1. Start with 'clk' or 'clock' (not just contain it)
            # 2. Are actually connected to register clock ports
            actual_clock_signals = set()
            
            # First pass: find what signals are actually connected to clock ports
            for gate_name, gate_info in self.gates.items():
                gate_type = gate_info['type'].upper()
                if any(reg in gate_type for reg in ['DFF', 'LATCH', 'REG', 'FLOP']):
                    for port, signal in gate_info['connections'].items():
                        if 'CLK' in port.upper() or 'CK' in port.upper():
                            actual_clock_signals.add(signal)
            
            # Filter to only primary clocks (start with clk/clock, not internal nodes)
            primary_clocks = set()
            for sig in actual_clock_signals:
                sig_lower = sig.lower()
                # Must start with clk/clock or be a single word clock signal
                if (sig_lower.startswith('clk') or 
                    sig_lower.startswith('clock') or
                    sig_lower == 'clk' or 
                    sig_lower == 'clock'):
                    primary_clocks.add(sig)
            
            # If no primary clocks found, use all actual clock signals
            if not primary_clocks:
                primary_clocks = actual_clock_signals
            
            # Find registers and their clock signals
            registers = []
            for gate_name, gate_info in self.gates.items():
                gate_type = gate_info['type'].upper()
                if any(reg in gate_type for reg in ['DFF', 'LATCH', 'REG', 'FLOP']):
                    # Find clock connection
                    clock_port = None
                    for port, signal in gate_info['connections'].items():
                        if 'CLK' in port.upper() or 'CK' in port.upper():
                            clock_port = signal
                            break
                    
                    # Only track if it's a primary clock
                    if clock_port and clock_port in primary_clocks:
                        if clock_port not in clock_domains:
                            clock_domains[clock_port] = {
                                'registers': [],
                                'all_nodes': [],  # Track all nodes in domain
                                'count': 0
                            }
                        clock_domains[clock_port]['registers'].append(gate_name)
                        clock_domains[clock_port]['all_nodes'].append(gate_name)
                        clock_domains[clock_port]['count'] += 1
            
            # Propagate domain info to combinational logic (if DAG is built)
            if self.dag.number_of_nodes() > 0:
                for clock, info in clock_domains.items():
                    visited = set(info['all_nodes'])
                    queue = list(info['registers'])
                    
                    while queue:
                        node = queue.pop(0)
                        
                        # Add predecessors (combinational logic feeding registers)
                        for pred in self.dag.predecessors(node):
                            if pred not in visited:
                                gate_type = self.gates.get(pred, {}).get('type', '').upper()
                                # Only add combinational gates
                                if not any(reg in gate_type for reg in ['DFF', 'LATCH', 'REG', 'FLOP']):
                                    visited.add(pred)
                                    info['all_nodes'].append(pred)
                                    queue.append(pred)
                        
                        # Add successors (logic driven by registers)
                        for succ in self.dag.successors(node):
                            if succ not in visited:
                                gate_type = self.gates.get(succ, {}).get('type', '').upper()
                                if not any(reg in gate_type for reg in ['DFF', 'LATCH', 'REG', 'FLOP']):
                                    visited.add(succ)
                                    info['all_nodes'].append(succ)
                                    queue.append(succ)
            
            # Analyze each domain
            domain_analysis = []
            for clock, info in clock_domains.items():
                analysis = {
                    'clock': clock,
                    'register_count': info['count'],
                    'total_nodes': len(info['all_nodes']),
                    'registers': info['registers'],
                    'all_nodes': info['all_nodes'],
                    'sample_registers': info['registers'][:10],
                    'percentage': (info['count'] / len(self.gates) * 100) if self.gates else 0
                }
                domain_analysis.append(analysis)
            
            # Sort by register count
            domain_analysis.sort(key=lambda x: x['register_count'], reverse=True)
            
            return domain_analysis
            
        except Exception as e:
            print(f"Clock domain analysis error: {e}")
            return []
    
    def identify_congestion_hotspots(self, threshold_score=10):
        """Find areas of high connectivity that may cause routing congestion"""
        try:
            hotspots = []
            
            # Analyze each node's local connectivity
            for node in self.dag.nodes():
                in_deg = self.dag.in_degree(node)
                out_deg = self.dag.out_degree(node)
                
                # Calculate "congestion score" based on degree
                congestion_score = in_deg + out_deg * 2  # Output fanout weighted more
                
                if congestion_score > threshold_score:  # Configurable threshold
                    # Analyze neighborhood
                    predecessors = list(self.dag.predecessors(node))
                    successors = list(self.dag.successors(node))
                    
                    # Build suggestions list
                    suggestions = []
                    if out_deg > 15:
                        suggestions.append(f'Insert buffer tree to reduce fanout from {out_deg}')
                        suggestions.append(f'Consider logic duplication for critical fanout paths')
                    if in_deg > 10:
                        suggestions.append(f'Restructure logic feeding this gate ({in_deg} inputs)')
                        suggestions.append(f'Break into multiple stages with pipeline registers')
                    if out_deg > 10 and in_deg > 5:
                        suggestions.append(f'High fanin+fanout: review physical constraints')
                    
                    if not suggestions:
                        suggestions.append('Monitor during physical design phase')
                    
                    hotspot = {
                        'gate': node,
                        'gate_type': self.gates[node]['type'] if node in self.gates else 'Unknown',
                        'fanin': in_deg,
                        'fanout': out_deg,
                        'congestion_score': congestion_score,
                        'severity': 'CRITICAL' if congestion_score > 50 else 'WARNING' if congestion_score > 30 else 'MODERATE',
                        'suggestions': suggestions
                    }
                    
                    hotspots.append(hotspot)
            
            # Sort by congestion score
            hotspots.sort(key=lambda x: x['congestion_score'], reverse=True)
            
            return hotspots
            
        except Exception as e:
            print(f"Congestion analysis error: {e}")
            return []
    
    def analyze_path_bottlenecks(self, path):
        """Analyze bottlenecks in a critical path"""
        bottlenecks = []
        
        for i, gate in enumerate(path):
            if gate not in self.gates:
                continue
            
            gate_type = self.gates[gate]['type']
            
            # Check for slow gates
            if any(slow in gate_type.upper() for slow in ['MUX', 'MULT', 'ADDER', 'XOR']):
                bottlenecks.append({
                    'position': i,
                    'gate': gate,
                    'type': gate_type,
                    'reason': 'Slow gate type'
                })
            
            # Check for high fanout after this gate
            if self.dag.out_degree(gate) > 10:
                bottlenecks.append({
                    'position': i,
                    'gate': gate,
                    'type': gate_type,
                    'reason': f'High fanout ({self.dag.out_degree(gate)})'
                })
        
        return bottlenecks
    
    def analyze_signal(self, signal_name):
        """Trace a specific signal with fanout analysis"""
        results = {
            'found': signal_name in self.signals,
            'info': None,
            'drivers': [],
            'readers': [],
            'fanout': 0,
            'fanout_health': 'GOOD'
        }
        
        if signal_name in self.signals:
            results['info'] = self.signals[signal_name]
            
            # Find drivers and readers
            for gate_name, gate_info in self.gates.items():
                for port, sig in gate_info['connections'].items():
                    if sig == signal_name:
                        if port in ['Y', 'Q', 'QN', 'CO', 'S', 'SO', 'Z', 'OUT']:
                            results['drivers'].append(gate_name)
                        else:
                            results['readers'].append(gate_name)
            
            # Fanout analysis
            results['fanout'] = len(results['readers'])
            
            if results['fanout'] > 100:
                results['fanout_health'] = 'CRITICAL'
            elif results['fanout'] > 50:
                results['fanout_health'] = 'WARNING'
            elif results['fanout'] > 20:
                results['fanout_health'] = 'MODERATE'
            else:
                results['fanout_health'] = 'GOOD'
        
        return results
    
    def suggest_buffer_insertion(self, signal_name, fanout_threshold=30):
        """Suggest buffer insertion points for high-fanout signals"""
        result = self.analyze_signal(signal_name)
        
        if not result['found'] or result['fanout'] < fanout_threshold:
            return None
        
        suggestions = []
        readers = result['readers']
        
        # Cluster readers for buffer tree
        num_buffers = (result['fanout'] // fanout_threshold) + 1
        readers_per_buffer = result['fanout'] // num_buffers
        
        for i in range(num_buffers):
            start_idx = i * readers_per_buffer
            end_idx = start_idx + readers_per_buffer if i < num_buffers - 1 else len(readers)
            cluster = readers[start_idx:end_idx]
            
            suggestions.append({
                'buffer_id': f'buf_{signal_name}_{i}',
                'drives': cluster,
                'fanout': len(cluster),
                'location': f'Between {result["drivers"][0] if result["drivers"] else "source"} and readers'
            })
        
        return {
            'signal': signal_name,
            'original_fanout': result['fanout'],
            'suggested_buffers': len(suggestions),
            'buffers': suggestions,
            'estimated_improvement': f'{100 - (fanout_threshold * 100 // result["fanout"])}% fanout reduction'
        }
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        report = f"""
# 📊 NETLIST ANALYSIS REPORT

## 📈 Statistics
- **Total Lines**: {self.stats['total_lines']:,}
- **Modules**: {self.stats['modules']}
- **Signals**: {self.stats['signals']:,}
- **Gate Instances**: {self.stats['gates']:,}
- **DAG Nodes**: {self.stats['dag_nodes']:,}
- **DAG Edges**: {self.stats['dag_edges']:,}

## 🏗️ Modules Found
{', '.join(self.stats['module_names'])}

## ⚡ Gate Distribution
"""
        for gate_type, count in sorted(self.stats['gate_types'].items(), key=lambda x: x[1], reverse=True)[:20]:
            report += f"- **{gate_type}**: {count:,} instances\n"
        
        if self.stats['unconnected']:
            report += f"\n## ⚠️ Unconnected Signals Found\n"
            report += f"Found {len(self.stats['unconnected'])} unconnected signals\n"
            for sig in self.stats['unconnected'][:10]:
                report += f"- `{sig}`\n"
        
        # Critical paths
        critical_paths = self.get_critical_paths(5)
        if critical_paths:
            report += f"\n## 🎯 Critical Paths (Longest Logic Chains)\n"
            for i, (length, path) in enumerate(critical_paths, 1):
                report += f"\n**Path {i}** (Length: {length} gates):\n"
                report += f"`{' -> '.join(path[:5])}{'...' if len(path) > 5 else ''}`\n"
        
        return report
    
    def export_dag_html(self, output_path, clock_domain_colors=None):
        """Generate interactive DAG visualization with optional clock domain coloring"""
        net = Network(height="700px", width="100%", directed=True, notebook=False)
        
        # Add nodes with clock domain coloring if provided
        if clock_domain_colors:
            for node in self.dag.nodes():
                color = clock_domain_colors.get(node, '#97C2FC')  # Default blue
                gate_type = self.gates.get(node, {}).get('type', 'Unknown')
                title = f"{node}\nType: {gate_type}"
                
                # Add domain info to tooltip if available
                for domain, nodes in st.session_state.get('domain_node_map', {}).items():
                    if node in nodes:
                        title += f"\nClock Domain: {domain}"
                        break
                
                net.add_node(node, label=node, color=color, title=title)
            
            # Add edges
            for edge in self.dag.edges():
                net.add_edge(edge[0], edge[1])
        else:
            # Default: just import from networkx
            net.from_nx(self.dag)
        
        # Customize appearance
        net.set_options("""
        {
          "physics": {
            "enabled": true,
            "barnesHut": {
              "gravitationalConstant": -8000,
              "springLength": 200
            }
          },
          "nodes": {
            "font": {
              "size": 10
            }
          }
        }
        """)
        
        net.save_graph(output_path)
        return output_path

# ==================== STREAMLIT UI ====================

# Session state
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None
if 'dag_html_path' not in st.session_state:
    st.session_state.dag_html_path = None
if 'auto_loaded' not in st.session_state:
    st.session_state.auto_loaded = False
if 'dag_colored' not in st.session_state:
    st.session_state.dag_colored = False
if 'domain_node_map' not in st.session_state:
    st.session_state.domain_node_map = {}
if 'domain_colors' not in st.session_state:
    st.session_state.domain_colors = {}

# Auto-load from command-line argument OR final.v on first run
if not st.session_state.auto_loaded:
    # Priority 1: Command-line argument
    if netlist_arg:
        netlist_path = Path(netlist_arg)
    else:
        # Priority 2: Default file.v in parent directory
        netlist_path = Path("../file.v")
    
    if netlist_path.exists():
        try:
            content = netlist_path.read_text()
            analyzer = NetlistAnalyzer(content)
            analyzer.parse()  # Full parse with DAG
            st.session_state.analyzer = analyzer
            st.session_state.auto_loaded = True
            st.toast(f"✅ Loaded {netlist_path.name}! {analyzer.stats['gates']:,} gates, {analyzer.stats['signals']:,} signals", icon="✅")
        except Exception as e:
            st.error(f"Auto-load error: {e}")
    st.session_state.auto_loaded = True

# Show tabs - conditionally show Load tab only if no file was auto-loaded
if st.session_state.analyzer and netlist_arg:
    # File provided via command-line - skip load tab
    tab2, tab3, tab4 = st.tabs([
        "📊 Analysis Report", 
        "🔍 Signal Trace & Debug",
        "📚 Learn EDA"
    ])
    
    # Show quick status at top
    st.success(f"✅ {Path(netlist_arg).name} is loaded and parsed!")
    col1, col2, col3 = st.columns(3)
    analyzer = st.session_state.analyzer
    col1.metric("Gates", f"{analyzer.stats['gates']:,}")
    col2.metric("Signals", f"{analyzer.stats['signals']:,}")
    col3.metric("Modules", analyzer.stats['modules'])
    st.markdown("---")
    
else:
    # No command-line file - show full interface with Load tab
    tab1, tab2, tab3, tab4 = st.tabs([
        "📂 Load Netlist",
        "📊 Analysis Report", 
        "🔍 Signal Trace & Debug",
        "📚 Learn EDA"
    ])
    
    with tab1:
        st.header("📂 Netlist Status")
        
        if st.session_state.analyzer:
            analyzer = st.session_state.analyzer
            st.success("✅ file.v is loaded and parsed!")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Gates", f"{analyzer.stats['gates']:,}")
            col2.metric("Signals", f"{analyzer.stats['signals']:,}")
            col3.metric("Modules", analyzer.stats['modules'])
            
            with st.expander("📄 Preview netlist (first 100 lines)"):
                lines = analyzer.content.split('\n')[:100]
                st.code('\n'.join(lines), language='verilog')
            
            if st.button("🔄 Reload & Re-parse", type="secondary"):
                st.session_state.auto_loaded = False
                st.rerun()
        else:
            st.info("📂 Looking for file.v in current directory...")
        
        st.markdown("---")
        
        # Dynamic file upload/load section
        st.subheader("📂 Load Netlist File")
        
        tab_upload, tab_workspace = st.tabs(["📤 Upload File", "📁 Load from Workspace"])
        
        with tab_upload:
            st.markdown("**Drag & drop or browse for your Verilog netlist file**")
            uploaded_file = st.file_uploader(
                "Choose a .v/.sv file",
                type=['v', 'sv', 'verilog'],
                help="Upload synthesized gate-level netlist"
            )
            
            if uploaded_file:
                st.success(f"📄 File ready: {uploaded_file.name} ({uploaded_file.size:,} bytes)")
                
                if st.button("🚀 Parse Uploaded File", type="primary", use_container_width=True):
                    content = uploaded_file.read().decode('utf-8')
                    
                    with st.spinner("🔄 Parsing netlist..."):
                        try:
                            analyzer = NetlistAnalyzer(content)
                            analyzer.parse()
                            st.session_state.analyzer = analyzer
                            st.balloons()
                            st.success(f"✅ Successfully parsed {uploaded_file.name}!")
                            st.info(f"📊 Found {analyzer.stats['gates']:,} gates, {analyzer.stats['signals']:,} signals")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Parse error: {e}")
        
        with tab_workspace:
            st.markdown("**Load file from workspace directory**")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                workspace_path = st.text_input(
                    "File path (relative or absolute):",
                    value="file.v",
                    placeholder="e.g., file.v, ../netlist.v"
                )
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                load_btn = st.button("📂 Load", type="primary", use_container_width=True)
            
            if load_btn:
                try:
                    path = Path(workspace_path)
                    if path.exists():
                        with open(path, 'r') as f:
                            content = f.read()
                        
                        with st.spinner(f"🔄 Parsing {path.name}..."):
                            analyzer = NetlistAnalyzer(content)
                            analyzer.parse()
                            st.session_state.analyzer = analyzer
                            st.balloons()
                            st.success(f"✅ Successfully loaded and parsed {path.name}!")
                            st.info(f"📊 Found {analyzer.stats['gates']:,} gates, {analyzer.stats['signals']:,} signals")
                            st.rerun()
                    else:
                        st.error(f"❌ File not found: {workspace_path}")
                        st.info("💡 Try using '../file.v' or provide the full path")
                except Exception as e:
                    st.error(f"❌ Error loading file: {e}")
        
        
with tab2:
    st.header("📊 Comprehensive Analysis Report")
    
    if st.session_state.analyzer:
        analyzer = st.session_state.analyzer
        
        # Display report
        report = analyzer.generate_report()
        st.markdown(report)
        
        # Download button
        st.download_button(
            "💾 Download Report",
            report,
            file_name="netlist_analysis_report.md",
            mime="text/markdown"
        )
        
        # Statistics in columns
        st.markdown("---")
        st.subheader("📈 Key Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Gates", f"{analyzer.stats['gates']:,}")
        col2.metric("Total Signals", f"{analyzer.stats['signals']:,}")
        col3.metric("DAG Nodes", f"{analyzer.stats['dag_nodes']:,}")
        col4.metric("DAG Edges", f"{analyzer.stats['dag_edges']:,}")
        
        # Gate type distribution chart
        if analyzer.stats['gate_types']:
            st.subheader("⚡ Gate Type Distribution")
            gate_df = pd.DataFrame(
                list(analyzer.stats['gate_types'].items()),
                columns=['Gate Type', 'Count']
            ).sort_values('Count', ascending=False).head(20)
            
            st.bar_chart(gate_df.set_index('Gate Type'))
    else:
        st.info("👈 Please load and parse a netlist first")

with tab3:
    st.header("🔍 Signal Trace & Debug")
    
    if st.session_state.analyzer:
        analyzer = st.session_state.analyzer
        
        signal_name = st.text_input(
            "Enter signal name to trace:",
            placeholder="e.g., clk, rst_n, n_123"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            analyze_btn = st.button("🔍 Trace Signal", type="primary")
        with col2:
            buffer_btn = st.button("💡 Buffer Suggestions")
        
        if analyze_btn:
            if signal_name:
                result = analyzer.analyze_signal(signal_name)
                
                if result['found']:
                    st.success(f"✅ Found signal: {signal_name}")
                    
                    # Fanout health indicator
                    health_colors = {
                        'GOOD': '🟢',
                        'MODERATE': '🟡',
                        'WARNING': '🟠',
                        'CRITICAL': '🔴'
                    }
                    st.markdown(f"### Fanout Health: {health_colors.get(result['fanout_health'], '⚪')} {result['fanout_health']}")
                    st.metric("Total Fanout", result['fanout'])
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 📤 Drivers")
                        if result['drivers']:
                            for driver in result['drivers']:
                                st.code(driver)
                        else:
                            st.info("No drivers (might be primary input)")
                    
                    with col2:
                        st.markdown("### 📥 Readers")
                        if result['readers']:
                            st.write(f"Showing {min(10, len(result['readers']))} of {len(result['readers'])} readers:")
                            for reader in result['readers'][:10]:
                                st.code(reader)
                            if len(result['readers']) > 10:
                                st.info(f"+ {len(result['readers']) - 10} more readers...")
                        else:
                            st.info("No readers (might be unconnected)")
                    
                    if result['info']:
                        st.markdown("### ℹ️ Signal Info")
                        st.json(result['info'])
                else:
                    st.error(f"❌ Signal '{signal_name}' not found")
            else:
                st.warning("Please enter a signal name")
        
        if buffer_btn:
            if signal_name:
                suggestion = analyzer.suggest_buffer_insertion(signal_name)
                
                if suggestion:
                    st.success(f"💡 Buffer Insertion Suggestions for {signal_name}")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Original Fanout", suggestion['original_fanout'])
                    col2.metric("Suggested Buffers", suggestion['suggested_buffers'])
                    col3.metric("Improvement", suggestion['estimated_improvement'])
                    
                    st.markdown("### 🌳 Suggested Buffer Tree")
                    for buf in suggestion['buffers']:
                        with st.expander(f"📦 {buf['buffer_id']} (drives {buf['fanout']} gates)"):
                            st.write(f"**Location**: {buf['location']}")
                            st.write(f"**Drives**: {', '.join(buf['drives'][:5])}...")
                else:
                    st.info(f"Signal '{signal_name}' doesn't need buffering (fanout < 30)")
            else:
                st.warning("Please enter a signal name")
        
        # List all signals
        with st.expander("📋 View All Signals"):
            if analyzer.signals:
                signal_list = list(analyzer.signals.keys())
                st.write(f"Total: {len(signal_list)} signals")
                st.dataframe(pd.DataFrame({'Signal Name': signal_list[:500]}))
    else:
        st.info("👈 Please load and parse a netlist first")

with tab4:
    st.header("📚 Learn EDA Concepts")
    
    st.markdown("""
    ## 🎯 What This Tool Does
    
    This **LOCAL** analyzer (no API required) provides:
    
    ### 📊 Analysis Capabilities
    - **Statistical Analysis**: Gate counts, signal counts, complexity metrics
    - **Gate Distribution**: Breakdown of gate types used
    - **Unconnected Signal Detection**: Finds UNCONNECTED wires
    - **Critical Path Analysis**: Identifies longest logic chains
    
    ### 🔍 Debug Features
    - **Signal Tracing**: Track any signal through the design
    - **Driver/Reader Analysis**: Find what drives/reads each signal
    - **Connectivity Verification**: Check signal connectivity
    
    ### 🌐 DAG Visualization
    - **Interactive Graph**: Pan, zoom, drag nodes
    - **Connectivity View**: See how gates connect
    - **Path Highlighting**: Identify critical paths
    - **Export to HTML**: Shareable visualizations
    
    ## 🚀 Quick Start
    
    1. **Load Tab**: Upload your final.v or use workspace button
    2. **Click Parse & Analyze**: Builds the internal DAG
    3. **Analysis Tab**: View comprehensive statistics
    4. **Signal Trace Tab**: Debug specific signals
    5. **DAG Tab**: Generate interactive visualization
    
    ## 💡 Use Cases
    
    - **Design Review**: Understand netlist structure
    - **Debug**: Find connectivity issues
    - **Optimization**: Identify critical paths
    - **Documentation**: Generate visual design docs
    - **Learning**: Understand how synthesized designs work
    
    ## ⚡ Advantages Over AI
    
    - ✅ **No API Key Required**: 100% local
    - ✅ **Instant Results**: No waiting for API calls
    - ✅ **Privacy**: Your design never leaves your machine
    - ✅ **Accurate**: Rule-based, deterministic analysis
    - ✅ **Visual**: Interactive DAG graphs
    - ✅ **Fast**: Handles large netlists efficiently
    """)

# Sidebar
with st.sidebar:
    st.header("📌 Quick Info")
    
    if st.session_state.analyzer:
        st.success("✅ Netlist Loaded")
        analyzer = st.session_state.analyzer
        st.metric("Gates", f"{analyzer.stats['gates']:,}")
        st.metric("Signals", f"{analyzer.stats['signals']:,}")
        st.metric("Modules", analyzer.stats['modules'])
        
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.analyzer = None
            st.session_state.dag_html_path = None
            st.rerun()
    else:
        st.info("📂 No netlist loaded yet")
    
    st.markdown("---")
    st.markdown("### ⚡ Features")
    st.markdown("""
    - ✅ No API required
    - ✅ Local processing
    - ✅ DAG visualization
    - ✅ Signal tracing
    - ✅ Critical paths
    - ✅ Gate analysis
    """)
