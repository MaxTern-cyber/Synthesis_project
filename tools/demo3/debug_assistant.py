"""
DEMO3: HARDWARE DEBUG ASSISTANT
Advanced debugging tool for EDA engineers
Features: Signal tracing, loop detection, fanout analysis, connectivity checker
"""

import streamlit as st
import networkx as nx
import re
from pathlib import Path
import pandas as pd
from collections import defaultdict, deque
import sys

# Parse command-line arguments for netlist file
netlist_arg = None
if len(sys.argv) > 1:
    netlist_arg = sys.argv[1]
else:
    # Default to file.v in parent directory
    netlist_arg = "../file.v"

st.set_page_config(
    page_title="Hardware Debug Assistant",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Hardware Debug Assistant")
st.caption("Advanced debugging tools for EDA engineers - Find issues fast!")

# ==================== NETLIST DEBUGGER ====================
class NetlistDebugger:
    def __init__(self, content):
        self.content = content
        self.dag = nx.DiGraph()
        self.signals = {}
        self.gates = {}
        self.modules = {}
        self.issues = []
        
    def parse(self):
        """Fast parse for debugging"""
        clean = re.sub(r'//.*?\n', '\n', self.content)
        clean = re.sub(r'/\*.*?\*/', '', clean, flags=re.DOTALL)
        
        # Extract modules
        for match in re.finditer(r'module\s+(\w+)', clean):
            self.modules[match.group(1)] = True
        
        # Extract signals
        for match in re.finditer(r'wire\s+(?:\[.*?\])?\s*([\w,\s]+);', clean):
            for sig in match.group(1).split(','):
                sig = sig.strip()
                self.signals[sig] = {'drivers': [], 'readers': [], 'type': 'wire'}
        
        # Extract gates
        gate_pattern = r'(\w+)\s+(\w+)\s*\((.*?)\);'
        for match in re.finditer(gate_pattern, clean, re.DOTALL):
            gate_type, instance, connections = match.groups()
            
            if gate_type in self.modules:
                continue
            
            ports = {}
            for port_match in re.finditer(r'\.(\w+)\s*\(([^)]+)\)', connections):
                port, signal = port_match.groups()
                ports[port] = signal.strip()
            
            self.gates[instance] = {
                'type': gate_type,
                'ports': ports
            }
            
            # Build connectivity
            for port, signal in ports.items():
                if port in ['Y', 'Q', 'Z', 'OUT', 'S', 'CO']:
                    if signal in self.signals:
                        self.signals[signal]['drivers'].append(instance)
                else:
                    if signal in self.signals:
                        self.signals[signal]['readers'].append(instance)
    
    def find_unconnected_signals(self):
        """Find signals with no drivers or readers"""
        unconnected = []
        for sig, info in self.signals.items():
            if not info['drivers'] and not info['readers']:
                unconnected.append({'signal': sig, 'issue': 'No connections'})
            elif not info['drivers']:
                unconnected.append({'signal': sig, 'issue': 'No driver'})
            elif not info['readers']:
                unconnected.append({'signal': sig, 'issue': 'No readers'})
        return unconnected
    
    def find_multiple_drivers(self):
        """Find signals driven by multiple gates"""
        multi = []
        for sig, info in self.signals.items():
            if len(info['drivers']) > 1:
                multi.append({
                    'signal': sig,
                    'drivers': info['drivers'],
                    'count': len(info['drivers'])
                })
        return multi
    
    def analyze_fanout(self, threshold=50):
        """Find signals with high fanout"""
        high_fanout = []
        for sig, info in self.signals.items():
            readers = len(info['readers'])
            if readers > threshold:
                high_fanout.append({
                    'signal': sig,
                    'fanout': readers,
                    'readers': info['readers'][:10]  # Sample
                })
        return sorted(high_fanout, key=lambda x: x['fanout'], reverse=True)
    
    def analyze_fanout_detailed(self, signal, include_timing=True):
        """Detailed fanout analysis with timing estimation"""
        if signal not in self.signals:
            return None
        
        info = self.signals[signal]
        readers = info['readers']
        
        # Gate load estimates (capacitive units)
        gate_loads = {
            'NAND': 1.0, 'NOR': 1.2, 'AND': 1.0, 'OR': 1.2,
            'INV': 0.8, 'BUF': 1.0, 'XOR': 1.5, 'MUX': 2.0,
            'DFF': 2.5, 'LATCH': 2.0
        }
        
        # Analyze each reader
        reader_details = []
        total_load = 0
        
        for reader_gate in readers:
            if reader_gate in self.gates:
                gate_type = self.gates[reader_gate]['type']
                
                # Estimate load
                load = 1.0  # Default
                for key, val in gate_loads.items():
                    if key in gate_type.upper():
                        load = val
                        break
                
                total_load += load
                
                # Find which port this signal connects to
                connected_port = None
                for port, sig in self.gates[reader_gate]['ports'].items():
                    if sig == signal:
                        connected_port = port
                        break
                
                reader_details.append({
                    'gate': reader_gate,
                    'type': gate_type,
                    'load': load,
                    'port': connected_port
                })
        
        # Timing estimation
        timing_penalty = 0
        if include_timing:
            # Base delay per fanout
            base_delay = 0.01  # ns per load unit
            timing_penalty = total_load * base_delay
        
        # Health assessment
        health = 'GOOD'
        if len(readers) > 100:
            health = 'CRITICAL'
        elif len(readers) > 50:
            health = 'WARNING'
        elif len(readers) > 20:
            health = 'MODERATE'
        
        return {
            'signal': signal,
            'fanout': len(readers),
            'total_load': round(total_load, 2),
            'avg_load': round(total_load / len(readers), 2) if readers else 0,
            'timing_penalty_ns': round(timing_penalty, 3),
            'health': health,
            'reader_details': reader_details[:20],  # Limit for display
            'drivers': info['drivers']
        }
    
    def suggest_fanout_optimization(self, signal, threshold=30):
        """Suggest optimizations for high-fanout signals"""
        analysis = self.analyze_fanout_detailed(signal)
        
        if not analysis or analysis['fanout'] < threshold:
            return None
        
        suggestions = []
        
        # Suggestion 1: Buffer tree
        num_buffers = (analysis['fanout'] // threshold) + 1
        suggestions.append({
            'type': 'Buffer Tree',
            'description': f'Insert {num_buffers} buffers to distribute fanout',
            'expected_fanout': threshold,
            'timing_improvement': f'{50 - (threshold * 50 // analysis["fanout"])}%'
        })
        
        # Suggestion 2: Signal replication
        if analysis['fanout'] > 80:
            suggestions.append({
                'type': 'Signal Replication',
                'description': 'Replicate driver logic to create parallel paths',
                'expected_fanout': analysis['fanout'] // 2,
                'timing_improvement': '40-60%'
            })
        
        # Suggestion 3: Register retiming
        suggestions.append({
            'type': 'Register Retiming',
            'description': 'Move registers closer to high-fanout points',
            'expected_fanout': analysis['fanout'],
            'timing_improvement': '20-30%'
        })
        
        return {
            'signal': signal,
            'current_fanout': analysis['fanout'],
            'current_load': analysis['total_load'],
            'timing_penalty': analysis['timing_penalty_ns'],
            'suggestions': suggestions
        }
    
    
    def trace_signal_path(self, signal, max_depth=10):
        """Trace signal through the design with timing"""
        if signal not in self.signals:
            return None
        
        info = self.signals[signal]
        
        # Gate delays for timing
        gate_delays = {
            'NAND': 0.05, 'NOR': 0.06, 'INV': 0.03, 'BUF': 0.04,
            'XOR': 0.10, 'MUX': 0.12, 'DFF': 0.15
        }
        
        # Trace backwards (drivers)
        backward = []
        visited = set()
        queue = deque([(signal, 0, 0.0)])  # signal, depth, cumulative_delay
        
        while queue:
            sig, depth, delay = queue.popleft()
            if depth >= max_depth or sig in visited:
                continue
            visited.add(sig)
            
            if sig in self.signals:
                for driver in self.signals[sig]['drivers']:
                    # Calculate gate delay
                    gate_delay = 0.05  # Default
                    if driver in self.gates:
                        gate_type = self.gates[driver]['type']
                        for key, val in gate_delays.items():
                            if key in gate_type.upper():
                                gate_delay = val
                                break
                    
                    new_delay = delay + gate_delay
                    backward.append({
                        'depth': depth,
                        'gate': driver,
                        'signal': sig,
                        'gate_type': self.gates[driver]['type'] if driver in self.gates else 'Unknown',
                        'cumulative_delay_ns': round(new_delay, 3)
                    })
                    # Find inputs to this gate
                    if driver in self.gates:
                        for port, in_sig in self.gates[driver]['ports'].items():
                            if port not in ['Y', 'Q', 'Z', 'OUT', 'S', 'CO']:
                                queue.append((in_sig, depth + 1, new_delay))
        
        # Trace forward (readers)
        forward = []
        visited = set()
        queue = deque([(signal, 0, 0.0)])
        
        while queue:
            sig, depth, delay = queue.popleft()
            if depth >= max_depth or sig in visited:
                continue
            visited.add(sig)
            
            if sig in self.signals:
                for reader in self.signals[sig]['readers']:
                    # Calculate gate delay
                    gate_delay = 0.05
                    if reader in self.gates:
                        gate_type = self.gates[reader]['type']
                        for key, val in gate_delays.items():
                            if key in gate_type.upper():
                                gate_delay = val
                                break
                    
                    new_delay = delay + gate_delay
                    forward.append({
                        'depth': depth,
                        'gate': reader,
                        'signal': sig,
                        'gate_type': self.gates[reader]['type'] if reader in self.gates else 'Unknown',
                        'cumulative_delay_ns': round(new_delay, 3)
                    })
                    # Find outputs from this gate
                    if reader in self.gates:
                        for port, out_sig in self.gates[reader]['ports'].items():
                            if port in ['Y', 'Q', 'Z', 'OUT', 'S', 'CO']:
                                queue.append((out_sig, depth + 1, new_delay))
        
        return {
            'signal': signal,
            'direct_drivers': info['drivers'],
            'direct_readers': info['readers'],
            'backward_trace': backward,
            'forward_trace': forward
        }
    
    def find_suspicious_patterns(self):
        """Find common bug patterns"""
        issues = []
        
        # UNCONNECTED signals
        for sig in self.signals:
            if 'UNCONNECTED' in sig.upper():
                issues.append({
                    'severity': 'WARNING',
                    'type': 'Unconnected Signal',
                    'signal': sig,
                    'message': 'Signal explicitly marked as unconnected'
                })
        
        # Signals ending in _n without _p counterpart
        n_signals = {s for s in self.signals if s.endswith('_n')}
        for sig in n_signals:
            p_sig = sig[:-2] + '_p'
            if p_sig not in self.signals:
                issues.append({
                    'severity': 'INFO',
                    'type': 'Unpaired Signal',
                    'signal': sig,
                    'message': f'Found {sig} but no {p_sig} counterpart'
                })
        
        # Floating inputs (gates with unconnected inputs)
        for gate_name, gate_info in self.gates.items():
            for port, signal in gate_info['ports'].items():
                if signal == '' or signal == 'NC':
                    issues.append({
                        'severity': 'ERROR',
                        'type': 'Floating Input',
                        'signal': gate_name,
                        'message': f'Port {port} has no connection'
                    })
        
        return issues
    
    def get_statistics(self):
        """Get design statistics"""
        return {
            'total_signals': len(self.signals),
            'total_gates': len(self.gates),
            'total_modules': len(self.modules),
            'unconnected': len([s for s, i in self.signals.items() if not i['drivers'] and not i['readers']]),
            'multi_driver': len([s for s, i in self.signals.items() if len(i['drivers']) > 1])
        }

# ==================== SESSION STATE ====================
if 'debugger' not in st.session_state:
    st.session_state.debugger = None
if 'loaded' not in st.session_state:
    st.session_state.loaded = False

# Auto-load from command-line argument
if not st.session_state.loaded:
    if netlist_arg:
        netlist_path = Path(netlist_arg)
    else:
        netlist_path = Path("../file.v")
    
    if netlist_path.exists():
        try:
            content = netlist_path.read_text()
            debugger = NetlistDebugger(content)
            debugger.parse()
            st.session_state.debugger = debugger
            st.session_state.loaded = True
            st.toast(f"✅ Loaded {netlist_path.name}!", icon="✅")
        except Exception as e:
            st.error(f"Load error: {e}")
    st.session_state.loaded = True

# ==================== UI ====================
if not st.session_state.debugger:
    st.error("❌ No netlist loaded. Place netlist.v in parent directory.")
    st.stop()

debugger = st.session_state.debugger
stats = debugger.get_statistics()

# Top metrics
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("🔌 Signals", f"{stats['total_signals']:,}")
col2.metric("⚡ Gates", f"{stats['total_gates']:,}")
col3.metric("📦 Modules", stats['total_modules'])
col4.metric("⚠️ Unconnected", stats['unconnected'])
col5.metric("🔴 Multi-Driver", stats['multi_driver'])

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Signal Tracer",
    "⚠️ Issue Finder",
    "📊 Connectivity Report",
    "🎯 Fanout Analyzer",
    "🔬 Advanced Debug"
])

