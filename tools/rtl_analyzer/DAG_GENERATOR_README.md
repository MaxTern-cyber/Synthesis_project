# DAG Visualization Generator

A standalone tool to generate interactive DAG (Directed Acyclic Graph) visualizations from Verilog RTL designs.

## ðŸš€ Quick Start

### Generate Visualization from Verilog File

```bash
python generate_dag_visualization.py your_netlist.v
```

This will:
- Parse the Verilog file
- Build a directed graph of signal dependencies
- Generate an interactive HTML file: `dag_visualization.html`
- Open the HTML file in your browser to view

## ðŸ“‹ Usage

### Basic Usage
```bash
python generate_dag_visualization.py <verilog_file>
```

### With Options
```bash
# Use force-directed layout
python generate_dag_visualization.py your_netlist.v --layout force

# Specify custom output file
python generate_dag_visualization.py your_netlist.v --output my_dag.html

# Hide signal names (cleaner for large designs)
python generate_dag_visualization.py your_netlist.v --no-labels

# Combine options
python generate_dag_visualization.py your_netlist.v --layout hierarchical --output output/dag.html
```

### Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `verilog_file` | Path to Verilog file (required) | - |
| `--layout` | Layout algorithm: `hierarchical` or `force` | `hierarchical` |
| `--output`, `-o` | Output HTML file path | `dag_visualization.html` |
| `--no-labels` | Hide signal names on nodes | `False` |

## ðŸŽ¨ Visualization Features

### Node Types & Shapes

- **ðŸ”· Diamond** - Input Ports (Blue)
- **ðŸ”º Triangle** - Output Ports (Red)
- **â—»ï¸ Box** - Sequential Elements / Registers (Green)
- **âšª Ellipse** - Combinational Logic (Orange)

### Edge Types

- **â”â” Solid Line** - Sequential path (through registers)
- **â”ˆâ”ˆ Dashed Line** - Combinational path (direct logic)

### Clock Domains

Sequential elements are color-coded by clock domain:
- Each clock domain gets a unique color
- Makes it easy to identify timing boundaries
- 10-color palette cycles for multiple domains

### Interactive Controls

The generated HTML includes:

**â„ï¸ Freeze Layout / â–¶ï¸ Enable Physics**
- Toggle physics simulation on/off
- Frozen mode: instant interaction, no lag
- Physics mode: nodes adjust dynamically

**ðŸ” Reset Zoom**
- Fits entire graph in viewport
- Useful after zooming/panning

**Loading Progress Bar**
- Shows 0-100% progress during stabilization
- Automatically hides when complete
- Timeout after 30 seconds if not complete

## ðŸ—ï¸ Architecture

### Parsing Pipeline

1. **Verilog Parsing**
   - Extract module name, ports, wires, registers
   - Parse assign statements
   - Identify sequential blocks (always @)
   - Detect clock signals

2. **DAG Construction**
   - Build NetworkX directed graph
   - Add nodes for ports, wires, registers
   - Add edges for dataflow dependencies
   - Classify edges as sequential/combinational

3. **Clock Domain Identification**
   - Group signals by clock
   - Assign colors to domains
   - Track cross-domain signals

4. **HTML Generation**
   - Create PyVis network visualization
   - Apply performance optimizations
   - Inject loading bar and controls
   - Save standalone HTML file

## âš¡ Performance Optimizations

### Automatic Optimizations

- **Reduced Iterations**: 30-50 iterations (vs 100+ default)
- **Adaptive Timestep**: Faster convergence
- **Node Size Scaling**: Smaller nodes for large graphs
  - 70% size for 100+ nodes
  - 50% size for 500+ nodes
  - 30% size for 1000+ nodes
- **Auto-Freeze**: Physics disabled 2 seconds after load

### Layout Algorithms

**Hierarchical (Recommended)**
- Top-down organization
- Clear dependency flow
- Fastest for most designs
- Best for: sequential pipelines, FSMs

**Force-Directed**
- Natural clustering
- Reveals hidden patterns
- Better for: irregular topologies, large netlists

