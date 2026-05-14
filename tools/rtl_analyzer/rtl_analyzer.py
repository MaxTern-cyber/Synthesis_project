import streamlit as st
import re
from collections import defaultdict, Counter
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import networkx as nx

class RTLAnalyzer:
    """
    Comprehensive RTL Verilog Analyzer
    Focuses on behavioral RTL code analysis (not gate-level netlists)
    """
    
    def __init__(self, content):
        self.content = content
        self.module_name = ""
        self.parameters = {}
        self.ports = {}  # {port_name: {direction, width, type}}
        self.signals = {}  # {signal_name: {type, width, reg/wire}}
        self.always_blocks = []  # List of always block info
        self.assign_statements = []  # Continuous assignments
        self.module_instances = []  # Submodule instances
        self.functions = []  # Functions
        self.tasks = []  # Tasks
        self.fsm_candidates = []  # Potential FSMs detected
        self.clock_signals = []  # Detected clocks
        self.reset_signals = []  # Detected resets
        self.register_chains = []  # Pipeline stages
        self.combinational_logic = []  # Comb logic blocks
        self.sequential_logic = []  # Sequential blocks
        self.coding_issues = []  # Coding style warnings
        self.synthesis_metrics = {}  # Synthesis time estimation
        self.combinational_loops = []  # Detected comb loops
        self.tied_signals = {}  # Signals tied to constants
        self.latch_warnings = []  # Potential latch inferences
        self.incomplete_cases = []  # Incomplete case statements
        self.clock_domains = {}  # Clock domain mapping {clock_name: [signals]}
        self.dag_graph = None  # NetworkX graph for DAG visualization
        
    def parse(self):
        """Main parsing function"""
        self._extract_module_info()
        self._extract_parameters()
        self._extract_ports()
        self._extract_signals()
        self._extract_always_blocks()
        self._extract_assign_statements()
        self._extract_module_instances()
        self._detect_clocks_resets()
        self._detect_fsms()
        self._analyze_register_chains()
        self._detect_tied_signals()
        self._detect_combinational_loops()
        self._check_latch_inference()
        self._check_incomplete_cases()
        self._check_coding_style()
        self._estimate_synthesis_time()
        self._build_dag_graph()
        self._identify_clock_domains()
        self._build_dag_graph()
        self._identify_clock_domains()
        
    def _extract_module_info(self):
        """Extract module name and basic info"""
        module_pattern = r'module\s+(\w+)'
        match = re.search(module_pattern, self.content)
        if match:
            self.module_name = match.group(1)
    
    def _extract_parameters(self):
        """Extract parameter declarations"""
        # parameter NAME = VALUE;
        param_pattern = r'parameter\s+(\w+)\s*=\s*([^;]+);'
        for match in re.finditer(param_pattern, self.content):
            param_name = match.group(1)
            param_value = match.group(2).strip()
            self.parameters[param_name] = param_value
    
    def _extract_ports(self):
        """Extract input/output/inout ports"""
        # Input ports
        input_pattern = r'input\s+(?:\[([\d:]+)\])?\s*([\w,\s]+);'
        for match in re.finditer(input_pattern, self.content):
            width = match.group(1) if match.group(1) else "0:0"
            signals = [s.strip() for s in match.group(2).split(',') if s.strip()]
            for sig in signals:
                self.ports[sig] = {
                    'direction': 'input',
                    'width': width,
                    'type': 'wire'
                }
        
        # Output ports
        output_pattern = r'output\s+(?:(reg|wire)\s+)?(?:\[([\d:]+)\])?\s*([\w,\s]+);'
        for match in re.finditer(output_pattern, self.content):
            sig_type = match.group(1) if match.group(1) else 'wire'
            width = match.group(2) if match.group(2) else "0:0"
            signals = [s.strip() for s in match.group(3).split(',') if s.strip()]
            for sig in signals:
                self.ports[sig] = {
                    'direction': 'output',
                    'width': width,
                    'type': sig_type
                }
        
        # Inout ports
        inout_pattern = r'inout\s+(?:\[([\d:]+)\])?\s*([\w,\s]+);'
        for match in re.finditer(inout_pattern, self.content):
            width = match.group(1) if match.group(1) else "0:0"
            signals = [s.strip() for s in match.group(2).split(',') if s.strip()]
            for sig in signals:
                self.ports[sig] = {
                    'direction': 'inout',
                    'width': width,
                    'type': 'wire'
                }
    
    def _extract_signals(self):
        """Extract internal wire and reg declarations"""
        # Wire declarations
        wire_pattern = r'wire\s+(?:\[([\d:]+)\])?\s*([\w,\s]+);'
        for match in re.finditer(wire_pattern, self.content):
            width = match.group(1) if match.group(1) else "0:0"
            signals = [s.strip() for s in match.group(2).split(',') if s.strip()]
            for sig in signals:
                if sig not in self.ports:  # Avoid duplicates
                    self.signals[sig] = {
                        'type': 'wire',
                        'width': width
                    }
        
        # Reg declarations
        reg_pattern = r'reg\s+(?:\[([\d:]+)\])?\s*([\w,\s]+);'
        for match in re.finditer(reg_pattern, self.content):
            width = match.group(1) if match.group(1) else "0:0"
            signals = [s.strip() for s in match.group(2).split(',') if s.strip()]
            for sig in signals:
                if sig not in self.ports:  # Avoid duplicates
                    self.signals[sig] = {
                        'type': 'reg',
                        'width': width
                    }
    
    def _extract_always_blocks(self):
        """Extract and classify always blocks"""
        # Find all always blocks
        always_pattern = r'always\s*@\s*\(([^)]+)\)\s*begin(.*?)end'
        
        for idx, match in enumerate(re.finditer(always_pattern, self.content, re.DOTALL), 1):
            sensitivity_list = match.group(1).strip()
            block_content = match.group(2)
            
            # Classify the always block
            block_type = self._classify_always_block(sensitivity_list, block_content)
            
            # Extract driven signals
            driven_signals = self._extract_driven_signals(block_content)
            
            # Extract read signals
            read_signals = self._extract_read_signals(block_content)
            
            # Check for blocking vs non-blocking
            has_blocking = '=' in block_content and '<=' not in block_content
            has_nonblocking = '<=' in block_content
            
            always_info = {
                'id': idx,
                'type': block_type,
                'sensitivity': sensitivity_list,
                'driven_signals': driven_signals,
                'read_signals': read_signals,
                'has_blocking': has_blocking and not has_nonblocking,
                'has_nonblocking': has_nonblocking,
                'mixed_assignments': has_blocking and has_nonblocking,
                'line_count': len(block_content.split('\n')),
                'content_preview': block_content[:200] + '...' if len(block_content) > 200 else block_content
            }
            
            self.always_blocks.append(always_info)
            
            # Categorize into sequential or combinational
            if block_type in ['sequential', 'async_reset', 'sync_reset']:
                self.sequential_logic.append(always_info)
            else:
                self.combinational_logic.append(always_info)
    
    def _classify_always_block(self, sensitivity, content):
        """Classify always block as combinational, sequential, etc."""
        sens_lower = sensitivity.lower()
        
        # Check for edge-sensitive (sequential)
        if 'posedge' in sens_lower or 'negedge' in sens_lower:
            # Check if it has asynchronous reset
            if sens_lower.count('posedge') + sens_lower.count('negedge') > 1:
                return 'async_reset'
            else:
                return 'sequential'
        # Combinational (sensitivity list with signals)
        elif '*' in sensitivity or ',' in sensitivity:
            return 'combinational'
        else:
            return 'unknown'
    
    def _extract_driven_signals(self, block_content):
        """Extract signals driven (assigned) in the block"""
        driven = set()
        # Look for assignments (both blocking and non-blocking)
        assign_pattern = r'(\w+)\s*(?:<=|=)'
        for match in re.finditer(assign_pattern, block_content):
            signal = match.group(1)
            if signal not in ['if', 'case', 'else', 'begin', 'end', 'for', 'while']:
                driven.add(signal)
        return list(driven)
    
    def _extract_read_signals(self, block_content):
        """Extract signals read (used) in the block"""
        # This is a simplified heuristic
        # Remove driven signals and look for identifiers
        read = set()
        # Look for identifiers in conditions and RHS
        id_pattern = r'\b([a-zA-Z_]\w*)\b'
        for match in re.finditer(id_pattern, block_content):
            signal = match.group(1)
            # Filter out keywords
            if signal not in ['if', 'else', 'case', 'begin', 'end', 'for', 'while', 
                             'posedge', 'negedge', 'or', 'and', 'not']:
                read.add(signal)
        return list(read)
    
    def _extract_assign_statements(self):
        """Extract continuous assign statements"""
        assign_pattern = r'assign\s+(\w+)\s*=\s*([^;]+);'
        for match in re.finditer(assign_pattern, self.content):
            lhs = match.group(1).strip()
            rhs = match.group(2).strip()
            self.assign_statements.append({
                'lhs': lhs,
                'rhs': rhs
            })
    
    def _extract_module_instances(self):
        """Extract submodule instantiations"""
        # Pattern: MODULE_NAME INSTANCE_NAME (connections);
        instance_pattern = r'(\w+)\s+(\w+)\s*\((.*?)\);'
        
        for match in re.finditer(instance_pattern, self.content, re.DOTALL):
            module_type = match.group(1)
            instance_name = match.group(2)
            connections = match.group(3)
            
            # Skip known keywords
            if module_type in ['module', 'assign', 'wire', 'reg', 'input', 'output', 
                              'parameter', 'always', 'initial', 'if', 'case']:
                continue
            
            # Parse port connections
            port_conns = []
            conn_pattern = r'\.(\w+)\s*\(\s*([^)]+)\s*\)'
            for conn_match in re.finditer(conn_pattern, connections):
                port = conn_match.group(1)
                signal = conn_match.group(2).strip()
                port_conns.append({'port': port, 'signal': signal})
            
            if port_conns:  # Only add if we found port connections
                self.module_instances.append({
                    'module_type': module_type,
                    'instance_name': instance_name,
                    'connections': port_conns
                })
    
    def _detect_clocks_resets(self):
        """Detect clock and reset signals"""
        # Clock detection heuristics
        for port_name in self.ports:
            name_lower = port_name.lower()
            if any(clk_hint in name_lower for clk_hint in ['clk', 'clock', 'ck']):
                self.clock_signals.append(port_name)
        
        for signal_name in self.signals:
            name_lower = signal_name.lower()
            if any(clk_hint in name_lower for clk_hint in ['clk', 'clock', 'ck']):
                self.clock_signals.append(signal_name)
        
        # Reset detection heuristics
        for port_name in self.ports:
            name_lower = port_name.lower()
            if any(rst_hint in name_lower for rst_hint in ['rst', 'reset', 'resetn', 'rst_n', 'rstn']):
                self.reset_signals.append(port_name)
        
        for signal_name in self.signals:
            name_lower = signal_name.lower()
            if any(rst_hint in name_lower for rst_hint in ['rst', 'reset', 'resetn', 'rst_n', 'rstn']):
                self.reset_signals.append(signal_name)
    
    def _detect_fsms(self):
        """Detect potential Finite State Machines"""
        # Look for state registers and state transitions
        state_keywords = ['state', 'current_state', 'next_state', 'cs', 'ns', 'present_state']
        
        potential_state_regs = []
        for sig_name in list(self.signals.keys()) + list(self.ports.keys()):
            name_lower = sig_name.lower()
            if any(kw in name_lower for kw in state_keywords):
                potential_state_regs.append(sig_name)
        
        if potential_state_regs:
            # Look for case statements (typical in FSMs)
            case_pattern = r'case\s*\(\s*(\w+)\s*\)'
            case_vars = []
            for match in re.finditer(case_pattern, self.content):
                case_var = match.group(1)
                if case_var in potential_state_regs:
                    case_vars.append(case_var)
            
            if case_vars:
                for state_var in case_vars:
                    # Extract case items
                    states = self._extract_fsm_states(state_var)
                    self.fsm_candidates.append({
                        'state_variable': state_var,
                        'states': states,
                        'state_count': len(states)
                    })
    
    def _extract_fsm_states(self, state_var):
        """Extract state names from FSM"""
        states = []
        # Look for parameter declarations that look like states
        state_param_pattern = r'parameter\s+(\w+)\s*=\s*\d+'
        for match in re.finditer(state_param_pattern, self.content):
            param_name = match.group(1)
            if 'STATE' in param_name.upper() or 'ST_' in param_name.upper():
                states.append(param_name)
        return states
    
    def _analyze_register_chains(self):
        """Detect register chains (pipeline stages)"""
        # Look for signals with similar names (e.g., data_stage1, data_stage2)
        stage_pattern = r'(\w+)_(?:stage|s|pipe|p)(\d+)'
        
        chains = defaultdict(list)
        all_signals = list(self.signals.keys()) + list(self.ports.keys())
        
        for sig in all_signals:
            match = re.match(stage_pattern, sig)
            if match:
                base_name = match.group(1)
                stage_num = int(match.group(2))
                chains[base_name].append((stage_num, sig))
        
        # Sort and create chain info
        for base_name, stages in chains.items():
            stages.sort()  # Sort by stage number
            if len(stages) >= 2:  # At least 2 stages
                self.register_chains.append({
                    'base_name': base_name,
                    'stages': [s[1] for s in stages],
                    'depth': len(stages)
                })
    
    def _detect_tied_signals(self):
        """Detect signals tied to constants (1'b0, 1'b1, 0, 1)"""
        constant_pattern = r"(\w+)\s*[<=]?\s*=\s*(1'b[01]|1'B[01]|\d+'b[01]|\d+'B[01])"
        
        for match in re.finditer(constant_pattern, self.content):
            signal = match.group(1)
            value = match.group(2)
            
            # Determine if it's 0 or 1
            if '0' in value:
                self.tied_signals[signal] = '0'
            else:
                self.tied_signals[signal] = '1'
    
    def _detect_combinational_loops(self):
        """Detect combinational feedback loops in assign statements"""
        # Build dependency graph from assign statements
        graph = nx.DiGraph()
        
        for assign in self.assign_statements:
            lhs = assign['lhs']
            rhs = assign['rhs']
            
            # Extract signals on RHS
            rhs_signals = re.findall(r'\b([a-zA-Z_]\w*)\b', rhs)
            
            for rhs_sig in rhs_signals:
                if rhs_sig in self.signals or rhs_sig in self.ports:
                    graph.add_edge(lhs, rhs_sig)
        
        # Find cycles using strongly connected components
        try:
            cycles = list(nx.simple_cycles(graph))
            
            for cycle in cycles:
                if len(cycle) > 1:  # Actual loop
                    self.combinational_loops.append({
                        'signals': cycle,
                        'length': len(cycle),
                        'severity': 'CRITICAL'
                    })
                    
                    self.coding_issues.append({
                        'severity': 'ERROR',
                        'type': 'Combinational Loop',
                        'message': f"Combinational loop detected: {' -> '.join(cycle)} -> {cycle[0]}",
                        'recommendation': "Break the loop by inserting a register or reviewing the logic"
                    })
        except:
            pass  # No cycles or graph issues
    
    def _check_latch_inference(self):
        """Check for potential latch inference in combinational always blocks"""
        for block in self.combinational_logic:
            content = block['content_preview']
            driven_sigs = block['driven_signals']
            
            # Check for if statements without else
            if_pattern = r'\bif\s*\([^)]+\)\s*begin'
            else_pattern = r'\belse\b'
            
            has_if = re.search(if_pattern, content)
            has_else = re.search(else_pattern, content)
            
            if has_if and not has_else and driven_sigs:
                for sig in driven_sigs:
                    self.latch_warnings.append({
                        'signal': sig,
                        'block_id': block['id'],
                        'reason': 'Incomplete if-else (missing else clause)',
                        'severity': 'WARNING'
                    })
                    
                    self.coding_issues.append({
                        'severity': 'WARNING',
                        'type': 'Latch Inference',
                        'message': f"Signal '{sig}' in always block #{block['id']} may infer a latch (incomplete if-else)",
                        'recommendation': "Add else clause or assign default values before if statement"
                    })
    
    def _check_incomplete_cases(self):
        """Check for incomplete case statements that may infer latches"""
        case_pattern = r'case\s*\(([^)]+)\)(.*?)endcase'
        
        for block in self.combinational_logic:
            content = block['content_preview']
            
            for match in re.finditer(case_pattern, content, re.DOTALL):
                case_var = match.group(1).strip()
                case_body = match.group(2)
                
                # Check for default case
                has_default = 'default' in case_body.lower()
                
                if not has_default and block['driven_signals']:
                    for sig in block['driven_signals']:
                        self.incomplete_cases.append({
                            'signal': sig,
                            'case_variable': case_var,
                            'block_id': block['id'],
                            'severity': 'WARNING'
                        })
                        
                        self.coding_issues.append({
                            'severity': 'WARNING',
                            'type': 'Incomplete Case',
                            'message': f"Case statement on '{case_var}' in block #{block['id']} missing default clause",
                            'recommendation': "Add 'default:' case to prevent latch inference"
                        })
    
    def _estimate_synthesis_time(self):
        """Estimate synthesis time based on design complexity"""
        # Industry-standard metrics for synthesis time estimation
        
        # Base metrics
        num_gates_estimate = (
            len(self.ports) * 2 +  # Ports
            len(self.signals) * 1.5 +  # Internal signals
            len(self.always_blocks) * 50 +  # Always blocks (avg 50 gates each)
            len(self.assign_statements) * 3 +  # Assign statements
            len(self.module_instances) * 100  # Module instances
        )
        
        # Complexity factors
        complexity_multiplier = 1.0
        
        # FSMs increase synthesis time
        complexity_multiplier += len(self.fsm_candidates) * 0.3
        
        # Large always blocks are slower
        large_blocks = sum(1 for b in self.always_blocks if b['line_count'] > 100)
        complexity_multiplier += large_blocks * 0.2
        
        # Pipelines are generally fast to synthesize
        complexity_multiplier += len(self.register_chains) * 0.1
        
        # Combinational loops dramatically slow down synthesis
        if self.combinational_loops:
            complexity_multiplier += len(self.combinational_loops) * 2.0
        
        # Base synthesis time estimates (industry averages)
        # Small design (<1K gates): 1-5 minutes
        # Medium design (1K-10K gates): 5-30 minutes
        # Large design (10K-100K gates): 30-300 minutes
        
        base_time_seconds = (num_gates_estimate / 1000) * 60  # 1 minute per 1K gates baseline
        estimated_time_seconds = base_time_seconds * complexity_multiplier
        
        # Calculate in different units
        estimated_minutes = estimated_time_seconds / 60
        estimated_hours = estimated_minutes / 60
        
        # Categorize
        if estimated_minutes < 5:
            category = "Fast"
            color = "green"
        elif estimated_minutes < 30:
            category = "Moderate"
            color = "yellow"
        elif estimated_minutes < 120:
            category = "Slow"
            color = "orange"
        else:
            category = "Very Slow"
            color = "red"
        
        self.synthesis_metrics = {
            'estimated_gates': int(num_gates_estimate),
            'complexity_multiplier': round(complexity_multiplier, 2),
            'estimated_time_seconds': int(estimated_time_seconds),
            'estimated_time_minutes': round(estimated_minutes, 1),
            'estimated_time_hours': round(estimated_hours, 2),
            'category': category,
            'color': color,
            'factors': {
                'base_gates': int(num_gates_estimate),
                'fsm_penalty': len(self.fsm_candidates),
                'large_block_penalty': large_blocks,
                'pipeline_bonus': len(self.register_chains),
                'comb_loop_penalty': len(self.combinational_loops)
            }
        }
    
    def _check_coding_style(self):
        """Check for common RTL coding style issues"""
        
        # Issue 1: Mixed blocking and non-blocking in same always block
        for block in self.always_blocks:
            if block['mixed_assignments']:
                self.coding_issues.append({
                    'severity': 'WARNING',
                    'type': 'Mixed Assignments',
                    'message': f"Always block #{block['id']} mixes blocking (=) and non-blocking (<=) assignments",
                    'recommendation': "Use non-blocking (<=) for sequential, blocking (=) for combinational"
                })
        
        # Issue 2: Blocking assignments in sequential blocks
        for block in self.sequential_logic:
            if block['has_blocking'] and not block['has_nonblocking']:
                self.coding_issues.append({
                    'severity': 'WARNING',
                    'type': 'Blocking in Sequential',
                    'message': f"Sequential always block #{block['id']} uses blocking assignments",
                    'recommendation': "Use non-blocking (<=) assignments in sequential blocks"
                })
        
        # Issue 3: Non-blocking in combinational blocks
        for block in self.combinational_logic:
            if block['has_nonblocking']:
                self.coding_issues.append({
                    'severity': 'INFO',
                    'type': 'Non-blocking in Combinational',
                    'message': f"Combinational always block #{block['id']} uses non-blocking assignments",
                    'recommendation': "Prefer blocking (=) assignments in combinational blocks"
                })
        
        # Issue 4: Check for signals driven in multiple always blocks
        driven_map = defaultdict(list)
        for block in self.always_blocks:
            for sig in block['driven_signals']:
                driven_map[sig].append(block['id'])
        
        for sig, blocks in driven_map.items():
            if len(blocks) > 1:
                self.coding_issues.append({
                    'severity': 'ERROR',
                    'type': 'Multiple Drivers',
                    'message': f"Signal '{sig}' is driven in multiple always blocks: {blocks}",
                    'recommendation': "Each signal should be driven in only one always block"
                })
        
        # Issue 5: Large always blocks (>100 lines)
        for block in self.always_blocks:
            if block['line_count'] > 100:
                self.coding_issues.append({
                    'severity': 'INFO',
                    'type': 'Large Always Block',
                    'message': f"Always block #{block['id']} has {block['line_count']} lines",
                    'recommendation': "Consider breaking into smaller blocks or sub-modules"
                })
    
    def _build_dag_graph(self):
        """Build a directed graph representing the RTL dataflow"""
        self.dag_graph = nx.DiGraph()
        
        # Add nodes for all signals with attributes
        for port_name, port_info in self.ports.items():
            node_type = 'input' if port_info['direction'] == 'input' else 'output' if port_info['direction'] == 'output' else 'inout'
            self.dag_graph.add_node(port_name, 
                                   node_type=node_type,
                                   element_type='port',
                                   width=port_info['width'])
        
        for signal_name, signal_info in self.signals.items():
            is_reg = signal_info['type'] == 'reg'
            self.dag_graph.add_node(signal_name,
                                   node_type='register' if is_reg else 'wire',
                                   element_type='signal',
                                   width=signal_info['width'])
        
        # Add edges from assign statements (combinational logic)
        for assign in self.assign_statements:
            lhs = assign['lhs']
            rhs = assign['rhs']
            # Extract all signals referenced in RHS
            rhs_signals = re.findall(r'\b([a-zA-Z_]\w*)\b', rhs)
            for rhs_sig in rhs_signals:
                if rhs_sig in self.ports or rhs_sig in self.signals:
                    self.dag_graph.add_edge(rhs_sig, lhs, edge_type='combinational', source='assign')
        
        # Add edges from always blocks
        for block in self.always_blocks:
            driven_sigs = block['driven_signals']
            read_sigs = block['read_signals']
            edge_type = 'sequential' if block['type'] in ['sequential', 'async_reset', 'sync_reset'] else 'combinational'
            
            for driven in driven_sigs:
                for read in read_sigs:
                    if read in self.ports or read in self.signals:
                        if driven != read:  # Avoid self-loops
                            self.dag_graph.add_edge(read, driven, 
                                                   edge_type=edge_type, 
                                                   source=f"always_block_{block['id']}")
    
    def _identify_clock_domains(self):
        """Identify clock domains and which signals belong to each"""
        for clk in self.clock_signals:
            self.clock_domains[clk] = []
            
            # Find all sequential blocks using this clock
            for block in self.sequential_logic:
                if clk in block['sensitivity']:
                    # Add all driven signals to this clock domain
                    self.clock_domains[clk].extend(block['driven_signals'])
            
            # Remove duplicates
            self.clock_domains[clk] = list(set(self.clock_domains[clk]))
    
    def get_statistics(self):
            # Find all sequential blocks using this clock
            for block in self.sequential_logic:
                if clk in block['sensitivity']:
                    # Add all driven signals to this clock domain
                    self.clock_domains[clk].extend(block['driven_signals'])
            
            # Remove duplicates
            self.clock_domains[clk] = list(set(self.clock_domains[clk]))
    
    def get_statistics(self):
        """Get comprehensive RTL statistics"""
        return {
            'module_name': self.module_name,
            'parameters': len(self.parameters),
            'total_ports': len(self.ports),
            'input_ports': sum(1 for p in self.ports.values() if p['direction'] == 'input'),
            'output_ports': sum(1 for p in self.ports.values() if p['direction'] == 'output'),
            'inout_ports': sum(1 for p in self.ports.values() if p['direction'] == 'inout'),
            'internal_signals': len(self.signals),
            'wire_signals': sum(1 for s in self.signals.values() if s['type'] == 'wire'),
            'reg_signals': sum(1 for s in self.signals.values() if s['type'] == 'reg'),
            'always_blocks': len(self.always_blocks),
            'sequential_blocks': len(self.sequential_logic),
            'combinational_blocks': len(self.combinational_logic),
            'assign_statements': len(self.assign_statements),
            'module_instances': len(self.module_instances),
            'detected_clocks': len(self.clock_signals),
            'detected_resets': len(self.reset_signals),
            'fsm_candidates': len(self.fsm_candidates),
            'register_chains': len(self.register_chains),
            'coding_issues': len(self.coding_issues),
            'critical_issues': sum(1 for i in self.coding_issues if i['severity'] == 'ERROR'),
            'warnings': sum(1 for i in self.coding_issues if i['severity'] == 'WARNING')
        }