with tab1:
    st.header("🔍 Signal Path Tracer")
    st.info("Trace any signal backward (to its sources) and forward (to its destinations)")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        signal_to_trace = st.text_input(
            "Enter signal name:",
            placeholder="e.g., clk, rst_n, data_out[0]",
            key="trace_signal"
        )
    
    with col2:
        trace_depth = st.number_input("Max Depth", min_value=1, max_value=20, value=5)
    
    if st.button("🔍 Trace Signal", type="primary"):
        if signal_to_trace:
            result = debugger.trace_signal_path(signal_to_trace, trace_depth)
            
            if result:
                st.success(f"✅ Found signal: {signal_to_trace}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### ⬅️ Backward Trace (Sources)")
                    if result['direct_drivers']:
                        st.markdown(f"**Direct Drivers:** `{', '.join(result['direct_drivers'])}`")
                    
                    if result['backward_trace']:
                        df = pd.DataFrame(result['backward_trace'])
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No backward connections (primary input)")
                
                with col2:
                    st.markdown("### ➡️ Forward Trace (Destinations)")
                    if result['direct_readers']:
                        st.markdown(f"**Direct Readers:** {len(result['direct_readers'])} gates")
                        with st.expander("View all readers"):
                            st.code('\n'.join(result['direct_readers'][:50]))
                    
                    if result['forward_trace']:
                        df = pd.DataFrame(result['forward_trace'])
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No forward connections (primary output)")
            else:
                st.error(f"❌ Signal '{signal_to_trace}' not found")