## ðŸ“Š Example Output

```
==============================================================
  RTL DAG Visualization Generator
==============================================================
ðŸ“– Parsing Verilog file: your_netlist.v
   Module: top_module
   Ports: 24
   Clocks: 2
   Sequential blocks: 15
   Assign statements: 42

ðŸ”¨ Building DAG graph...
   Nodes: 156
   Edges: 324
   Clock domains: 2

ðŸŽ¨ Generating visualization...
   Saving to: dag_visualization.html

âœ… Visualization generated successfully!
ðŸ“‚ Open dag_visualization.html in your browser to view
==============================================================
âœ¨ Done!
==============================================================
```

## ðŸ”§ Requirements

```bash
pip install networkx pyvis
```

Or install from requirements:
```bash
pip install -r requirements.txt
```

## ðŸ“– Visualization Legend

### In the Generated HTML:

**Top-Left Info Panel:**
- Module name
- Number of nodes
- Number of edges
- Clock domain count

**Graph Interaction:**
- **Scroll** - Zoom in/out
- **Drag background** - Pan
- **Drag nodes** - Reposition
- **Hover nodes** - View details
- **Click nodes** - Select/highlight

## ðŸŽ¯ Use Cases

### 1. Debug Signal Flow
```bash
python generate_dag_visualization.py buggy_design.v
```
- Trace signal dependencies
- Find undriven signals
- Identify feedback loops

### 2. Understand Legacy Code
```bash
python generate_dag_visualization.py legacy_module.v --no-labels
```
- Visualize overall structure
- Identify major dataflow paths
- Understand clock domain crossings

### 3. Document Design
```bash
python generate_dag_visualization.py my_design.v -o docs/architecture.html
```
- Generate architecture diagram
- Share with team
- Include in documentation

### 4. Verify Hierarchy
```bash
python generate_dag_visualization.py top.v --layout hierarchical
```
- Check pipeline stages
- Verify intended structure
- Find unexpected dependencies

## ðŸ› Troubleshooting

### Issue: "Module not found: pyvis"
**Solution:**
```bash
pip install pyvis networkx
```

### Issue: Visualization loads slowly
**Solution:**
- Use `--no-labels` for large designs
- Try `--layout hierarchical` (faster)
- Physics auto-freezes after 2 seconds

### Issue: Can't see all nodes
**Solution:**
- Click "ðŸ” Reset Zoom" button
- Scroll to zoom out
- Check if graph is empty (parse errors)

### Issue: Nodes keep moving around
**Solution:**
- Click "â„ï¸ Freeze Layout" button
- Or wait 2 seconds for auto-freeze

## ðŸ“ Notes

### File Format
- Supports Verilog (.v) and SystemVerilog (.sv)
- ASCII and UTF-8 encoding
- Handles comments and multi-line statements

### Graph Size Limits
- **Small** (<100 nodes): ~1-2 seconds
- **Medium** (100-500 nodes): ~4-6 seconds
- **Large** (500-1000 nodes): ~10-15 seconds
- **Very Large** (1000+ nodes): May take longer, use `--no-labels`

### Browser Compatibility
- âœ… Chrome/Edge (recommended)
- âœ… Firefox
- âš ï¸ Safari (slightly slower)
- âŒ IE11 (not supported)

## ðŸ”— Related Tools

- **RTL Analyzer** ([rtl_analyzer.py](rtl_analyzer.py)) - Full Streamlit app with synthesis estimation, HDL lint, etc.
- **Performance Guide** ([PERFORMANCE_OPTIMIZATIONS.md](PERFORMANCE_OPTIMIZATIONS.md)) - Detailed optimization documentation
- **DAG Guide** ([DAG_VISUALIZATION_GUIDE.md](DAG_VISUALIZATION_GUIDE.md)) - Comprehensive visualization guide

## ðŸ“„ License

See [LICENSE](../LICENSE)

---

**Last Updated**: January 22, 2026  
**Version**: 1.0  
**Status**: Production-ready âœ…