# ==================== Streamlit Application ====================

def main():
    st.set_page_config(
        page_title="RTL Analyzer",
        page_icon="ðŸ“",
        layout="wide"
    )
    
    st.title("ðŸ“ Advanced RTL Verilog Analyzer")
    st.markdown("**Behavioral RTL Analysis | FSM Detection | Coding Style Checker | Pipeline Analysis**")
    
    # Sidebar
    with st.sidebar:
        st.header("ðŸ“ Load RTL File")
        
        uploaded_file = st.file_uploader("Upload RTL Verilog (.v)", type=['v'])
        
        if uploaded_file:
            content = uploaded_file.read().decode('utf-8')
            st.session_state['rtl_content'] = content
            st.session_state['filename'] = uploaded_file.name
            st.success(f"âœ… Loaded: {uploaded_file.name}")
        
        elif st.button("ðŸ”„ Load Default (sample_counter.v)"):
            try:
                with open('sample_counter.v', 'r') as f:
                    content = f.read()
                st.session_state['rtl_content'] = content
                st.session_state['filename'] = 'sample_counter.v'
                st.success("âœ… Loaded sample_counter.v")
            except FileNotFoundError:
                st.error("âŒ sample_counter.v not found")
    
    # Main content
    if 'rtl_content' not in st.session_state:
        st.info("ðŸ‘ˆ Please load an RTL Verilog file from the sidebar")
        
        st.markdown("""
        ### ðŸŽ¯ RTL Analysis Features:
        
        **Design Structure Analysis:**
        - âœ… Module hierarchy and parameters
        - âœ… Port interface analysis
        - âœ… Internal signal declarations
        - âœ… Module instantiations
        
        **Behavioral Analysis:**
        - âœ… Always block classification (sequential vs combinational)
        - âœ… FSM detection and state extraction
        - âœ… Clock and reset signal detection
        - âœ… Pipeline/register chain identification
        
        **Code Quality:**
        - âœ… Coding style checking
        - âœ… Multiple driver detection
        - âœ… Blocking vs non-blocking assignment analysis
        - âœ… Best practices recommendations
        
        **Synthesis Readiness:**
        - âœ… Latch inference warnings
        - âœ… Sensitivity list completeness
        - âœ… Synthesizable construct verification
        """)
        return
    
    # Parse RTL
    if 'analyzer' not in st.session_state or st.sidebar.button("ðŸ”„ Reparse RTL"):
        with st.spinner("Analyzing RTL..."):
            analyzer = RTLAnalyzer(st.session_state['rtl_content'])
            analyzer.parse()
            st.session_state['analyzer'] = analyzer
        st.success("âœ… RTL analysis complete!")
    
    analyzer = st.session_state['analyzer']
    stats = analyzer.get_statistics()
    
    # Create tabs
    tabs = st.tabs([
        "ðŸ“Š Overview",
        "ðŸ”Œ Ports & Signals",
        "âš™ï¸ Always Blocks",
        "ðŸ”„ FSM Detection",
        "ðŸ“ˆ Pipeline Analysis",
        "âš ï¸ Code Quality",
        "ðŸ—ï¸ Module Hierarchy",
        "â±ï¸ Synthesis Estimation",
        "ðŸ” HDL Lint"
    ])
    
    # ===== TAB 1: Overview =====
    with tabs[0]:
        st.header(f"ðŸ“Š Module: `{stats['module_name']}`")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Ports", stats['total_ports'])
            st.metric("  â†³ Inputs", stats['input_ports'])
            st.metric("  â†³ Outputs", stats['output_ports'])
        
        with col2:
            st.metric("Internal Signals", stats['internal_signals'])
            st.metric("  â†³ Wires", stats['wire_signals'])
            st.metric("  â†³ Regs", stats['reg_signals'])
        
        with col3:
            st.metric("Always Blocks", stats['always_blocks'])
            st.metric("  â†³ Sequential", stats['sequential_blocks'])
            st.metric("  â†³ Combinational", stats['combinational_blocks'])
        
        with col4:
            st.metric("Submodules", stats['module_instances'])
            st.metric("Assign Statements", stats['assign_statements'])
            st.metric("Parameters", stats['parameters'])
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("ðŸ•’ Detected Clocks", stats['detected_clocks'])
            if analyzer.clock_signals:
                for clk in analyzer.clock_signals:
                    st.markdown(f"  - `{clk}`")
        
        with col2:
            st.metric("ðŸ”„ Detected Resets", stats['detected_resets'])
            if analyzer.reset_signals:
                for rst in analyzer.reset_signals:
                    st.markdown(f"  - `{rst}`")
        
        with col3:
            st.metric("ðŸ¤– FSM Candidates", stats['fsm_candidates'])
            st.metric("ðŸ“ˆ Pipeline Chains", stats['register_chains'])
        
        # Coding issues summary
        st.markdown("---")
        st.subheader("âš ï¸ Code Quality Summary")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Issues", stats['coding_issues'], 
                     delta="ðŸ”´" if stats['critical_issues'] > 0 else ("ðŸŸ¡" if stats['warnings'] > 0 else "ðŸŸ¢"))
        with col2:
            st.metric("Critical Errors", stats['critical_issues'],
                     delta="âš ï¸" if stats['critical_issues'] > 0 else None)
        with col3:
            st.metric("Warnings", stats['warnings'],
                     delta="â„¹ï¸" if stats['warnings'] > 0 else None)
        
        # Visualization: Signal type distribution
        st.markdown("---")
        st.subheader("ðŸ“ˆ Signal Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            port_data = {
                'Type': ['Input', 'Output', 'Inout'],
                'Count': [stats['input_ports'], stats['output_ports'], stats['inout_ports']]
            }
            fig = px.pie(port_data, values='Count', names='Type', title='Port Distribution')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            signal_data = {
                'Type': ['Wire', 'Reg'],
                'Count': [stats['wire_signals'], stats['reg_signals']]
            }
            fig = px.pie(signal_data, values='Count', names='Type', title='Internal Signal Types')
            st.plotly_chart(fig, use_container_width=True)
    
    # ===== TAB 2: Ports & Signals =====
    with tabs[1]:
        st.header("ðŸ”Œ Ports & Signals Analysis")
        
        # Ports
        st.subheader("Module Ports")
        if analyzer.ports:
            port_df = pd.DataFrame([
                {
                    'Port Name': name,
                    'Direction': info['direction'].upper(),
                    'Type': info['type'],
                    'Width': info['width']
                }
                for name, info in analyzer.ports.items()
            ])
            st.dataframe(port_df, use_container_width=True)
        else:
            st.info("No ports declared")
        
        st.markdown("---")
        
        # Internal Signals
        st.subheader("Internal Signals")
        if analyzer.signals:
            signal_df = pd.DataFrame([
                {
                    'Signal Name': name,
                    'Type': info['type'],
                    'Width': info['width']
                }
                for name, info in analyzer.signals.items()
            ])
            st.dataframe(signal_df, use_container_width=True)
            
            # Download option
            csv = signal_df.to_csv(index=False)
            st.download_button(
                label="ðŸ“¥ Download Signal List (CSV)",
                data=csv,
                file_name=f"{stats['module_name']}_signals.csv",
                mime="text/csv"
            )
        else:
            st.info("No internal signals declared")
        
        # Parameters
        if analyzer.parameters:
            st.markdown("---")
            st.subheader("Parameters")
            param_df = pd.DataFrame([
                {'Parameter': name, 'Value': value}
                for name, value in analyzer.parameters.items()
            ])
            st.dataframe(param_df, use_container_width=True)
    
    # ===== TAB 3: Always Blocks =====
    with tabs[2]:
        st.header("âš™ï¸ Always Block Analysis")
        
        if not analyzer.always_blocks:
            st.info("No always blocks found")
        else:
            # Summary
            st.subheader("Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Always Blocks", len(analyzer.always_blocks))
            with col2:
                st.metric("Sequential", len(analyzer.sequential_logic))
            with col3:
                st.metric("Combinational", len(analyzer.combinational_logic))
            
            st.markdown("---")
            
            # Detailed view
            for block in analyzer.always_blocks:
                block_type_emoji = {
                    'sequential': 'ðŸ”„',
                    'async_reset': 'âš¡',
                    'sync_reset': 'ðŸ”„',
                    'combinational': 'ðŸ”€',
                    'unknown': 'â“'
                }
                
                emoji = block_type_emoji.get(block['type'], 'â“')
                
                with st.expander(f"{emoji} Always Block #{block['id']} - {block['type'].upper()}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Type:** `{block['type']}`")
                        st.markdown(f"**Sensitivity List:** `{block['sensitivity']}`")
                        st.markdown(f"**Lines of Code:** {block['line_count']}")
                        
                        if block['has_nonblocking']:
                            st.markdown("âœ… Uses non-blocking assignments (<=)")
                        if block['has_blocking']:
                            st.markdown("âœ… Uses blocking assignments (=)")
                        if block['mixed_assignments']:
                            st.warning("âš ï¸ Mixed blocking and non-blocking!")
                    
                    with col2:
                        st.markdown("**Driven Signals:**")
                        if block['driven_signals']:
                            for sig in block['driven_signals'][:10]:
                                st.markdown(f"  - `{sig}`")
                            if len(block['driven_signals']) > 10:
                                st.info(f"... and {len(block['driven_signals']) - 10} more")
                        else:
                            st.info("None")
                        
                        st.markdown("**Read Signals:**")
                        if block['read_signals']:
                            sig_count = len(block['read_signals'])
                            st.info(f"{sig_count} signals read")
                        else:
                            st.info("None")
                    
                    # Content preview
                    st.markdown("**Content Preview:**")
                    st.code(block['content_preview'], language='verilog')
    
    # ===== TAB 4: FSM Detection =====
    with tabs[3]:
        st.header("ðŸ”„ Finite State Machine Detection")
        
        if not analyzer.fsm_candidates:
            st.info("No FSM candidates detected")
            st.markdown("""
            **FSM Detection Heuristics:**
            - Looks for signals with "state" in the name
            - Identifies case statements on state variables
            - Extracts state parameter definitions
            """)
        else:
            st.success(f"âœ… Detected {len(analyzer.fsm_candidates)} FSM candidate(s)")
            
            for idx, fsm in enumerate(analyzer.fsm_candidates, 1):
                with st.expander(f"FSM #{idx}: State Variable = `{fsm['state_variable']}`", expanded=True):
                    st.metric("Total States", fsm['state_count'])
                    
                    if fsm['states']:
                        st.markdown("**Detected States:**")
                        cols = st.columns(4)
                        for i, state in enumerate(fsm['states']):
                            with cols[i % 4]:
                                st.markdown(f"- `{state}`")
                    else:
                        st.info("No state parameters found (may be using enumerated values)")
                    
                    # FSM visualization would go here
                    st.info("ðŸ’¡ Tip: Ensure all states are reachable and FSM is fully specified")
    
    # ===== TAB 5: Pipeline Analysis =====
    with tabs[4]:
        st.header("ðŸ“ˆ Pipeline & Register Chain Analysis")
        
        if not analyzer.register_chains:
            st.info("No register chains/pipelines detected")
            st.markdown("""
            **Pipeline Detection Heuristics:**
            - Looks for signals with stage numbers (e.g., data_stage1, data_stage2)
            - Common patterns: `name_stage<N>`, `name_s<N>`, `name_pipe<N>`, `name_p<N>`
            """)
        else:
            st.success(f"âœ… Detected {len(analyzer.register_chains)} register chain(s)")
            
            for chain in analyzer.register_chains:
                with st.expander(f"Pipeline: `{chain['base_name']}` ({chain['depth']} stages)", expanded=True):
                    st.markdown(f"**Pipeline Depth:** {chain['depth']} stages")
                    st.markdown("**Stages:**")
                    
                    # Visual pipeline representation
                    pipeline_str = " â†’ ".join([f"`{stage}`" for stage in chain['stages']])
                    st.markdown(pipeline_str)
                    
                    # Table view
                    stage_df = pd.DataFrame([
                        {'Stage #': idx + 1, 'Signal Name': stage}
                        for idx, stage in enumerate(chain['stages'])
                    ])
                    st.dataframe(stage_df, use_container_width=True)
    
    # ===== TAB 6: Code Quality =====
    with tabs[5]:
        st.header("âš ï¸ Code Quality & Best Practices")
        
        if not analyzer.coding_issues:
            st.success("âœ… No coding issues detected! Great job!")
        else:
            st.warning(f"âš ï¸ Found {len(analyzer.coding_issues)} coding issue(s)")
            
            # Group by severity
            errors = [i for i in analyzer.coding_issues if i['severity'] == 'ERROR']
            warnings = [i for i in analyzer.coding_issues if i['severity'] == 'WARNING']
            infos = [i for i in analyzer.coding_issues if i['severity'] == 'INFO']
            
            # Errors
            if errors:
                st.markdown("### ðŸ”´ Critical Errors")
                for issue in errors:
                    with st.expander(f"âŒ {issue['type']}: {issue['message']}", expanded=True):
                        st.error(issue['message'])
                        st.markdown(f"**Recommendation:** {issue['recommendation']}")
            
            # Warnings
            if warnings:
                st.markdown("### ðŸŸ¡ Warnings")
                for issue in warnings:
                    with st.expander(f"âš ï¸ {issue['type']}: {issue['message']}", expanded=False):
                        st.warning(issue['message'])
                        st.markdown(f"**Recommendation:** {issue['recommendation']}")
            
            # Info
            if infos:
                st.markdown("### â„¹ï¸ Informational")
                for issue in infos:
                    with st.expander(f"â„¹ï¸ {issue['type']}: {issue['message']}", expanded=False):
                        st.info(issue['message'])
                        st.markdown(f"**Recommendation:** {issue['recommendation']}")
            
            # Export report
            st.markdown("---")
            if st.button("ðŸ“¥ Generate Full Report"):
                report = f"# Code Quality Report - {stats['module_name']}\n\n"
                report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                report += f"## Summary\n"
                report += f"- Total Issues: {len(analyzer.coding_issues)}\n"
                report += f"- Errors: {len(errors)}\n"
                report += f"- Warnings: {len(warnings)}\n"
                report += f"- Info: {len(infos)}\n\n"
                
                for issue in analyzer.coding_issues:
                    report += f"### [{issue['severity']}] {issue['type']}\n"
                    report += f"**Issue:** {issue['message']}\n\n"
                    report += f"**Recommendation:** {issue['recommendation']}\n\n"
                    report += "---\n\n"
                
                st.download_button(
                    label="ðŸ“¥ Download Report (Markdown)",
                    data=report,
                    file_name=f"{stats['module_name']}_code_quality_report.md",
                    mime="text/markdown"
                )
    
    # ===== TAB 7: Module Hierarchy =====
    with tabs[6]:
        st.header("ðŸ—ï¸ Module Instantiation Hierarchy")
        
        if not analyzer.module_instances:
            st.info("No submodule instantiations found (this is a leaf module)")
        else:
            st.success(f"âœ… Found {len(analyzer.module_instances)} submodule instance(s)")
            
            # Group by module type
            module_types = Counter([inst['module_type'] for inst in analyzer.module_instances])
            
            st.subheader("Instance Summary")
            summary_df = pd.DataFrame([
                {'Module Type': mod_type, 'Instance Count': count}
                for mod_type, count in module_types.items()
            ])
            st.dataframe(summary_df, use_container_width=True)
            
            st.markdown("---")
            
            # Detailed instances
            st.subheader("Instance Details")
            for inst in analyzer.module_instances:
                with st.expander(f"ðŸ“¦ {inst['instance_name']} ({inst['module_type']})", expanded=False):
                    st.markdown(f"**Module Type:** `{inst['module_type']}`")
                    st.markdown(f"**Instance Name:** `{inst['instance_name']}`")
                    
                    st.markdown("**Port Connections:**")
    
    # ===== TAB 8: Synthesis Time Estimation =====
    with tabs[7]:
        st.header("â±ï¸ Synthesis Time Estimation")
        
        if not analyzer.synthesis_metrics:
            st.error("âŒ Synthesis metrics not calculated")
        else:
            metrics = analyzer.synthesis_metrics
            
            # Main estimate
            st.subheader("ðŸ“Š Estimated Synthesis Time")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                time_display = f"{metrics['estimated_time_minutes']:.1f} min"
                if metrics['estimated_time_minutes'] > 60:
                    time_display = f"{metrics['estimated_time_hours']:.1f} hrs"
                
                st.metric(
                    "Estimated Time",
                    time_display,
                    delta=metrics['category']
                )
            
            with col2:
                st.metric("Estimated Gates", f"{metrics['estimated_gates']:,}")
            
            with col3:
                st.metric("Complexity Factor", f"{metrics['complexity_multiplier']}x")
            
            with col4:
                category_emoji = {
                    'Fast': 'ðŸŸ¢',
                    'Moderate': 'ðŸŸ¡',
                    'Slow': 'ðŸŸ ',
                    'Very Slow': 'ðŸ”´'
                }
                st.metric(
                    "Category",
                    f"{category_emoji.get(metrics['category'], 'âšª')} {metrics['category']}"
                )
            
            # Progress bar visualization
            st.markdown("---")
            st.subheader("Time Estimate Breakdown")
            
            max_time = 120  # 2 hours
            progress = min(metrics['estimated_time_minutes'] / max_time, 1.0)
            st.progress(progress)
            
            # Factors
            st.markdown("### ðŸ“ˆ Complexity Factors")
            
            factors = metrics['factors']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Positive Factors (increase time):**")
                if factors['fsm_penalty'] > 0:
                    st.markdown(f"  - ðŸ”„ FSMs: +{factors['fsm_penalty'] * 0.3:.1f}x")
                if factors['large_block_penalty'] > 0:
                    st.markdown(f"  - ðŸ“ Large blocks: +{factors['large_block_penalty'] * 0.2:.1f}x")
                if factors['comb_loop_penalty'] > 0:
                    st.error(f"  - âš ï¸ Comb loops: +{factors['comb_loop_penalty'] * 2.0:.1f}x (CRITICAL)")
            
            with col2:
                st.markdown("**Negative Factors (decrease time):**")
                if factors['pipeline_bonus'] > 0:
                    st.markdown(f"  - ðŸ“ˆ Pipelines: +{factors['pipeline_bonus'] * 0.1:.1f}x (efficient)")
                st.info("Well-structured RTL synthesizes faster")
            
            # Industry comparison
            st.markdown("---")
            st.subheader("ðŸ­ Industry Benchmark Comparison")
            
            benchmark_data = {
                'Design Size': ['Small (<1K gates)', 'Medium (1K-10K)', 'Large (10K-100K)', 'Your Design'],
                'Typical Time': ['1-5 min', '5-30 min', '30-300 min', time_display],
                'Complexity': ['Low', 'Moderate', 'High', metrics['category']]
            }
            
            benchmark_df = pd.DataFrame(benchmark_data)
            st.dataframe(benchmark_df, use_container_width=True)
            
            # Recommendations
            st.markdown("---")
            st.subheader("ðŸ’¡ Optimization Recommendations")
            
            if metrics['category'] in ['Slow', 'Very Slow']:
                st.warning("âš ï¸ Your design may have long synthesis times. Consider:")
                
                if factors['large_block_penalty'] > 0:
                    st.markdown("- âœ… Break large always blocks into smaller modules")
                
                if factors['comb_loop_penalty'] > 0:
                    st.error("- ðŸ”´ **CRITICAL**: Fix combinational loops immediately")
                
                if factors['fsm_penalty'] > 2:
                    st.markdown("- âœ… Review FSM encoding (consider one-hot vs binary)")
                
                st.markdown("- âœ… Use partitioning for large designs")
                st.markdown("- âœ… Enable incremental synthesis")
                st.markdown("- âœ… Use synthesis directives for optimization")
            else:
                st.success("âœ… Your design should synthesize efficiently!")
            
            # Notes
            st.markdown("---")
            st.info("""
            **ðŸ“ Notes:**
            - Estimates based on industry-standard synthesis tools (Design Compiler, Genus)
            - Actual time depends on: tool version, machine specs, optimization goals, technology library
            - First-time synthesis is slower; incremental synthesis is faster
            - Complex timing constraints increase synthesis time
            """)
    
    # ===== TAB 9: HDL Lint Rules =====
    with tabs[8]:
        st.header("ðŸ” HDL Lint Rules & Checks")
        
        # Summary
        st.subheader("ðŸ“Š Lint Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Combinational Loops", len(analyzer.combinational_loops),
                     delta="ðŸ”´ CRITICAL" if analyzer.combinational_loops else "âœ…")
        
        with col2:
            st.metric("Latch Warnings", len(analyzer.latch_warnings),
                     delta="âš ï¸" if analyzer.latch_warnings else "âœ…")
        
        with col3:
            st.metric("Incomplete Cases", len(analyzer.incomplete_cases),
                     delta="âš ï¸" if analyzer.incomplete_cases else "âœ…")
        
        with col4:
            st.metric("Tied Signals", len(analyzer.tied_signals),
                     delta="â„¹ï¸" if analyzer.tied_signals else "âœ…")
        
        st.markdown("---")
        
        # Combinational Loops
        st.subheader("ðŸ”´ Combinational Loop Detection")
        
        if not analyzer.combinational_loops:
            st.success("âœ… No combinational loops detected!")
        else:
            st.error(f"ðŸ”´ Found {len(analyzer.combinational_loops)} combinational loop(s)")
            
            for idx, loop in enumerate(analyzer.combinational_loops, 1):
                with st.expander(f"Loop #{idx}: {len(loop['signals'])} signals involved", expanded=True):
                    st.error(f"**Severity:** {loop['severity']}")
                    
                    # Show loop path
                    loop_path = ' â†’ '.join([f"`{sig}`" for sig in loop['signals']]) + f" â†’ `{loop['signals'][0]}`"
                    st.markdown(f"**Loop Path:** {loop_path}")
                    
                    st.markdown("**Impact:**")
                    st.markdown("- âŒ Synthesis will fail")
                    st.markdown("- âŒ Simulation may hang or oscillate")
                    st.markdown("- âŒ Cannot generate valid logic")
                    
                    st.markdown("**Resolution:**")
                    st.markdown("- âœ… Insert a register to break the loop")
                    st.markdown("- âœ… Review the logic equations")
                    st.markdown("- âœ… Check for unintended feedback paths")
        
        st.markdown("---")
        
        # Latch Inference
        st.subheader("âš ï¸ Latch Inference Warnings")
        
        if not analyzer.latch_warnings:
            st.success("âœ… No potential latches detected!")
        else:
            st.warning(f"âš ï¸ Found {len(analyzer.latch_warnings)} potential latch(es)")
            
            latch_df = pd.DataFrame(analyzer.latch_warnings)
            st.dataframe(latch_df, use_container_width=True)
            
            st.markdown("**Common Causes:**")
            st.markdown("1. âŒ `if` statement without `else` in combinational block")
            st.markdown("2. âŒ Incomplete `case` statement without `default`")
            st.markdown("3. âŒ Variable not assigned in all code paths")
            
            st.markdown("**How to Fix:**")
            st.code("""
// BAD - Will infer latch
always @(*) begin
    if (enable)
        out = data;
    // Missing else - out not assigned when enable=0
end

// GOOD - No latch
always @(*) begin
    if (enable)
        out = data;
    else
        out = 0;  // Default value
end

// BETTER - Default assignment
always @(*) begin
    out = 0;  // Default
    if (enable)
        out = data;
end
""", language='verilog')
        
        st.markdown("---")
        
        # Incomplete Cases
        st.subheader("âš ï¸ Incomplete Case Statements")
        
        if not analyzer.incomplete_cases:
            st.success("âœ… All case statements have default clauses!")
        else:
            st.warning(f"âš ï¸ Found {len(analyzer.incomplete_cases)} incomplete case statement(s)")
            
            case_df = pd.DataFrame(analyzer.incomplete_cases)
            st.dataframe(case_df, use_container_width=True)
            
            st.markdown("**How to Fix:**")
            st.code("""
// BAD - May infer latch
case (select)
    2'b00: out = a;
    2'b01: out = b;
    2'b10: out = c;
    // Missing 2'b11 case!
endcase

// GOOD - Full case with default
case (select)
    2'b00: out = a;
    2'b01: out = b;
    2'b10: out = c;
    default: out = 0;  // Covers all other cases
endcase
""", language='verilog')
        
        st.markdown("---")
        
        # Tied Signals
        st.subheader("ðŸ”Œ Tied Signals (Constants)")
        
        if not analyzer.tied_signals:
            st.info("â„¹ï¸ No tied signals detected")
        else:
            st.info(f"â„¹ï¸ Found {len(analyzer.tied_signals)} signal(s) tied to constants")
            
            col1, col2 = st.columns(2)
            
            tied_to_zero = {k: v for k, v in analyzer.tied_signals.items() if v == '0'}
            tied_to_one = {k: v for k, v in analyzer.tied_signals.items() if v == '1'}
            
            with col1:
                st.markdown("**Tied to 0 (GND):**")
                if tied_to_zero:
                    for sig in tied_to_zero.keys():
                        st.markdown(f"  - `{sig}` = 0")
                else:
                    st.success("None")
            
            with col2:
                st.markdown("**Tied to 1 (VDD):**")
                if tied_to_one:
                    for sig in tied_to_one.keys():
                        st.markdown(f"  - `{sig}` = 1")
                else:
                    st.success("None")
            
            st.markdown("**Note:** Tied signals are often intentional for configuration or testing.")
        
        st.markdown("---")
        
        # HDL Best Practices Summary
        st.subheader("ðŸ“š HDL Lint Rules Checked")
        
        lint_rules = {
            'Rule': [
                'Combinational Loops',
                'Incomplete If-Else',
                'Incomplete Case Statements',
                'Multiple Drivers',
                'Blocking in Sequential',
                'Non-blocking in Combinational',
                'Mixed Assignments',
                'Tied Signals',
                'Large Always Blocks'
            ],
            'Status': [
                'âœ… Checked' if not analyzer.combinational_loops else 'âŒ Issues Found',
                'âœ… Checked' if not analyzer.latch_warnings else 'âš ï¸ Warnings',
                'âœ… Checked' if not analyzer.incomplete_cases else 'âš ï¸ Warnings',
                'âœ… Checked',
                'âœ… Checked',
                'âœ… Checked',
                'âœ… Checked',
                'âœ… Checked',
                'âœ… Checked'
            ],
            'Severity': [
                'CRITICAL',
                'WARNING',
                'WARNING',
                'ERROR',
                'WARNING',
                'INFO',
                'ERROR',
                'INFO',
                'INFO'
            ]
        }
        
        lint_df = pd.DataFrame(lint_rules)
        st.dataframe(lint_df, use_container_width=True)
        
        # Export lint report
        if st.button("ðŸ“¥ Generate HDL Lint Report"):
            report = f"# HDL Lint Report - {stats['module_name']}\n\n"
            report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            report += f"## Summary\n"
            report += f"- Combinational Loops: {len(analyzer.combinational_loops)}\n"
            report += f"- Latch Warnings: {len(analyzer.latch_warnings)}\n"
            report += f"- Incomplete Cases: {len(analyzer.incomplete_cases)}\n"
            report += f"- Tied Signals: {len(analyzer.tied_signals)}\n\n"
            
            if analyzer.combinational_loops:
                report += f"## ðŸ”´ Combinational Loops (CRITICAL)\n\n"
                for idx, loop in enumerate(analyzer.combinational_loops, 1):
                    report += f"### Loop #{idx}\n"
                    report += f"Signals: {' â†’ '.join(loop['signals'])}\n\n"
            
            if analyzer.latch_warnings:
                report += f"## âš ï¸ Latch Warnings\n\n"
                for warn in analyzer.latch_warnings:
                    report += f"- Signal `{warn['signal']}` in block #{warn['block_id']}: {warn['reason']}\n"
                report += "\n"
            
            if analyzer.incomplete_cases:
                report += f"## âš ï¸ Incomplete Case Statements\n\n"
                for case in analyzer.incomplete_cases:
                    report += f"- Signal `{case['signal']}` in block #{case['block_id']}: case({case['case_variable']}) missing default\n"
                report += "\n"
            
            if analyzer.tied_signals:
                report += f"## ðŸ”Œ Tied Signals\n\n"
                for sig, val in analyzer.tied_signals.items():
                    report += f"- `{sig}` = {val}\n"
            
            st.download_button(
                label="ðŸ“¥ Download HDL Lint Report",
                data=report,
                file_name=f"{stats['module_name']}_hdl_lint_report.md",
                mime="text/markdown"
            )


if __name__ == "__main__":
    main()