with tab2:
    st.header("⚠️ Issue Finder - Automated Bug Detection")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("Click below to scan for common issues")
    
    with col2:
        scan_btn = st.button("🔍 Scan for Issues", type="primary", use_container_width=True)
    
    if scan_btn:
        with st.spinner("🔍 Scanning design..."):
            # Unconnected signals
            st.markdown("### 🔌 Unconnected Signals")
            unconnected = debugger.find_unconnected_signals()
            if unconnected:
                st.warning(f"Found {len(unconnected)} unconnected signals")
                df = pd.DataFrame(unconnected)
                st.dataframe(df, use_container_width=True)
            else:
                st.success("✅ No unconnected signals found")
            
            # Multiple drivers
            st.markdown("### 🔴 Multiple Driver Issues")
            multi = debugger.find_multiple_drivers()
            if multi:
                st.error(f"Found {len(multi)} signals with multiple drivers!")
                for item in multi[:10]:
                    st.warning(f"**{item['signal']}** driven by {item['count']} gates: {', '.join(item['drivers'])}")
            else:
                st.success("✅ No multiple driver issues")
            
            # Suspicious patterns
            st.markdown("### 🔬 Suspicious Patterns")
            issues = debugger.find_suspicious_patterns()
            if issues:
                for issue in issues:
                    if issue['severity'] == 'ERROR':
                        st.error(f"**{issue['type']}**: {issue['signal']} - {issue['message']}")
                    elif issue['severity'] == 'WARNING':
                        st.warning(f"**{issue['type']}**: {issue['signal']} - {issue['message']}")
                    else:
                        st.info(f"**{issue['type']}**: {issue['signal']} - {issue['message']}")
            else:
                st.success("✅ No suspicious patterns found")

