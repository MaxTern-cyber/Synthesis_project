import streamlit as st
import re
from collections import defaultdict
import pandas as pd
from datetime import datetime

class EnhancedVerilogParser:
    """Enhanced Verilog parser with proper boundary detection and constant handling"""
    
    def __init__(self, content):
        self.content = content
        self.module_name = ""
        self.primary_inputs = set()
        self.primary_outputs = set()
        self.internal_signals = set()
        self.gates = {}
        self.signal_drivers = defaultdict(list)  # signal -> list of gates driving it
        self.signal_readers = defaultdict(list)  # signal -> list of gates reading it
        self.tied_signals = {}  # signal -> constant value ('0' or '1')
        self.constant_nets = {}  # Maps constant connections like 1'b0, 1'b1
        
    def parse(self):
        """Parse the Verilog netlist"""
        self._extract_module_info()
        self._extract_primary_ports()
        self._extract_internal_signals()
        self._extract_gates()
        self._detect_tied_signals()
        self._build_connectivity_map()
        
    def _extract_module_info(self):
        """Extract module name"""
        module_pattern = r'module\s+(\w+)'
        match = re.search(module_pattern, self.content)
        if match:
            self.module_name = match.group(1)
    
    def _extract_primary_ports(self):
        """Extract primary inputs and outputs"""
        # Find input declarations
        input_pattern = r'input(?:\s+\[[\d:]+\])?\s+([\w,\s]+);'
        for match in re.finditer(input_pattern, self.content):
            signals = match.group(1).split(',')
            for sig in signals:
                sig = sig.strip()
                if sig:
                    self.primary_inputs.add(sig)
        
        # Find output declarations
        output_pattern = r'output(?:\s+\[[\d:]+\])?\s+([\w,\s]+);'
        for match in re.finditer(output_pattern, self.content):
            signals = match.group(1).split(',')
            for sig in signals:
                sig = sig.strip()
                if sig:
                    self.primary_outputs.add(sig)
    
    def _extract_internal_signals(self):
        """Extract internal wires and regs"""
        # Wire declarations
        wire_pattern = r'wire(?:\s+\[[\d:]+\])?\s+([\w,\s]+);'
        for match in re.finditer(wire_pattern, self.content):
            signals = match.group(1).split(',')
            for sig in signals:
                sig = sig.strip()
                if sig and sig not in self.primary_inputs and sig not in self.primary_outputs:
                    self.internal_signals.add(sig)
        
        # Reg declarations
        reg_pattern = r'reg(?:\s+\[[\d:]+\])?\s+([\w,\s]+);'
        for match in re.finditer(reg_pattern, self.content):
            signals = match.group(1).split(',')
            for sig in signals:
                sig = sig.strip()
                if sig and sig not in self.primary_inputs and sig not in self.primary_outputs:
                    self.internal_signals.add(sig)
    
    def _extract_gates(self):
        """Extract gate instances with connections"""
        # Pattern for gate instances
        # Format: GATE_TYPE INSTANCE_NAME (.PORT(NET), .PORT(NET), ...);
        gate_pattern = r'(\w+)\s+(\w+)\s*\((.*?)\)\s*;'
        
        for match in re.finditer(gate_pattern, self.content, re.DOTALL):
            gate_type = match.group(1)
            instance_name = match.group(2)
            connections = match.group(3)
            
            # Skip module and assign statements
            if gate_type in ['module', 'assign', 'wire', 'reg', 'input', 'output']:
                continue
            
            # Parse connections
            port_connections = {}
            conn_pattern = r'\.(\w+)\s*\(\s*([^)]+)\s*\)'
            for conn_match in re.finditer(conn_pattern, connections):
                port = conn_match.group(1)
                net = conn_match.group(2).strip()
                port_connections[port] = net
            
            if port_connections:
                self.gates[instance_name] = {
                    'type': gate_type,
                    'connections': port_connections,
                    'inputs': [],
                    'outputs': []
                }
    
    def _detect_tied_signals(self):
        """Detect signals tied to constants (1'b0, 1'b1, 0, 1)"""
        constant_patterns = [
            r"1'b0",
            r"1'b1", 
            r"1'B0",
            r"1'B1",
            r"\b0\b",
            r"\b1\b"
        ]
        
        for instance_name, gate_info in self.gates.items():
            for port, net in gate_info['connections'].items():
                # Check if net is a constant
                for pattern in constant_patterns:
                    if re.match(pattern, net):
                        # Determine if it's 0 or 1
                        if '0' in net:
                            self.tied_signals[f"{instance_name}.{port}"] = '0'
                            self.constant_nets[net] = '0'
                        else:
                            self.tied_signals[f"{instance_name}.{port}"] = '1'
                            self.constant_nets[net] = '1'
                        break
    
    def _build_connectivity_map(self):
        """Build signal driver and reader mappings"""
        for instance_name, gate_info in self.gates.items():
            gate_type = gate_info['type'].upper()
            connections = gate_info['connections']
            
            # Identify input and output ports based on gate type and common port names
            input_ports = []
            output_ports = []
            
            for port, net in connections.items():
                port_upper = port.upper()
                
                # Common output port names
                if port_upper in ['Z', 'ZN', 'Q', 'QN', 'Y', 'OUT', 'O', 'S', 'CO', 'SUM']:
                    output_ports.append(port)
                    gate_info['outputs'].append(net)
                    # This gate drives this signal
                    if not self._is_constant(net):
                        self.signal_drivers[net].append(instance_name)
                
                # Common input port names
                elif port_upper in ['A', 'B', 'C', 'D', 'I', 'IN', 'A0', 'A1', 'A2', 'A3',
                                   'B0', 'B1', 'B2', 'B3', 'S0', 'S1', 'SEL', 'CK', 'CLK',
                                   'D', 'RN', 'SN', 'E', 'EN', 'CI', 'CIN']:
                    input_ports.append(port)
                    gate_info['inputs'].append(net)
                    # This gate reads this signal
                    if not self._is_constant(net):
                        self.signal_readers[net].append(instance_name)
    
    def _is_constant(self, net):
        """Check if a net is a constant value"""
        return net in self.constant_nets or re.match(r"1'[bB][01]", net) or net in ['0', '1']
    
    def get_signal_type(self, signal):
        """Determine the type of a signal"""
        if signal in self.primary_inputs:
            return "PRIMARY_INPUT"
        elif signal in self.primary_outputs:
            return "PRIMARY_OUTPUT"
        elif signal in self.internal_signals:
            return "INTERNAL"
        else:
            return "UNKNOWN"
    
    def backtrack_signal(self, signal, max_depth=10):
        """
        Backtrack a signal to find what drives it
        Returns None if signal is a primary input (can't backtrack further)
        """
        signal = signal.strip()
        
        # Check if this is a primary input
        if signal in self.primary_inputs:
            return {
                'status': 'BOUNDARY',
                'type': 'PRIMARY_INPUT',
                'message': f"'{signal}' is a PRIMARY INPUT - cannot backtrack further (this is the starting point)",
                'signal': signal
            }
        
        # Check if this signal exists
        if signal not in self.signal_drivers and signal not in self.internal_signals and signal not in self.primary_outputs:
            return {
                'status': 'NOT_FOUND',
                'message': f"Signal '{signal}' not found in the design",
                'signal': signal
            }
        
        # Get drivers
        drivers = self.signal_drivers.get(signal, [])
        
        if not drivers:
            # No drivers but not a primary input - might be floating or tied
            tied_info = []
            for tied_port, value in self.tied_signals.items():
                if signal in tied_port:
                    tied_info.append((tied_port, value))
            
            if tied_info:
                return {
                    'status': 'TIED',
                    'type': 'CONSTANT',
                    'message': f"Signal '{signal}' is tied to constant value",
                    'tied_connections': tied_info,
                    'signal': signal
                }
            else:
                return {
                    'status': 'FLOATING',
                    'message': f"Signal '{signal}' has no drivers (floating or undriven)",
                    'signal': signal
                }
        
        # Build backtrack tree
        backtrack_info = {
            'status': 'SUCCESS',
            'signal': signal,
            'signal_type': self.get_signal_type(signal),
            'drivers': []
        }
        
        for driver_gate in drivers:
            gate_info = self.gates[driver_gate]
            driver_detail = {
                'gate': driver_gate,
                'type': gate_info['type'],
                'inputs': gate_info['inputs'],
                'outputs': gate_info['outputs']
            }
            backtrack_info['drivers'].append(driver_detail)
        
        return backtrack_info
    
    def forward_track_signal(self, signal, max_depth=10):
        """
        Forward track a signal to find what reads it
        Returns None if signal is a primary output (can't track further)
        """
        signal = signal.strip()
        
        # Check if this is a primary output
        if signal in self.primary_outputs:
            return {
                'status': 'BOUNDARY',
                'type': 'PRIMARY_OUTPUT',
                'message': f"'{signal}' is a PRIMARY OUTPUT - cannot forward track further (this is the endpoint)",
                'signal': signal
            }
        
        # Check if this signal exists
        if signal not in self.signal_readers and signal not in self.internal_signals and signal not in self.primary_inputs:
            return {
                'status': 'NOT_FOUND',
                'message': f"Signal '{signal}' not found in the design",
                'signal': signal
            }
        
        # Get readers
        readers = self.signal_readers.get(signal, [])
        
        if not readers:
            return {
                'status': 'UNLOADED',
                'message': f"Signal '{signal}' has no readers (unloaded or unused)",
                'signal': signal
            }
        
        # Build forward track tree
        forward_info = {
            'status': 'SUCCESS',
            'signal': signal,
            'signal_type': self.get_signal_type(signal),
            'readers': []
        }
        
        for reader_gate in readers:
            gate_info = self.gates[reader_gate]
            reader_detail = {
                'gate': reader_gate,
                'type': gate_info['type'],
                'inputs': gate_info['inputs'],
                'outputs': gate_info['outputs']
            }
            forward_info['readers'].append(reader_detail)
        
        return forward_info
    
    def get_full_connectivity(self, signal):
        """Get complete connectivity info for a signal"""
        signal = signal.strip()
        
        signal_type = self.get_signal_type(signal)
        drivers = self.signal_drivers.get(signal, [])
        readers = self.signal_readers.get(signal, [])
        
        # Check for tied connections
        tied_info = []
        for tied_port, value in self.tied_signals.items():
            if signal in tied_port:
                tied_info.append((tied_port, value))
        
        return {
            'signal': signal,
            'type': signal_type,
            'is_primary_input': signal in self.primary_inputs,
            'is_primary_output': signal in self.primary_outputs,
            'driver_count': len(drivers),
            'reader_count': len(readers),
            'drivers': drivers,
            'readers': readers,
            'tied_connections': tied_info
        }
    
    def get_all_tied_signals(self):
        """Get all signals tied to constants"""
        tied_summary = defaultdict(list)
        
        for tied_port, value in self.tied_signals.items():
            tied_summary[value].append(tied_port)
        
        return dict(tied_summary)
    
    def get_statistics(self):
        """Get design statistics"""
        return {
            'module_name': self.module_name,
            'primary_inputs': len(self.primary_inputs),
            'primary_outputs': len(self.primary_outputs),
            'internal_signals': len(self.internal_signals),
            'total_gates': len(self.gates),
            'tied_to_zero': len([v for v in self.tied_signals.values() if v == '0']),
            'tied_to_one': len([v for v in self.tied_signals.values() if v == '1']),
            'floating_signals': self._count_floating_signals(),
            'unloaded_signals': self._count_unloaded_signals()
        }
    
    def _count_floating_signals(self):
        """Count signals with no drivers (excluding primary inputs)"""
        count = 0
        all_signals = self.internal_signals | self.primary_outputs
        for sig in all_signals:
            if sig not in self.signal_drivers or len(self.signal_drivers[sig]) == 0:
                count += 1
        return count
    
    def _count_unloaded_signals(self):
        """Count signals with no readers (excluding primary outputs)"""
        count = 0
        all_signals = self.internal_signals | self.primary_inputs
        for sig in all_signals:
            if sig not in self.signal_readers or len(self.signal_readers[sig]) == 0:
                count += 1
        return count


