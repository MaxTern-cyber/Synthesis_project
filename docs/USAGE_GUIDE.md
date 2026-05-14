# ðŸ“– Usage Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Hardware Debug Assistant Tutorial](#hardware-debug-assistant-tutorial)
3. [Netlist Analyzer Tutorial](#netlist-analyzer-tutorial)
4. [Advanced Workflows](#advanced-workflows)
5. [Tips & Best Practices](#tips--best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Installation

#### Step 1: Prerequisites
- Python 3.14 or higher
- Modern web browser (Chrome, Firefox, Edge, Safari)
- 4GB RAM minimum

#### Step 2: Install Dependencies
```bash
cd Synthesis_project
pip install -r requirements.txt
```

Expected output:
```
Successfully installed streamlit-1.53.0 networkx-3.0 pandas-2.0.0 ...
```

#### Step 3: Verify Installation
```bash
python -c "import streamlit, networkx, pandas; print('âœ… All dependencies installed')"
```

### Launching Applications

#### Quick Launch (Both Apps)
```bash
python LAUNCH_BOTH.py
```

This opens:
- **Hardware Debug Assistant**: http://localhost:8610
- **Netlist Analyzer**: http://localhost:8550

#### Individual Launch

**Hardware Debug Assistant Only**:
```bash
cd demo3
streamlit run debug_assistant.py --server.port 8610
```

**Netlist Analyzer Only**:
```bash
cd demo4
streamlit run local_analyzer.py --server.port 8550
```

---

## Hardware Debug Assistant Tutorial

### Tutorial 1: Basic Signal Tracing

**Objective**: Find and analyze a specific signal

**Steps**:

1. **Launch the App**
   ```bash
   python LAUNCH_BOTH.py
   ```
   Navigate to http://localhost:8610

2. **Load Netlist**
   - The sample `<your_netlist.v>` auto-loads on startup
   - Status shows: "âœ… your_netlist.v is loaded and parsed!"
   - You'll see gate count (e.g., 2000+ gates)

3. **Search for a Signal**
   - Go to "ðŸ” Signal Trace & Analysis" tab
   - Enter signal name: `data_out` (or any signal from your netlist)
   - Click "ðŸ” Trace Signal"

4. **Interpret Results**
   ```
   Signal: data_out
   Type: wire
   Drivers: [AND2_g_1234]
   Readers: [DFF_reg_456, NAND_g_789, OR_g_101]
   Fanout: 3 ðŸŸ¢ GOOD
   ```

   **Health Indicators**:
   - ðŸŸ¢ **GOOD** (0-10): Healthy fanout
   - ðŸŸ¡ **MODERATE** (10-20): Watch this signal
   - ðŸŸ  **WARNING** (20-30): Consider buffering
   - ðŸ”´ **CRITICAL** (>30): Needs immediate attention

5. **View Load Estimation**
   ```
   Estimated Capacitive Load: 6.5 fF
   
   Load Breakdown:
   - DFF_reg_456: 2.5 fF
   - NAND_g_789: 1.2 fF
   - OR_g_101: 2.8 fF
   
   Timing Impact: +0.065 ns
   ```

---

### Tutorial 2: High-Fanout Optimization

**Objective**: Identify and optimize high-fanout signals

**Steps**:

1. **Find Critical Signals**
   - In "Signal Trace" tab
   - Try searching: `clk`, `reset`, `enable` (common high-fanout signals)

2. **Analyze Fanout**
   ```
   Signal: clk
   Fanout: 45 ðŸ”´ CRITICAL
   Estimated Load: 112.5 fF
   Timing Impact: +1.125 ns âš ï¸
   ```

3. **Get Buffer Suggestions**
   - Scroll to "Buffer Insertion Suggestions" section
   - See recommended buffer tree:
   
   ```
   Suggested Buffer Tree:
   
   clk â†’ BUF_1 â†’ [gates 1-15]
       â†’ BUF_2 â†’ [gates 16-30]
       â†’ BUF_3 â†’ [gates 31-45]
   
   Improvement: 67% fanout reduction per buffer
   New timing: +0.375 ns (66% improvement)
   ```

4. **Export Results**
   - Click "ðŸ“¥ Export Analysis Report"
   - Saves detailed CSV with all metrics

---

### Tutorial 3: Connectivity Debugging

**Objective**: Verify signal connectivity

**Steps**:

1. **Check Driver**
   - Search signal: `my_signal`
   - Look at "Drivers" field
   - **Expected**: 1 driver (single source)
   - **Problem**: 0 drivers = unconnected/floating signal
   - **Problem**: 2+ drivers = bus contention

2. **Check Readers**
   - Look at "Readers" field
   - **Expected**: 1+ readers
   - **Warning**: 0 readers = unused signal (dead code)

3. **Trace Full Path**
   - Start with input signal
   - Trace each output through the chain
   - Verify continuous connectivity

**Example Workflow**:
```
Input Signal â†’ Driver Gate â†’ Intermediate Signal â†’ Reader Gate â†’ Output Signal
                                                                        
data_in â†’ AND_g1 â†’ temp_wire â†’ DFF_reg â†’ q_out
```

---

## Netlist Analyzer Tutorial

### Tutorial 1: Statistical Analysis

**Objective**: Get design overview and statistics

**Steps**:

1. **Launch and Load**
   - Navigate to http://localhost:8550
   - Sample netlist auto-loads
   - Go to "ðŸ“Š Statistical Analysis" tab

2. **View Key Metrics**
   ```
   ðŸ“ˆ Statistics:
   - Total Lines: 9,005
   - Modules: 1
   - Signals: 3,500
   - Gate Instances: 2,000
   - DAG Nodes: 2,000
   - DAG Edges: 5,800
   ```

3. **Analyze Gate Distribution**
   ```
   âš¡ Gate Distribution:
   - DFF: 450 instances (22.5%)
   - AND2: 380 instances (19.0%)
   - NAND2: 320 instances (16.0%)
   - INV: 280 instances (14.0%)
   - OR2: 250 instances (12.5%)
   ...
   ```

4. **Check for Issues**
   - Look for "Unconnected Signals" section
   - Review critical path summary

---

### Tutorial 2: Clock Domain Visualization

**Objective**: Visualize design by clock domains

**Steps**:

1. **Analyze Clock Domains**
   - Go to "ðŸŒ DAG Visualization" tab
   - Scroll to "Advanced Design Analysis"
   - Click "ðŸ•’ Analyze Clock Domains"

2. **Review Results**
   ```
   âœ… Found 2 clock domain(s)
   
   Clock Signal    Registers    Total Nodes
   â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
   clk             400          1,200
   clk_slow        50           180
   ```

3. **Generate Color-Coded DAG**
   - Check â˜‘ï¸ "Color by Clock Domain"
   - Click "ðŸŽ¨ Generate Interactive DAG"
   - Wait for generation (~5 seconds)

4. **Explore Visualization**
   ```
   ðŸŽ¨ Clock Domain Legend:
   
   [Red Box] clk - 1,200 nodes
   [Teal Box] clk_slow - 180 nodes
   ```

5. **Interact with DAG**
   - **Pan**: Click and drag background
   - **Zoom**: Mouse wheel or pinch
   - **Move Node**: Drag individual nodes
   - **Hover**: See gate info (type, domain)
   - **Click**: Highlight connections

6. **Identify Domain Crossings**
   - Look for edges between different colors
   - These are Clock Domain Crossings (CDC)
   - May need synchronizers

---

### Tutorial 3: Combinational Loop Detection

**Objective**: Find design errors before synthesis

**Steps**:

1. **Run Loop Detection**
   - Go to "DAG Visualization" tab
   - Click "ðŸ”´ Detect Combinational Loops"
   - Wait for analysis

2. **Interpret Results**

   **Good Design**:
   ```
   âœ… No combinational loops detected
   ```

   **Problem Found**:
   ```
   âš ï¸ Found 1 combinational loop(s)!
   
   âŒ Loop 1: 4 gates involved - CRITICAL
   
   Loop Path: gate_A â†’ gate_B â†’ gate_C â†’ gate_D â†’ gate_A
   Severity: CRITICAL
   Gate Types: AND, NAND, OR, INV
   
   ðŸ”§ Suggested Fixes:
   - Insert DFF after gate_D to break loop
   - Review logic equations for gate_C
   - Check for unintended feedback
   ```

3. **Apply Fixes**
   - Note the suggested insertion point
   - Modify RTL to add register
   - Re-synthesize and verify

---

### Tutorial 4: Congestion Analysis

**Objective**: Predict routing issues before P&R

**Steps**:

1. **Run Congestion Analysis**
   - Click "ðŸŒ¡ï¸ Identify Congestion"
   - Wait for scoring

2. **Review Hotspots**
   ```
   âš ï¸ Found 5 congestion hotspot(s)
   
   Gate         Type    Score    Fanin    Fanout    Severity
   â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
   mux_g_4567   MUX8    68       8        26        ðŸ”´ CRITICAL
   buf_g_2341   BUF     45       1        22        ðŸŸ  HIGH
   and_g_9876   AND4    38       4        15        ðŸŸ  HIGH
   ```

3. **View Mitigation Strategies**
   ```
   Gate: mux_g_4567 (Score: 68)
   
   Fanin: 8 signals
   Fanout: 26 signals
   
   Suggestions:
   - Insert buffer tree to reduce fanout from 26
   - Consider logic duplication for critical paths
   - High fanin+fanout: review physical constraints
   ```

4. **Plan Optimizations**
   - Add suggested buffers to floorplan
   - Consider gate decomposition
   - Set placement constraints

---

## Advanced Workflows

### Workflow 1: Full Design Review

**Use Case**: Post-synthesis netlist verification

**Steps**:

1. **Load Netlist** (Netlist Analyzer)
   - Upload synthesized .v file
   - Click "Parse & Analyze"

2. **Statistical Check**
   - Review gate counts
   - Check for unexpected types
   - Verify signal connectivity

3. **Loop Detection**
   - Run combinational loop check
   - **Must be zero** for valid design
   - Fix any loops found

4. **Clock Domain Analysis**
   - Identify all clocks
   - Verify register distribution
   - Check for unexpected domains

5. **Critical Path Review**
   - Go to "Analysis" tab
   - View top 10 critical paths
   - Estimate timing

6. **Congestion Check**
   - Run hotspot identification
   - Plan buffer insertion
   - Set constraints for P&R

7. **Generate Documentation**
   - Export DAG visualization
   - Save analysis reports
   - Create review presentation

---

### Workflow 2: Debug Specific Issue

**Use Case**: Signal not behaving as expected

**Steps**:

1. **Identify Signal** (Debug Assistant)
   - Search for problematic signal
   - Verify it exists in netlist

2. **Check Connectivity**
   - Verify driver exists
   - Check reader count
   - Look for floating connections

3. **Trace Backwards** (Netlist Analyzer)
   - Find driver gate in DAG
   - Trace inputs recursively
   - Identify signal source

4. **Trace Forwards**
   - Find all readers
   - Verify expected connections
   - Check for missing loads

5. **Analyze Timing**
   - Check critical paths
   - Estimate delays
   - Identify bottlenecks

6. **Generate Report**
   - Document findings
   - Export path diagrams
   - Recommend fixes

---

### Workflow 3: CDC Verification

**Use Case**: Verify clock domain crossings

**Steps**:

1. **Identify Clocks** (Netlist Analyzer)
   - Run clock domain analysis
   - List all domains
   - Count registers per domain

2. **Visualize Domains**
   - Generate color-coded DAG
   - Look for color transitions
   - Mark CDC points

3. **Check Synchronizers**
   - For each CDC, verify:
     - 2-FF synchronizer present
     - Proper domain
     - No combinational paths

4. **Analyze Gray Codes**
   - For multi-bit crossings
   - Verify Gray encoding
   - Check for race conditions

5. **Document Crossings**
   - List all CDC points
   - Verify each has sync
   - Generate CDC report

---

## Tips & Best Practices

### Performance Tips

1. **Large Netlists**
   - Use lazy parsing first (stats only)
   - Build DAG only when needed
   - Close unused tabs in browser

2. **Faster Analysis**
   - Limit top_n in critical paths (use 5 instead of 20)
   - Use specific signal search vs. browsing all
   - Cache results in session

3. **Memory Management**
   - Close and reopen app for fresh start
   - Clear browser cache if sluggish
   - Process modules individually for huge designs

### Analysis Best Practices

1. **Always Check**
   - Zero combinational loops
   - No floating signals
   - Reasonable fanout (<30 typical)

2. **Before Synthesis**
   - Verify RTL structure
   - Check clock strategy
   - Plan for CDC

3. **After Synthesis**
   - Compare gate counts to expectations
   - Verify optimization didn't break logic
   - Check for unexpected structures

4. **Before P&R**
   - Run congestion analysis
   - Plan buffer locations
   - Set floorplan constraints

### Visualization Tips

1. **DAG Exploration**
   - Start zoomed out for overview
   - Zoom in on areas of interest
   - Use search (Ctrl+F) in browser for gate names

2. **Color Coding**
   - Always use clock domain colors for multi-clock designs
   - Export colored DAG for presentations
   - Screenshot interesting sections

3. **Performance**
   - DAG generation can take 5-10s for 10K gates
   - Don't generate DAG repeatedly
   - Save HTML file for offline viewing

---

## Troubleshooting

### Common Issues

#### Issue: "No gates found"

**Cause**: Netlist format not recognized

**Solutions**:
- Verify Verilog syntax
- Check for `module` keyword
- Ensure gate instantiations present
- Try sample `<your_netlist.v>` to confirm tool works

#### Issue: "DAG generation timeout"

**Cause**: Design too large

**Solutions**:
- Increase timeout in config
- Process modules separately
- Use more powerful machine
- Reduce max_gates limit

#### Issue: "Memory error"

**Cause**: Insufficient RAM

**Solutions**:
- Close other applications
- Use chunked processing
- Upgrade system RAM
- Process smaller sections

#### Issue: "Port already in use"

**Cause**: Previous instance still running

**Solutions**:
```bash
# Windows
netstat -ano | findstr :8610
taskkill /PID <pid> /F

# Mac/Linux
lsof -ti:8610 | xargs kill -9
```

#### Issue: "Module not found"

**Cause**: Missing dependencies

**Solutions**:
```bash
pip install -r requirements.txt --upgrade
```

#### Issue: "Slow performance"

**Cause**: Browser/Python overhead

**Solutions**:
- Close unused browser tabs
- Restart Streamlit app
- Use Chrome (fastest performance)
- Clear browser cache

---

### Getting Help

1. **Check Documentation**
   - Read [DOCUMENTATION.md](DOCUMENTATION.md)
   - Review [README.md](README.md)
   - See [PRESENTATION.md](PRESENTATION.md)

2. **Verify Installation**
   ```bash
   python -c "import streamlit; print(streamlit.__version__)"
   python -c "import networkx; print(networkx.__version__)"
   ```

3. **Test with Sample**
   - Use included `<your_netlist.v>`
   - Verify it works
   - Compare with your netlist

4. **Debug Mode**
   ```bash
   streamlit run debug_assistant.py --logger.level=debug
   ```

---

## Keyboard Shortcuts

### Browser Shortcuts
- `Ctrl+F`: Find in page
- `Ctrl++`: Zoom in
- `Ctrl+-`: Zoom out
- `F5`: Refresh page
- `Ctrl+W`: Close tab

### Streamlit Shortcuts
- `R`: Rerun app
- `C`: Clear cache
- `?`: Show keyboard shortcuts

---

## Appendix: Sample Workflows

### A. Morning Design Review (15 minutes)

```
1. Launch both apps (1 min)
2. Load netlist (auto)
3. Check statistics (2 min)
   - Gate counts match expectations?
   - Any unusual gate types?
4. Run all analyses (5 min)
   - Combinational loops: Must be zero
   - Clock domains: Verify count
   - Congestion: Note hotspots
5. Generate DAG (3 min)
6. Export reports (2 min)
7. Review in team meeting (2 min)
```

### B. Debug Session (30 minutes)

```
1. Identify problem signal (5 min)
2. Search in Debug Assistant (2 min)
3. Check connectivity (5 min)
4. Trace in DAG (10 min)
5. Analyze critical paths (5 min)
6. Document findings (3 min)
```

### C. Pre-Tapeout Verification (1 hour)

```
1. Statistical analysis (10 min)
2. Loop detection (5 min) - MUST PASS
3. Clock domain analysis (15 min)
4. Congestion analysis (15 min)
5. Critical path review (10 min)
6. Generate documentation (5 min)
```

---

**Next Steps**: See [PRESENTATION.md](PRESENTATION.md) for architecture details and presentation materials.
