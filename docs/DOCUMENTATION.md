# " Technical Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Component Details](#component-details)
3. [Algorithm Specifications](#algorithm-specifications)
4. [API Reference](#api-reference)
5. [Data Structures](#data-structures)
6. [Performance Optimization](#performance-optimization)

---

## Architecture Overview

### System Architecture

```
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"                    User Interface Layer                      "
"                      (Streamlit Apps)                        "
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"  Hardware Debug      "      Netlist Analyzer                "
"  Assistant (8610)    "      (Demo 4 - 8550)                 "
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
                              "
                              -
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"                   Analysis Engine Layer                      "
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"  NetlistAnalyzer     "    DebugAssistant                    "
"  - Parse netlists    "    - Signal tracing                  "
"  - Build DAG         "    - Fanout analysis                 "
"  - Graph algorithms  "    - Load estimation                 "
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
                              "
                              -
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"                 Data Processing Layer                        "
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"  NetworkX            "    Pandas                            "
"  - Graph operations  "    - Data tables                     "
"  - Path finding      "    - Statistics                      "
"  - SCC detection     "    - Export                          "
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
                              "
                              -
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"                  Visualization Layer                         "
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"  PyVis               "    Plotly                            "
"  - DAG rendering     "    - Charts                          "
"  - Interactive       "    - Metrics                         "
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
```

---

## Component Details

### 1. Hardware Debug Assistant (Demo 3)

**File**: `demo3/debug_assistant.py`

**Purpose**: Signal-level debugging and connectivity analysis

**Key Classes**:

```python
class VerilogParser:
    """Parses Verilog netlist files"""
    
    def extract_signals(self, content: str) -> dict:
        """Extract all wire/reg declarations"""
        
    def extract_gates(self, content: str) -> dict:
        """Extract gate instances with connections"""
        
    def build_connectivity_map(self) -> dict:
        """Build signal driver/reader mapping"""
```

**Features Implementation**:

1. **Signal Search**
   - Linear scan through signal dictionary
   - O(1) lookup by signal name
   - Pattern matching support

2. **Fanout Analysis**
   - Counts readers per signal
   - Classifies health: GOOD(<10), MODERATE(10-20), WARNING(20-30), CRITICAL(>30)
   - Real-time metrics

3. **Load Estimation**
   - 28nm CMOS model
   - Gate capacitances: INV(0.8), NAND(1.2), DFF(2.5) fF
   - Delay = base_delay + load -- 0.01 ns

---

### 2. Netlist Analyzer (Demo 4)

**File**: `demo4/local_analyzer.py`

**Purpose**: DAG-based analysis with advanced algorithms

**Key Classes**:

```python
class NetlistAnalyzer:
    """Main analysis engine"""
    
    def __init__(self, content: str):
        self.content = content
        self.dag = nx.DiGraph()
        self.gates = {}
        self.signals = {}
        self.stats = {}
    
    def parse(self, build_dag: bool = True):
        """Parse netlist and optionally build DAG"""
        
    def detect_combinational_loops(self) -> list:
        """Find feedback loops using SCC"""
        
    def analyze_clock_domains(self) -> list:
        """Identify clock domains and propagate"""
        
    def identify_congestion_hotspots(self) -> list:
        """Find high-connectivity nodes"""
```

---

## Algorithm Specifications

### 1. Combinational Loop Detection

**Algorithm**: Tarjan's Strongly Connected Components

**Complexity**: O(V + E) where V = gates, E = connections

**Implementation**:
```python
def detect_combinational_loops(self):
    # Find all SCCs using Tarjan's algorithm
    sccs = list(nx.strongly_connected_components(self.dag))
    
    loops = []
    for scc in sccs:
        if len(scc) > 1:  # Non-trivial SCC = potential loop
            # Check if loop contains registers
            has_register = any(self._is_register(node) for node in scc)
            
            if not has_register:
                # Pure combinational loop - CRITICAL
                cycle = nx.find_cycle(self.dag.subgraph(scc))
                loops.append({
                    'nodes': list(scc),
                    'path': self._extract_cycle_path(cycle),
                    'severity': 'CRITICAL',
                    'suggestions': self._generate_loop_fixes(scc)
                })
    
    return loops
```

**Why This Works**:
- SCCs identify all nodes in feedback loops
- Filter out valid register-based feedback
- Remaining cycles are combinational (synthesis errors)

---

### 2. Clock Domain Analysis

**Algorithm**: BFS Propagation with Heuristic Detection

**Complexity**: O(V + E)

**Implementation**:
```python
def analyze_clock_domains(self):
    # Step 1: Find primary clocks
    primary_clocks = set()
    for sig in self.signals:
        if sig.lower().startswith('clk'):
            primary_clocks.add(sig)
    
    # Step 2: Map registers to clocks
    clock_domains = {}
    for gate in self.gates:
        if self._is_register(gate):
            clk_signal = self._get_clock_port(gate)
            if clk_signal in primary_clocks:
                clock_domains.setdefault(clk_signal, []).append(gate)
    
    # Step 3: Propagate to combinational logic
    for clk, registers in clock_domains.items():
        visited = set(registers)
        queue = list(registers)
        
        while queue:
            node = queue.pop(0)
            
            # Add predecessors (logic feeding registers)
            for pred in self.dag.predecessors(node):
                if pred not in visited and not self._is_register(pred):
                    visited.add(pred)
                    queue.append(pred)
            
            # Add successors (logic driven by registers)
            for succ in self.dag.successors(node):
                if succ not in visited and not self._is_register(succ):
                    visited.add(succ)
                    queue.append(succ)
        
        clock_domains[clk] = list(visited)
    
    return clock_domains
```

**Smart Detection Features**:
- Only considers signals starting with "clk"
- Ignores internal nodes (n_XXX)
- Propagates through combinational gates only
- Stops at register boundaries

---

### 3. Congestion Hotspot Identification

**Algorithm**: Weighted Degree Scoring

**Complexity**: O(V)

**Implementation**:
```python
def identify_congestion_hotspots(self):
    hotspots = []
    
    for node in self.dag.nodes():
        fanin = self.dag.in_degree(node)
        fanout = self.dag.out_degree(node)
        
        # Weighted score: fanout has 2x impact
        score = fanin + (2 * fanout)
        
        if score > 20:  # Threshold
            severity = (
                'CRITICAL' if score > 50 else
                'HIGH' if score > 30 else
                'MODERATE'
            )
            
            suggestions = []
            if fanout > 15:
                suggestions.append(f'Insert buffer tree (fanout={fanout})')
            if fanin > 10:
                suggestions.append(f'Decompose logic ({fanin} inputs)')
            
            hotspots.append({
                'gate': node,
                'score': score,
                'fanin': fanin,
                'fanout': fanout,
                'severity': severity,
                'suggestions': suggestions
            })
    
    return sorted(hotspots, key=lambda x: x['score'], reverse=True)
```

**Scoring Rationale**:
- High fanout ' routing congestion
- High fanin ' area/timing issues
- Fanout weighted 2x (physical design impact)

---

## API Reference

### NetlistAnalyzer Class

#### Constructor
```python
NetlistAnalyzer(content: str)
```
**Parameters**:
- `content`: Full netlist file content as string

#### Methods

##### parse()
```python
parse(build_dag: bool = True) -> None
```
Parse the netlist and optionally build DAG.

**Parameters**:
- `build_dag`: If True, constructs full directed acyclic graph

**Sets**:
- `self.gates`: Dictionary of gate instances
- `self.signals`: Dictionary of signals
- `self.dag`: NetworkX DiGraph
- `self.stats`: Statistics dictionary

---

##### get_critical_paths()
```python
get_critical_paths(top_n: int = 10) -> list[dict]
```
Identify longest logic paths using topological sort.

**Parameters**:
- `top_n`: Number of paths to return

**Returns**:
```python
[{
    'length': int,           # Number of gates
    'delay_ns': float,       # Estimated delay
    'path': list[str],       # Gate names
    'bottlenecks': list[str] # Slow gates
}, ...]
```

---

##### analyze_signal()
```python
analyze_signal(signal_name: str) -> dict
```
Detailed analysis of a single signal.

**Parameters**:
- `signal_name`: Name of signal to analyze

**Returns**:
```python
{
    'found': bool,
    'type': str,             # 'wire' or 'reg'
    'drivers': list[str],    # Gates driving this signal
    'readers': list[str],    # Gates reading this signal
    'fanout': int,           # Number of readers
    'fanout_health': str,    # 'GOOD', 'MODERATE', 'WARNING', 'CRITICAL'
    'estimated_load': float  # Capacitive load (fF)
}
```

---

##### detect_combinational_loops()
```python
detect_combinational_loops() -> list[dict]
```
Find feedback loops in combinational logic.

**Returns**:
```python
[{
    'nodes': list[str],      # Gates in loop
    'path': list[str],       # Cycle path
    'gate_types': list[str], # Types of gates
    'severity': str,         # 'CRITICAL', 'WARNING', 'INFO'
    'suggestions': list[str] # Fix recommendations
}, ...]
```

---

##### analyze_clock_domains()
```python
analyze_clock_domains() -> list[dict]
```
Identify and analyze clock domains.

**Returns**:
```python
[{
    'clock': str,            # Clock signal name
    'register_count': int,   # Number of registers
    'total_nodes': int,      # Including combinational
    'registers': list[str],  # Register names
    'all_nodes': list[str],  # All nodes in domain
    'percentage': float      # % of total design
}, ...]
```

---

##### identify_congestion_hotspots()
```python
identify_congestion_hotspots() -> list[dict]
```
Find high-connectivity routing hotspots.

**Returns**:
```python
[{
    'gate': str,             # Gate name
    'gate_type': str,        # Gate type
    'fanin': int,            # Input degree
    'fanout': int,           # Output degree
    'congestion_score': int, # fanin + 2*fanout
    'severity': str,         # 'CRITICAL', 'HIGH', 'MODERATE'
    'suggestions': list[str] # Mitigation strategies
}, ...]
```

---

##### export_dag_html()
```python
export_dag_html(output_path: str, clock_domain_colors: dict = None) -> str
```
Generate interactive DAG visualization.

**Parameters**:
- `output_path`: File path for HTML output
- `clock_domain_colors`: Optional node color mapping

**Returns**: Path to generated HTML file

---

## Data Structures

### Gate Dictionary
```python
gates = {
    'gate_name': {
        'type': 'AND2',
        'connections': {
            'A': 'signal_1',
            'B': 'signal_2',
            'Y': 'signal_out'
        },
        'module': 'module_name'
    },
    ...
}
```

### Signal Dictionary
```python
signals = {
    'signal_name': {
        'type': 'wire',  # or 'reg'
        'drivers': ['gate1', 'gate2'],
        'readers': ['gate3', 'gate4', 'gate5'],
        'width': 1  # bit width
    },
    ...
}
```

### DAG Structure
```python
# NetworkX DiGraph
dag.nodes() = ['gate1', 'gate2', 'gate3', ...]
dag.edges() = [('gate1', 'gate2'), ('gate2', 'gate3'), ...]
dag.in_degree('gate2') = 1
dag.out_degree('gate2') = 1
```

---

## Performance Optimization

### Parsing Optimization

**Lazy DAG Building**:
```python
# Fast stats-only mode
analyzer.parse(build_dag=False)  # ~0.5s for 10K gates

# Full DAG mode
analyzer.parse(build_dag=True)   # ~2s for 10K gates
```

**Gate Extraction Limit**:
```python
# Configurable limit for large files
max_gates = 10000  # Default
```

---

### Memory Optimization

**Incremental Processing**:
- Stream large files in chunks
- Process modules independently
- Clear intermediate data structures

**Example**:
```python
def parse_large_netlist(filename, chunk_size=1000):
    with open(filename) as f:
        while chunk := f.read(chunk_size):
            process_chunk(chunk)
            gc.collect()  # Free memory
```

---

### Caching Strategies

**Memoization**:
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_critical_path(start_node, end_node):
    return nx.shortest_path(dag, start_node, end_node)
```

**Session State** (Streamlit):
```python
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = NetlistAnalyzer(content)
```

---

## Error Handling

### Parsing Errors

```python
try:
    analyzer = NetlistAnalyzer(content)
    analyzer.parse()
except SyntaxError as e:
    print(f"Verilog syntax error: {e}")
except ValueError as e:
    print(f"Invalid netlist structure: {e}")
```

### Graph Algorithm Errors

```python
try:
    loops = analyzer.detect_combinational_loops()
except nx.NetworkXError as e:
    print(f"Graph error: {e}")
except Exception as e:
    print(f"Analysis failed: {e}")
```

---

## Testing

### Unit Tests

```python
def test_parse_basic_netlist():
    content = """
    module test;
      wire a, b, c;
      AND2 g1 (.A(a), .B(b), .Y(c));
    endmodule
    """
    analyzer = NetlistAnalyzer(content)
    analyzer.parse()
    assert len(analyzer.gates) == 1
    assert 'g1' in analyzer.gates
```

### Integration Tests

```python
def test_full_analysis_pipeline():
    with open('your_netlist.v') as f:
        content = f.read()
    
    analyzer = NetlistAnalyzer(content)
    analyzer.parse(build_dag=True)
    
    paths = analyzer.get_critical_paths()
    loops = analyzer.detect_combinational_loops()
    domains = analyzer.analyze_clock_domains()
    
    assert len(paths) > 0
    assert len(loops) == 0  # Good design
    assert len(domains) > 0
```

---

## Deployment

### Standalone App

```python
# Build executable with PyInstaller
pyinstaller --onefile \
    --add-data "demo3:demo3" \
    --add-data "demo4:demo4" \
    --name "NetlistAnalyzer" \
    LAUNCH_BOTH.py
```

### Docker Container

```dockerfile
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8610 8550
CMD ["python", "LAUNCH_BOTH.py"]
```

---

## Security Considerations

1. **Input Validation**: Sanitize uploaded netlist files
2. **Resource Limits**: Cap memory usage for large designs
3. **File Access**: Restrict file system access
4. **Network**: Run locally, no external connections

---

## Troubleshooting

### Common Issues

**Issue**: "No gates found"
**Solution**: Check netlist format, ensure gate instances present

**Issue**: "DAG generation timeout"
**Solution**: Reduce max_gates limit or use lazy parsing

**Issue**: "Memory error on large netlist"
**Solution**: Enable chunked processing or increase system RAM

---

## References

1. NetworkX Documentation: https://networkx.org
2. Streamlit Documentation: https://docs.streamlit.io
3. Tarjan's SCC Algorithm: Sedgewick & Wayne, Algorithms 4th Ed.
4. EDA Algorithms: Synopsys Design Compiler User Guide
