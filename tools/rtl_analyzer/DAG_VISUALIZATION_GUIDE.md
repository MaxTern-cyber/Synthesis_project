# DAG Visualization Guide - RTL Analyzer

## Overview

The DAG (Directed Acyclic Graph) Visualization feature provides an **interactive, graphical representation** of your RTL dataflow, making it easy to understand signal dependencies, identify combinational vs. sequential logic, and visualize clock domains.

---

## Features

### 🎨 Visual Elements

#### **Node Shapes & Colors**

| Element Type | Shape | Color | Purpose |
|-------------|-------|-------|---------|
| **Input Ports** | 🔷 Diamond | Blue (#3498DB) | Primary inputs to the module |
| **Output Ports** | 🔺 Triangle | Red (#E74C3C) | Primary outputs from the module |
| **Registers (Sequential)** | 🟩 Rectangle/Box | Green (#2ECC71) | Flip-flops, latches, sequential elements |
| **Wires (Combinational)** | 🟠 Ellipse | Orange (#F39C12) | Combinational logic signals |
| **Simple Wires** | ⚫ Dot | Gray (#95A5A6) | Pass-through connections |

#### **Edge Types**

| Edge Type | Style | Color | Meaning |
|-----------|-------|-------|---------|
| **Sequential** | ━━ Solid, Thick (width=2) | Green | Path through registers (clocked) |
| **Combinational** | ┈┈ Dashed, Thin (width=1) | Orange | Direct combinational logic |

---

## Clock Domain Visualization

### Color-Coded Clock Domains

Each clock domain is assigned a **unique color** from a predefined palette:

```
Clock 1: #FF6B6B (Red-ish)
Clock 2: #4ECDC4 (Teal)
Clock 3: #45B7D1 (Sky Blue)
Clock 4: #FFA07A (Light Salmon)
Clock 5: #98D8C8 (Mint)
... and 5 more colors cycling
```

**All registers (sequential elements) in the same clock domain share the same color**, making it easy to identify clock domain crossings and potential CDC (Clock Domain Crossing) issues.

### Clock Domain Information Panel

The visualization includes an expandable panel showing:
- Clock signal name
- Number of signals in that domain
- List of all signals (first 20 shown, with overflow indicator)

---

## Layout Algorithms

Choose from **4 different layout algorithms** to best visualize your design:

### 1. **Hierarchical (Top-Down)** ⭐ *Recommended*
- **Best for:** Most RTL designs, showing signal flow from inputs → logic → outputs
- **Direction:** Top to bottom (inputs at top, outputs at bottom)
- **Algorithm:** Directed hierarchical layout with level separation
- **Settings:**
  - Level separation: 150px
  - Node spacing: 200px
  - Sort method: Directed (follows edge direction)

**Use case:** Default view for understanding dataflow hierarchy

### 2. **Force-Directed**
- **Best for:** Small to medium designs, discovering hidden patterns
- **Algorithm:** ForceAtlas2 physics simulation
- **Settings:**
  - Gravitational constant: -50
  - Spring length: 100
  - Central gravity: 0.01

**Use case:** When you want nodes to naturally cluster by connectivity

### 3. **Circular**
- **Best for:** Designs with feedback loops, cyclic dependencies
- **Algorithm:** Arranges nodes in a circle
- **Use case:** Highlighting cycles and feedback paths

### 4. **Spring**
- **Best for:** Organic, natural-looking layouts
- **Algorithm:** Spring-electrical model with physics
- **Use case:** Exploratory analysis, aesthetic views

---

## Visualization Controls

### Interactive Options

1. **Show Signal Names** (Checkbox)
   - ✅ **ON**: Display signal names on nodes
   - ❌ **OFF**: Clean view with only shapes (hover for names)

2. **Cluster Combinational Logic** (Checkbox)
   - ✅ **ON**: Groups combinational wires together (cloud-like cluster)
   - ❌ **OFF**: Distributes signals evenly

**Clustering Logic:**
- **Combinational cluster**: All wires involved in `assign` statements or combinational `always @(*)` blocks
- **Clock domain clusters**: Sequential elements grouped by their driving clock

---

## Graph Statistics

The visualization header displays key metrics:

| Metric | Description |
|--------|-------------|
| **Total Nodes** | Number of all signals (ports + internal signals) |
| **Total Edges** | Number of dataflow connections |
| **Combinational Paths** | Edges through combinational logic only |
| **Sequential Paths** | Edges through registers (clocked elements) |

---

## How It Works (Implementation Details)

### Graph Construction Algorithm

```
1. Initialize empty directed graph G = (V, E)

2. Add vertices V:
   For each port p in {input, output, inout}:
     Add node(p, type=port, direction=p.direction)
   
   For each signal s in {wire, reg}:
     Add node(s, type=signal, is_register=(s.type == reg))

3. Add edges E from assign statements:
   For each "assign lhs = rhs":
     Extract all signals in rhs → rhs_signals
     For each sig in rhs_signals:
       Add edge(sig → lhs, type=combinational, source=assign)

4. Add edges E from always blocks:
   For each always block B:
     driven = B.driven_signals
     read = B.read_signals
     edge_type = sequential if B.is_clocked else combinational
     
     For each d in driven:
       For each r in read:
         If d ≠ r:  # Avoid self-loops
           Add edge(r → d, type=edge_type, source=B.id)

5. Identify clock domains:
   For each clock C:
     Find all sequential blocks using C
     Collect all signals driven by those blocks
     domain[C] = {driven_signals}
```

### Node Styling Logic

```python
if node.type == 'input':
    shape = 'diamond', color = blue, size = 25
elif node.type == 'output':
    shape = 'triangle', color = red, size = 25
elif node.type == 'register':
    shape = 'box', color = green, size = 20
    # Override color if in specific clock domain
    if node in clock_domain[clk]:
        color = clock_colors[clk]
elif node.type == 'wire':
    # Check if combinational
    if has_combinational_edge(node):
        shape = 'ellipse', color = orange, size = 15
    else:
        shape = 'dot', color = gray, size = 10
```

### Edge Styling Logic

```python
if edge.type == 'sequential':
    color = green, width = 2, dashes = False (solid)
elif edge.type == 'combinational':
    color = orange, width = 1, dashes = True (dashed)
```

---

## Combinational Logic Clustering

When **"Cluster Combinational Logic"** is enabled:

### What Gets Clustered?
- All `wire` signals involved in `assign` statements
- Signals driven by combinational `always @(*)` blocks
- Signals that are purely combinational (no register in path)

### Visual Effect
- PyVis groups these nodes together
- They appear as a "cloud" or cluster in the visualization
- Separate from sequential elements and I/O ports

### Algorithm
```python
for node in graph.nodes:
    if node.type == 'wire':
        if is_involved_in_combinational_logic(node):
            assign_group(node, group='combinational')
    elif node.type == 'register':
        # Group by clock domain
        for clk in clock_domains:
            if node in clock_domains[clk]:
                assign_group(node, group=f'clk_{clk}')
```

---

## Sequential Elements Visualization

### Sequential vs. Combinational

| Aspect | Sequential | Combinational |
|--------|-----------|---------------|
| **Shape** | Rectangle (Box) | Ellipse/Circle |
| **Edge** | Solid line | Dashed line |
| **Color** | Green (or clock domain color) | Orange |
| **Meaning** | Has memory (flip-flop) | Pure logic (gates) |

### Sequential Element Detection

An element is classified as **sequential** if:
1. Declared as `reg` in Verilog
2. Driven by an `always @(posedge clk)` or `always @(negedge clk)` block
3. Part of an asynchronous reset pattern

```verilog
// Sequential - will be a GREEN BOX
reg data_reg;
always @(posedge clk) begin
    data_reg <= data_in;
end

// Combinational - will be an ORANGE ELLIPSE
wire result;
assign result = a & b | c;
```

---

## Clock Domain Identification

### Algorithm

```
For each detected clock signal clk:
    clock_domain[clk] = []
    
    For each sequential always block B:
        If clk appears in B.sensitivity_list:
            Add all B.driven_signals to clock_domain[clk]
    
    Remove duplicates from clock_domain[clk]
```

### Example

```verilog
module multi_clock (
    input clk_fast,
    input clk_slow,
    input [7:0] data,
    output reg [7:0] out_fast,
    output reg [7:0] out_slow
);

// Clock Domain 1: clk_fast
always @(posedge clk_fast) begin
    out_fast <= data;
end

// Clock Domain 2: clk_slow
always @(posedge clk_slow) begin
    out_slow <= data;
end

endmodule
```

**Visualization:**
- `out_fast` register: Colored with clock_domain[clk_fast] color (e.g., #FF6B6B)
- `out_slow` register: Colored with clock_domain[clk_slow] color (e.g., #4ECDC4)
- **Clearly shows the two separate clock domains**

---

## Use Cases

### 1. **Understanding Signal Dependencies**
- **How:** Follow edges from inputs to outputs
- **Look for:** Long combinational paths (multiple dashed edges in sequence)
- **Action:** Consider adding pipeline stages

### 2. **Identifying Clock Domain Crossings (CDC)**
- **How:** Look for edges connecting different colored boxes
- **Problem:** Edge from red register to blue register = CDC
- **Action:** Add synchronizers or async FIFOs

### 3. **Finding Combinational Loops**
- **How:** Look for cycles in the graph (edge returns to starting node)
- **Visual:** Dashed orange edges forming a loop
- **Problem:** CRITICAL - synthesis will fail
- **Action:** Break loop with register

### 4. **Verifying Pipeline Structure**
- **How:** Look for chain of green boxes (registers) with sequential edges
- **Visual:** Input → Box → Box → Box → Output
- **Validation:** Count stages matches expected pipeline depth

### 5. **Analyzing Fan-Out**
- **How:** Count edges leaving a single node
- **Visual:** One node with many outgoing edges
- **Problem:** High fan-out may cause timing issues
- **Action:** Add buffers or replicate signal

### 6. **Detecting Unused Signals**
- **How:** Look for isolated nodes with no incoming or outgoing edges
- **Visual:** Floating nodes disconnected from main graph
- **Action:** Remove dead code

---

## Interactive Features

### PyVis Network Interactivity

The visualization is fully **interactive** with the following controls:

#### Mouse Controls
- **Left Click + Drag**: Pan the canvas
- **Scroll Wheel**: Zoom in/out
- **Right Click**: Context menu (browser default)
- **Hover over Node**: Show tooltip with:
  - Signal name
  - Node type (input/output/register/wire)
  - Element type (port/signal)

#### Keyboard Controls (when canvas focused)
- **Arrow Keys**: Pan view
- **+/-**: Zoom in/out

#### Physics Controls
- **Auto-stabilize**: Graph will animate to find optimal layout
- **Freeze**: Click "Stop Physics" in controls to freeze layout
- **Drag Node**: Manually reposition nodes (only works when physics is off)

---

## Troubleshooting

### Problem: "PyVis library not installed"

**Solution:**
```bash
pip install pyvis
# or
pip install -r requirements.txt
```

### Problem: Graph is too cluttered

**Solutions:**
1. Disable "Show Signal Names" for cleaner view
2. Switch to "Hierarchical" layout
3. Enable "Cluster Combinational Logic"
4. Filter: Modify code to only show critical signals

### Problem: Can't see any nodes

**Causes:**
- No signals in the RTL file
- Parsing error (check console)
- All nodes off-screen (try zooming out)

**Solution:**
- Check "Graph Statistics" panel for node count
- Use "Fit to Screen" button (if available)
- Reload the page

### Problem: Edges are hard to distinguish

**Solutions:**
- Use "Hierarchical" layout (clearer separation)
- Look at edge color: Green = sequential, Orange = combinational
- Check "Legend" panel for reference

---

## Advanced Configuration

### Customizing Node Appearance

Edit [rtl_analyzer.py](rtl_analyzer.py) lines 1278-1328:

```python
# Change input port color
if node_type == 'input':
    color = '#YOUR_COLOR_HEX'  # Default: '#3498DB'
    shape = 'diamond'  # Options: diamond, dot, star, triangle, box, ellipse
    size = 25  # Pixel size
```

### Customizing Layout Physics

Edit [rtl_analyzer.py](rtl_analyzer.py) lines 1221-1265:

```python
net.set_options("""
{
  "physics": {
    "forceAtlas2Based": {
      "gravitationalConstant": -50,  # Increase for more spacing
      "springLength": 100,           # Edge length
      "springConstant": 0.08         # Edge stiffness
    }
  }
}
""")
```

### Adding Custom Node Groups

```python
# Group by custom criteria
if signal_is_critical(node):
    net.add_node(node_name, ..., group='critical_path')
```

---

## Performance Considerations

### Large Designs (>500 nodes)

**Recommendations:**
1. Use "Hierarchical" layout (fastest)
2. Disable physics after initial layout
3. Hide signal names
4. Consider filtering to show only critical paths

### Memory Usage

- **Small design (<100 nodes)**: <50 MB
- **Medium design (100-500 nodes)**: 50-200 MB
- **Large design (>500 nodes)**: 200 MB - 1 GB

### Browser Compatibility

| Browser | Support | Performance |
|---------|---------|-------------|
| **Chrome** | ✅ Excellent | Fast |
| **Firefox** | ✅ Good | Moderate |
| **Edge** | ✅ Good | Fast |
| **Safari** | ⚠️ Limited | Slow |

---

## Export and Sharing

### Export Options

1. **Screenshot**: Right-click graph → "Save Image As"
2. **HTML File**: 
   ```python
   net.save_graph("my_rtl_dag.html")
   ```
3. **Graph Data**:
   ```python
   nx.write_gml(analyzer.dag_graph, "my_rtl.gml")
   ```

### Sharing with Team

- **Interactive HTML**: Share the generated HTML file (self-contained)
- **Static Image**: Screenshot for presentations/documentation
- **Graph Data**: Export .gml file for Gephi/Cytoscape analysis

---

## Examples

### Example 1: Simple Counter

```verilog
module counter (
    input clk,
    input rst,
    output reg [7:0] count
);

always @(posedge clk or posedge rst) begin
    if (rst)
        count <= 0;
    else
        count <= count + 1;
end

endmodule
```

**DAG Visualization:**
```
🔷 clk (Diamond, Blue)
   ↓ (Solid Green)
🟩 count (Box, Green)
   ↓ (Dashed Orange - feedback)
🟠 count+1 (Ellipse, Orange)
   ↓ (Solid Green)
🟩 count (Box, Green)
   ↓ (Solid Green)
🔺 count (Triangle, Red)
```

### Example 2: Pipeline with CDC

```verilog
module pipeline_cdc (
    input clk_a,
    input clk_b,
    input [7:0] data_in,
    output reg [7:0] data_out
);

reg [7:0] stage1;  // Clock domain A
reg [7:0] stage2;  // Clock domain B

always @(posedge clk_a)
    stage1 <= data_in;

always @(posedge clk_b)
    stage2 <= stage1;  // ⚠️ CDC here!

assign data_out = stage2;

endmodule
```

**DAG Visualization:**
```
🔷 data_in (Diamond, Blue)
   ↓ (Solid Green)
🟩 stage1 (Box, Color1 - clk_a domain)
   ↓ (Solid Green) ⚠️ CROSSES CLOCK DOMAIN
🟩 stage2 (Box, Color2 - clk_b domain)
   ↓ (Dashed Orange)
🔺 data_out (Triangle, Red)
```

**Visual Clue**: The edge from Color1 box to Color2 box immediately shows the CDC issue!

---

## Best Practices

1. **Start with Hierarchical Layout** - Best default view
2. **Use Clustering** - Reduces visual clutter
3. **Check Clock Domains First** - Identify CDC issues early
4. **Follow Critical Paths** - Trace from input to output
5. **Look for Symmetry** - Well-designed RTL often has symmetric graphs
6. **Isolate Issues** - Use filters to focus on problem areas
7. **Export for Documentation** - Capture screenshots for design reviews

---

## Comparison with Other Tools

| Feature | RTL Analyzer DAG | Synopsys Design Vision | Vivado Schematic | Modelsim Wave |
|---------|-----------------|----------------------|------------------|---------------|
| **Interactive** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **Clock Domains** | ✅ Color-coded | ⚠️ Limited | ⚠️ Manual | ❌ N/A |
| **Combinational Clustering** | ✅ Yes | ❌ No | ❌ No | ❌ N/A |
| **Free/Open** | ✅ Yes | ❌ No | ❌ No (license) | ❌ No (license) |
| **RTL Level** | ✅ Yes | ⚠️ Gate-level | ✅ Yes | ⚠️ Simulation only |
| **Export HTML** | ✅ Yes | ❌ No | ❌ No | ❌ No |

---

## Future Enhancements

Planned features for future releases:

- [ ] **Critical Path Highlighting**: Auto-highlight longest combinational path
- [ ] **Timing Annotation**: Show estimated delays on edges
- [ ] **Filtering Controls**: Show/hide specific signal types
- [ ] **Diff View**: Compare two versions of RTL side-by-side
- [ ] **3D Visualization**: Multi-layer view for complex hierarchies
- [ ] **Export to Graphviz**: Generate DOT files for publication
- [ ] **Animation**: Show data flow propagation over time

---

## References

- **NetworkX Documentation**: https://networkx.org/
- **PyVis Documentation**: https://pyvis.readthedocs.io/
- **IEEE 1364-2005**: Verilog HDL Standard
- **Graph Theory**: Introduction to Graph Theory by Douglas West

---

**Document Version:** 1.0  
**Last Updated:** January 22, 2026  
**Author:** RTL Analyzer Development Team