# Streamlit Application
def main():
    st.set_page_config(
        page_title="Advanced Hardware Debugger",
        page_icon="🔧",
        layout="wide"
    )
    
    st.title("🔧 Advanced Hardware Debugger")
    st.markdown("**Enhanced Signal Tracing with Boundary Detection & Constant Handling**")
    
    # Sidebar for file upload
    with st.sidebar:
        st.header("📁 Load Netlist")
        
        # File upload
        uploaded_file = st.file_uploader("Upload Verilog Netlist (.v)", type=['v'])
        
        if uploaded_file:
            content = uploaded_file.read().decode('utf-8')
            st.session_state['netlist_content'] = content
            st.session_state['filename'] = uploaded_file.name
            st.success(f"✅ Loaded: {uploaded_file.name}")
        
        # Or use default netlist
        elif st.button("🔄 Load Default Netlist"):
            try:
                with open('../netlist.v', 'r') as f:
                    content = f.read()
                st.session_state['netlist_content'] = content
                st.session_state['filename'] = 'netlist.v'
                st.success("✅ Loaded default netlist.v")
            except FileNotFoundError:
                st.error("❌ Default netlist.v not found")
    
    # Main content
    if 'netlist_content' not in st.session_state:
        st.info("👈 Please load a Verilog netlist file from the sidebar")
        st.markdown("""
        ### Features:
        - ✅ **Proper Boundary Detection**: Primary inputs can't be backtracked, primary outputs can't be forward tracked
        - ✅ **Constant Signal Detection**: Identifies signals tied to 1'b0 or 1'b1
        - ✅ **Enhanced Signal Analysis**: Comprehensive connectivity information
        - ✅ **Design Statistics**: Overview of design structure and issues
        """)
        return
    
    # Parse the netlist
    if 'parser' not in st.session_state or st.sidebar.button("🔄 Reparse Netlist"):
        with st.spinner("Parsing netlist..."):
            parser = EnhancedVerilogParser(st.session_state['netlist_content'])
            parser.parse()
            st.session_state['parser'] = parser
        st.success("✅ Netlist parsed successfully!")
    
    parser = st.session_state['parser']
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Design Overview",
        "🔍 Signal Tracing", 
        "⚡ Constant Signals",
        "🔗 Connectivity Analysis",
        "📋 Design Issues"
    ])
    
    # Tab 1: Design Overview
    with tab1:
        st.header("📊 Design Statistics")
        
        stats = parser.get_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Module", stats['module_name'])
            st.metric("Primary Inputs", stats['primary_inputs'])
        with col2:
            st.metric("Primary Outputs", stats['primary_outputs'])
            st.metric("Internal Signals", stats['internal_signals'])
        with col3:
            st.metric("Total Gates", stats['total_gates'])
            st.metric("Tied to 0", stats['tied_to_zero'])
        with col4:
            st.metric("Tied to 1", stats['tied_to_one'])
            st.metric("Floating Signals", stats['floating_signals'], 
                     delta="⚠️" if stats['floating_signals'] > 0 else None)
        
        # Show primary ports
        st.subheader("🔌 Primary Ports")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Primary Inputs:**")
            if parser.primary_inputs:
                for inp in sorted(parser.primary_inputs):
                    st.markdown(f"- `{inp}`")
            else:
                st.info("No primary inputs found")
        
        with col2:
            st.markdown("**Primary Outputs:**")
            if parser.primary_outputs:
                for out in sorted(parser.primary_outputs):
                    st.markdown(f"- `{out}`")
            else:
                st.info("No primary outputs found")
    
    # Tab 2: Signal Tracing
    with tab2:
        st.header("🔍 Signal Tracing")
        
        # Signal search
        signal_name = st.text_input("Enter Signal Name:", placeholder="e.g., data_out, clk, reset")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⬅️ Backtrack (Find Drivers)", use_container_width=True):
                if signal_name:
                    result = parser.backtrack_signal(signal_name)
                    
                    if result['status'] == 'BOUNDARY':
                        st.warning(f"🚫 **{result['message']}**")
                        st.info("Primary inputs are the starting points of the design and have no drivers.")
                    
                    elif result['status'] == 'NOT_FOUND':
                        st.error(result['message'])
                    
                    elif result['status'] == 'TIED':
                        st.info(f"🔌 **{result['message']}**")
                        for tied_port, value in result['tied_connections']:
                            st.markdown(f"- `{tied_port}` → **{value}**")
                    
                    elif result['status'] == 'FLOATING':
                        st.warning(result['message'])
                    
                    elif result['status'] == 'SUCCESS':
                        st.success(f"✅ Found {len(result['drivers'])} driver(s) for `{signal_name}`")
                        st.markdown(f"**Signal Type:** `{result['signal_type']}`")
                        
                        for idx, driver in enumerate(result['drivers'], 1):
                            with st.expander(f"Driver {idx}: {driver['gate']} ({driver['type']})", expanded=True):
                                st.markdown(f"**Gate Type:** `{driver['type']}`")
                                st.markdown(f"**Inputs:** {', '.join([f'`{i}`' for i in driver['inputs']])}")
                                st.markdown(f"**Outputs:** {', '.join([f'`{o}`' for o in driver['outputs']])}")
        
        with col2:
            if st.button("➡️ Forward Track (Find Readers)", use_container_width=True):
                if signal_name:
                    result = parser.forward_track_signal(signal_name)
                    
                    if result['status'] == 'BOUNDARY':
                        st.warning(f"🚫 **{result['message']}**")
                        st.info("Primary outputs are the endpoints of the design and have no readers.")
                    
                    elif result['status'] == 'NOT_FOUND':
                        st.error(result['message'])
                    
                    elif result['status'] == 'UNLOADED':
                        st.warning(result['message'])
                    
                    elif result['status'] == 'SUCCESS':
                        st.success(f"✅ Found {len(result['readers'])} reader(s) for `{signal_name}`")
                        st.markdown(f"**Signal Type:** `{result['signal_type']}`")
                        
                        for idx, reader in enumerate(result['readers'], 1):
                            with st.expander(f"Reader {idx}: {reader['gate']} ({reader['type']})", expanded=True):
                                st.markdown(f"**Gate Type:** `{reader['type']}`")
                                st.markdown(f"**Inputs:** {', '.join([f'`{i}`' for i in reader['inputs']])}")
                                st.markdown(f"**Outputs:** {', '.join([f'`{o}`' for o in reader['outputs']])}")
    
    # Tab 3: Constant Signals
    with tab3:
        st.header("⚡ Constant Signals (Tied to 0/1)")
        
        tied_signals = parser.get_all_tied_signals()
        
        if not tied_signals:
            st.success("✅ No tied signals found in the design")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🔌 Tied to 0 (GND)")
                if '0' in tied_signals:
                    st.info(f"Found {len(tied_signals['0'])} connections tied to 0")
                    for tied_port in tied_signals['0']:
                        st.markdown(f"- `{tied_port}`")
                else:
                    st.success("No signals tied to 0")
            
            with col2:
                st.subheader("🔌 Tied to 1 (VDD)")
                if '1' in tied_signals:
                    st.info(f"Found {len(tied_signals['1'])} connections tied to 1")
                    for tied_port in tied_signals['1']:
                        st.markdown(f"- `{tied_port}`")
                else:
                    st.success("No signals tied to 1")
            
            # Export option
            if st.button("📥 Export Tied Signals Report"):
                report = "# Tied Signals Report\n\n"
                report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                report += f"Netlist: {st.session_state.get('filename', 'Unknown')}\n\n"
                
                if '0' in tied_signals:
                    report += f"## Tied to 0 ({len(tied_signals['0'])} connections)\n\n"
                    for port in tied_signals['0']:
                        report += f"- {port}\n"
                    report += "\n"
                
                if '1' in tied_signals:
                    report += f"## Tied to 1 ({len(tied_signals['1'])} connections)\n\n"
                    for port in tied_signals['1']:
                        report += f"- {port}\n"
                
                st.download_button(
                    label="Download Report",
                    data=report,
                    file_name="tied_signals_report.md",
                    mime="text/markdown"
                )
    
    # Tab 4: Connectivity Analysis
    with tab4:
        st.header("🔗 Full Connectivity Analysis")
        
        signal_for_analysis = st.text_input("Signal to Analyze:", placeholder="Enter signal name")
        
        if st.button("🔍 Analyze Connectivity", use_container_width=True):
            if signal_for_analysis:
                conn_info = parser.get_full_connectivity(signal_for_analysis)
                
                st.subheader(f"Analysis: `{conn_info['signal']}`")
                
                # Signal type
                type_color = {
                    'PRIMARY_INPUT': '🟢',
                    'PRIMARY_OUTPUT': '🔴',
                    'INTERNAL': '🔵',
                    'UNKNOWN': '⚪'
                }
                
                st.markdown(f"**Type:** {type_color.get(conn_info['type'], '⚪')} `{conn_info['type']}`")
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Drivers", conn_info['driver_count'])
                with col2:
                    st.metric("Readers", conn_info['reader_count'])
                with col3:
                    fanout_health = "🟢" if conn_info['reader_count'] < 10 else "🟡" if conn_info['reader_count'] < 30 else "🔴"
                    st.metric("Fanout", conn_info['reader_count'], delta=fanout_health)
                
                # Boundary warnings
                if conn_info['is_primary_input']:
                    st.warning("⚠️ This is a PRIMARY INPUT - cannot be backtracked")
                if conn_info['is_primary_output']:
                    st.warning("⚠️ This is a PRIMARY OUTPUT - cannot be forward tracked")
                
                # Drivers
                if conn_info['drivers']:
                    st.markdown("### ⬅️ Drivers")
                    for driver in conn_info['drivers']:
                        gate_info = parser.gates.get(driver, {})
                        st.markdown(f"- `{driver}` ({gate_info.get('type', 'Unknown')})")
                else:
                    if conn_info['is_primary_input']:
                        st.info("No drivers (Primary Input)")
                    else:
                        st.warning("⚠️ No drivers found (Floating signal)")
                
                # Readers
                if conn_info['readers']:
                    st.markdown("### ➡️ Readers")
                    for reader in conn_info['readers']:
                        gate_info = parser.gates.get(reader, {})
                        st.markdown(f"- `{reader}` ({gate_info.get('type', 'Unknown')})")
                else:
                    if conn_info['is_primary_output']:
                        st.info("No readers (Primary Output)")
                    else:
                        st.warning("⚠️ No readers found (Unused signal)")
                
                # Tied connections
                if conn_info['tied_connections']:
                    st.markdown("### 🔌 Tied Connections")
                    for tied_port, value in conn_info['tied_connections']:
                        st.markdown(f"- `{tied_port}` → **{value}**")
    
    # Tab 5: Design Issues
    with tab5:
        st.header("📋 Design Issues & Warnings")
        
        stats = parser.get_statistics()
        
        issues_found = False
        
        # Floating signals
        if stats['floating_signals'] > 0:
            issues_found = True
            st.warning(f"⚠️ **{stats['floating_signals']} Floating Signals Found**")
            st.markdown("Floating signals have no drivers and may cause simulation issues.")
            
            with st.expander("View Floating Signals"):
                all_signals = parser.internal_signals | parser.primary_outputs
                floating = [sig for sig in all_signals 
                           if sig not in parser.signal_drivers or len(parser.signal_drivers[sig]) == 0]
                for sig in floating[:50]:  # Limit to 50
                    st.markdown(f"- `{sig}`")
                if len(floating) > 50:
                    st.info(f"... and {len(floating) - 50} more")
        
        # Unloaded signals
        if stats['unloaded_signals'] > 0:
            issues_found = True
            st.info(f"ℹ️ **{stats['unloaded_signals']} Unloaded Signals Found**")
            st.markdown("Unloaded signals have no readers (might be intentional or dead code).")
            
            with st.expander("View Unloaded Signals"):
                all_signals = parser.internal_signals | parser.primary_inputs
                unloaded = [sig for sig in all_signals 
                           if sig not in parser.signal_readers or len(parser.signal_readers[sig]) == 0]
                for sig in unloaded[:50]:  # Limit to 50
                    st.markdown(f"- `{sig}`")
                if len(unloaded) > 50:
                    st.info(f"... and {len(unloaded) - 50} more")
        
        # Tied signals summary
        if stats['tied_to_zero'] + stats['tied_to_one'] > 0:
            st.success(f"✅ **{stats['tied_to_zero'] + stats['tied_to_one']} Constant Connections Found**")
            st.markdown(f"- Tied to 0: {stats['tied_to_zero']}")
            st.markdown(f"- Tied to 1: {stats['tied_to_one']}")
            st.markdown("See 'Constant Signals' tab for details")
        
        if not issues_found and stats['tied_to_zero'] + stats['tied_to_one'] == 0:
            st.success("✅ No major issues detected in the design!")


if __name__ == "__main__":
    main()