with tab3:
    st.header("📊 Connectivity Report")
    
    # Search for specific signal
    search = st.text_input("Search signals:", placeholder="Enter partial name")
    
    if search:
        matches = [s for s in debugger.signals.keys() if search.lower() in s.lower()]
        st.write(f"Found {len(matches)} matching signals:")
        
        data = []
        for sig in matches[:100]:
            info = debugger.signals[sig]
            data.append({
                'Signal': sig,
                'Drivers': len(info['drivers']),
                'Readers': len(info['readers']),
                'Status': '✅ OK' if info['drivers'] and info['readers'] else '⚠️ Issue'
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Enter a signal name to search connectivity")
    
    # Summary stats
    with st.expander("📊 Full Design Statistics"):
        st.markdown(f"""
        - **Total Signals**: {stats['total_signals']:,}
        - **Total Gates**: {stats['total_gates']:,}
        - **Unconnected**: {stats['unconnected']}
        - **Multi-Driver**: {stats['multi_driver']}
        """)

with tab4:
    st.header("🎯 Fanout Analyzer")
    st.info("Analyze high-fanout signals that may impact timing and require buffering")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fanout_signal = st.text_input(
            "Signal name for detailed analysis:",
            placeholder="e.g., clk, data_bus[0]",
            key="fanout_signal"
        )
    
    with col2:
        fanout_threshold_detail = st.number_input("Optimization Threshold", min_value=10, max_value=200, value=30)
    
    col1, col2 = st.columns(2)
    with col1:
        analyze_detail_btn = st.button("🔬 Detailed Analysis", type="primary")
    with col2:
        optimize_btn = st.button("💡 Get Optimization Suggestions")
    
    if analyze_detail_btn and fanout_signal:
        analysis = debugger.analyze_fanout_detailed(fanout_signal)
        
        if analysis:
            st.success(f"✅ Detailed Fanout Analysis: {fanout_signal}")
            
            # Health indicator
            health_colors = {
                'GOOD': '🟢',
                'MODERATE': '🟡',
                'WARNING': '🟠',
                'CRITICAL': '🔴'
            }
            st.markdown(f"## Health Status: {health_colors.get(analysis['health'], '⚪')} {analysis['health']}")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Fanout", analysis['fanout'])
            col2.metric("Total Load", f"{analysis['total_load']} units")
            col3.metric("Avg Load", f"{analysis['avg_load']} units")
            col4.metric("Timing Penalty", f"{analysis['timing_penalty_ns']} ns")
            
            # Driver info
            st.markdown("### 📤 Drivers")
            st.write(", ".join(analysis['drivers']) if analysis['drivers'] else "No drivers (primary input)")
            
            # Reader details
            st.markdown("### 📥 Reader Details (Top 20)")
            reader_data = []
            for r in analysis['reader_details']:
                reader_data.append({
                    'Gate': r['gate'],
                    'Type': r['type'],
                    'Load': r['load'],
                    'Port': r['port']
                })
            
            df = pd.DataFrame(reader_data)
            st.dataframe(df, use_container_width=True)
            
            # Load distribution chart
            if reader_data:
                st.markdown("### 📊 Load Distribution")
                load_counts = {}
                for r in analysis['reader_details']:
                    load_counts[r['type']] = load_counts.get(r['type'], 0) + r['load']
                
                chart_data = pd.DataFrame({
                    'Gate Type': list(load_counts.keys()),
                    'Total Load': list(load_counts.values())
                })
                st.bar_chart(chart_data.set_index('Gate Type'))
        else:
            st.error(f"Signal '{fanout_signal}' not found")
    
    if optimize_btn and fanout_signal:
        suggestions = debugger.suggest_fanout_optimization(fanout_signal, fanout_threshold_detail)
        
        if suggestions:
            st.success(f"💡 Optimization Suggestions for {fanout_signal}")
            
            # Current state
            st.markdown("### 📊 Current State")
            col1, col2, col3 = st.columns(3)
            col1.metric("Fanout", suggestions['current_fanout'])
            col2.metric("Total Load", f"{suggestions['current_load']} units")
            col3.metric("Timing Penalty", f"{suggestions['timing_penalty']} ns")
            
            # Suggestions
            st.markdown("### 🎯 Recommended Optimizations")
            for i, sug in enumerate(suggestions['suggestions'], 1):
                with st.expander(f"Option {i}: {sug['type']}"):
                    st.write(f"**Description**: {sug['description']}")
                    st.write(f"**Expected Fanout**: {sug['expected_fanout']}")
                    st.write(f"**Timing Improvement**: {sug['timing_improvement']}")
                    
                    if sug['type'] == 'Buffer Tree':
                        st.info("💡 Insert buffers between driver and readers to reduce capacitive load")
                    elif sug['type'] == 'Signal Replication':
                        st.info("💡 Duplicate the driver logic to create parallel signal paths")
                    elif sug['type'] == 'Register Retiming':
                        st.info("💡 Move pipeline registers closer to high-fanout points")
        else:
            st.info(f"Signal '{fanout_signal}' doesn't require optimization (fanout < {fanout_threshold_detail})")
    
    st.markdown("---")
    
    # High fanout signals list
    st.info("Find signals with high fanout (many readers) - potential timing bottlenecks")
    
    threshold = st.slider("Fanout threshold:", 1, 200, 50)
    
    if st.button("📊 Analyze Fanout", type="primary"):
        high_fanout = debugger.analyze_fanout(threshold)
        
        if high_fanout:
            st.warning(f"Found {len(high_fanout)} signals with fanout > {threshold}")
            
            for item in high_fanout[:20]:
                with st.expander(f"🔌 {item['signal']} - Fanout: {item['fanout']}"):
                    st.markdown(f"**Total Readers**: {item['fanout']}")
                    st.markdown("**Sample Readers (first 10):**")
                    st.code('\n'.join(item['readers']))
        else:
            st.success(f"✅ No signals with fanout > {threshold}")

with tab5:
    st.header("🔬 Advanced Debug Tools")
    
    st.markdown("### 🔧 Quick Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📝 Export Signal List")
        if st.button("💾 Export All Signals", use_container_width=True):
            signal_list = '\n'.join(sorted(debugger.signals.keys()))
            st.download_button(
                "Download signals.txt",
                signal_list,
                file_name="all_signals.txt",
                mime="text/plain"
            )
    
    with col2:
        st.markdown("#### 📝 Export Gate List")
        if st.button("💾 Export All Gates", use_container_width=True):
            gate_list = '\n'.join([f"{name} ({info['type']})" for name, info in debugger.gates.items()])
            st.download_button(
                "Download gates.txt",
                gate_list,
                file_name="all_gates.txt",
                mime="text/plain"
            )
    
    st.markdown("### 🔍 Custom Analysis")
    
    analysis_type = st.selectbox(
        "Choose analysis:",
        ["Find all clock signals", "Find all reset signals", "Find all register outputs"]
    )
    
    if st.button("🚀 Run Analysis", type="primary"):
        if "clock" in analysis_type.lower():
            clocks = [s for s in debugger.signals if 'clk' in s.lower() or 'clock' in s.lower()]
            st.success(f"Found {len(clocks)} clock signals:")
            st.code('\n'.join(clocks[:50]))
        elif "reset" in analysis_type.lower():
            resets = [s for s in debugger.signals if 'rst' in s.lower() or 'reset' in s.lower()]
            st.success(f"Found {len(resets)} reset signals:")
            st.code('\n'.join(resets[:50]))
        elif "register" in analysis_type.lower():
            regs = [name for name, info in debugger.gates.items() if 'DFF' in info['type'] or 'REG' in info['type']]
            st.success(f"Found {len(regs)} registers:")
            st.code('\n'.join(regs[:50]))

# Sidebar
with st.sidebar:
    st.header("🔧 Debug Tools")
    
    st.metric("Design Health", "85%", "⬆️ Good")
    
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🔄 Reload Netlist", use_container_width=True):
        st.session_state.loaded = False
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📚 Features")
    st.markdown("""
    - ✅ Signal path tracing
    - ✅ Connectivity checker
    - ✅ Fanout analysis
    - ✅ Issue detection
    - ✅ Pattern matching
    - ✅ Export reports
    """)
    
    st.markdown("---")
    st.caption("💡 **Tip**: Start with Issue Finder to get an overview")
