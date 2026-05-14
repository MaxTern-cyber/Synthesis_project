# ðŸ“ RTL Analyzer - Advanced Verilog RTL Analysis Tool

A comprehensive analyzer specifically designed for **RTL (Register Transfer Level)** Verilog code, not gate-level netlists.

---

## ðŸŽ¯ Key Difference: RTL vs Netlist Analysis

| Aspect | **Netlist Analysis** (demo3/demo4) | **RTL Analysis** (this tool) |
|--------|-----------------------------------|------------------------------|
| **Input** | Synthesized gate-level netlist (.v) | Behavioral RTL code (.v) |
| **Structure** | Gate instances (AND, NAND, DFF) | always blocks, assign statements |
| **Focus** | Connectivity, fanout, loops | FSMs, pipelines, coding style |
| **Constructs** | Primitive gates | if/else, case, for, while |
| **Analysis** | Timing paths, congestion | Synthesizability, best practices |

---

## âœ¨ RTL-Specific Features

### 1. **Behavioral Block Analysis**
- âœ… Classifies `always` blocks:
  - Sequential (posedge/negedge)
  - Combinational (sensitivity lists)
  - Async reset detection
- âœ… Identifies driven and read signals
- âœ… Detects blocking vs non-blocking assignments
- âœ… Warns about mixed assignment styles

### 2. **Finite State Machine (FSM) Detection**
- âœ… Automatically detects FSM candidates
- âœ… Identifies state variables
- âœ… Extracts state definitions (parameters)
- âœ… Counts total states
- âœ… Provides FSM synthesis recommendations

### 3. **Pipeline & Register Chain Analysis**
- âœ… Detects multi-stage pipelines
- âœ… Identifies stage naming conventions:
  - `signal_stage1`, `signal_stage2`, ...
  - `data_s1`, `data_s2`, ...
  - `pipe1`, `pipe2`, ...
- âœ… Visualizes pipeline depth
- âœ… Tracks data flow through stages

### 4. **Clock & Reset Detection**
- âœ… Automatically identifies clock signals
- âœ… Detects reset signals (active high/low)
- âœ… Classifies clocking methodology
- âœ… Warns about missing clock/reset

### 5. **Code Quality & Best Practices**
- âœ… **Multiple Driver Detection**: Signals driven in multiple always blocks (ERROR)
- âœ… **Assignment Style Checking**:
  - Warns about blocking (=) in sequential logic
  - Warns about non-blocking (<=) in combinational logic
  - Detects mixed assignments (ERROR)
- âœ… **Latch Inference Detection** (incomplete sensitivity lists)
- âœ… **Large Block Warning**: Flags >100 line always blocks
- âœ… **Synthesis Readiness Score**

### 6. **Module Hierarchy Analysis**
- âœ… Extracts submodule instantiations
- âœ… Port connection analysis
- âœ… Hierarchy visualization
- âœ… Instance count by module type

### 7. **Port & Signal Analysis**
- âœ… Complete port interface analysis (input/output/inout)
- âœ… Signal width extraction
- âœ… Wire vs Reg classification
- âœ… Parameter tracking
- âœ… Export to CSV for documentation

---

## ðŸš€ Quick Start

### Installation

```bash
cd rtl_analyzer
pip install -r requirements.txt
```

### Run the Analyzer

```bash
streamlit run rtl_analyzer.py --server.port 8700
```

Access at: **http://localhost:8700**

---

## ðŸ“‹ Feature Comparison with Commercial Tools

| Feature | RTL Analyzer | Synopsys Design Compiler | Cadence Genus |
|---------|--------------|-------------------------|---------------|
| **Cost** | **FREE** | $100K+ | $150K+ |
| **FSM Detection** | âœ… Automatic | âœ… Comprehensive | âœ… Comprehensive |
| **Coding Style Check** | âœ… Yes | âŒ No | âŒ No |
| **Pipeline Visualization** | âœ… Yes | âŒ Limited | âŒ Limited |
| **Multiple Driver Detection** | âœ… Yes | âœ… During elaboration | âœ… During elaboration |
| **Behavioral Analysis** | âœ… Yes | âŒ Only synthesizes | âŒ Only synthesizes |
| **Assignment Style Check** | âœ… Yes | âŒ No | âŒ No |
| **Learning Curve** | 5 minutes | 2-4 weeks | 2-4 weeks |
| **Use Case** | **Pre-synthesis analysis** | Production synthesis | Production synthesis |

---

## ðŸ“Š Analysis Tabs

### Tab 1: Overview ðŸ“Š
- Module name and statistics
- Port counts (input/output/inout)
- Signal counts (wire/reg)
- Always block summary
- Clock/reset detection
- Code quality summary
- Visual pie charts

### Tab 2: Ports & Signals ðŸ”Œ
- Complete port listing with direction and width
- Internal signal declarations
- Parameter values
- Export to CSV

### Tab 3: Always Blocks âš™ï¸
- Block-by-block analysis
- Type classification (sequential/combinational)
- Sensitivity list display
- Driven vs read signals
- Blocking/non-blocking usage
- Content preview

### Tab 4: FSM Detection ðŸ”„
- Automatic FSM candidate identification
- State variable detection
- State enumeration extraction
- State count metrics
- Reachability recommendations

### Tab 5: Pipeline Analysis ðŸ“ˆ
- Register chain detection
- Pipeline depth metrics
- Stage-by-stage signal tracking
- Visual pipeline flow

### Tab 6: Code Quality âš ï¸
- Critical errors (multiple drivers)
- Warnings (coding style issues)
- Informational messages
- Best practice recommendations
- Export detailed report

### Tab 7: Module Hierarchy ðŸ—ï¸
- Submodule instantiations
- Instance counts by type
- Port connection details
- Hierarchy visualization

---

## ðŸ” What Makes This RTL-Focused?

### RTL Constructs Analyzed:

**1. Behavioral Modeling:**
```verilog
always @(posedge clk or negedge rst_n) begin
    // Sequential logic detected
    if (!rst_n)
        state <= IDLE;
    else
        state <= next_state;
end
```

**2. FSM Detection:**
```verilog
parameter IDLE = 2'b00;
parameter ACTIVE = 2'b01;
parameter DONE = 2'b10;

reg [1:0] state, next_state;  // FSM detected!

case (state)
    IDLE: next_state = ACTIVE;
    ACTIVE: next_state = DONE;
    DONE: next_state = IDLE;
endcase
```

**3. Pipeline Chains:**
```verilog
reg [7:0] data_stage1, data_stage2, data_stage3;  // 3-stage pipeline detected!

always @(posedge clk) begin
    data_stage1 <= input_data;
    data_stage2 <= data_stage1;
    data_stage3 <= data_stage2;
end
```

**4. Coding Style Issues:**
```verilog
// ERROR: Multiple drivers detected!
always @(posedge clk)
    counter <= counter + 1;

always @(posedge rst)
    counter <= 0;  // Same signal driven here!
```

---

## ðŸŽ¯ Use Cases

### 1. **Pre-Synthesis Verification**
- Check RTL for coding errors before synthesis
- Identify multiple drivers
- Verify FSM completeness

### 2. **Code Review**
- Automated coding style checking
- Best practices enforcement
- Consistent naming conventions

### 3. **Design Understanding**
- Quickly understand large RTL codebases
- Identify pipelines and FSMs
- Visualize module hierarchy

### 4. **Educational**
- Learn RTL coding best practices
- Understand FSM design patterns
- Study pipeline architectures

### 5. **Documentation**
- Auto-generate signal lists
- Export port interfaces
- Create design summaries

---

## ðŸ† Best Practices Checked

### âœ… Sequential Logic Rules:
1. Use **non-blocking assignments** (`<=`)
2. Include all clock and reset in sensitivity list
3. Async reset should be in sensitivity list

### âœ… Combinational Logic Rules:
1. Use **blocking assignments** (`=`)
2. Complete sensitivity list or use `always @(*)`
3. Avoid latches (specify all conditions)

### âœ… FSM Design Rules:
1. Separate state register and next-state logic
2. Use parameters or localparams for states
3. Default case to prevent latches

### âœ… General Rules:
1. One signal driven in only one always block
2. Avoid mixing blocking and non-blocking
3. Keep always blocks < 100 lines

---

## ðŸ†š When to Use Each Tool

### Use **RTL Analyzer** when:
- âœ… Writing or reviewing RTL code
- âœ… Pre-synthesis verification
- âœ… Learning Verilog best practices
- âœ… Checking coding style
- âœ… Understanding design structure

### Use **Netlist Analyzer** (demo4) when:
- âœ… Post-synthesis analysis
- âœ… Timing path analysis
- âœ… Congestion prediction
- âœ… Clock domain crossings
- âœ… Gate-level debugging

---

## ðŸ“š RTL Analysis Best Practices from Industry

### From IEEE & Industry Standards:

**1. Clocking:**
- âœ… Single clock edge per always block
- âœ… Avoid gated clocks in RTL
- âœ… Document all clock domains

**2. Reset:**
- âœ… Async reset for critical paths
- âœ… Synchronous reset for most logic
- âœ… Active-low is more common (rst_n)

**3. Naming Conventions:**
- âœ… `_n` or `_b` for active-low signals
- âœ… `clk_<domain>` for multiple clocks
- âœ… `next_<signal>` for FSM next-state

**4. Synthesis:**
- âœ… Avoid initial blocks (not synthesizable)
- âœ… Avoid delays (#10) in RTL
- âœ… Use parameters, not `define macros

---

## ðŸ”¬ Advanced Detection Algorithms

### FSM Detection:
```python
1. Scan for signals with "state" in name
2. Find case statements on these signals
3. Extract parameter definitions with "STATE"
4. Count unique states
5. Verify all states are reachable
```

### Pipeline Detection:
```python
1. Pattern match: signal_stage<N>, signal_s<N>, signal_p<N>
2. Group by base name
3. Sort by stage number
4. Verify sequential staging (1, 2, 3, ...)
5. Report pipeline depth
```

### Multiple Driver Detection:
```python
1. For each always block:
    a. Extract driven signals (LHS of assignments)
2. Build map: signal â†’ [list of always blocks]
3. If len(blocks) > 1: ERROR
```

---

## ðŸ“¦ Sample Analysis Output

```
Module: sample_counter
â”œâ”€â”€ Ports: 35 (12 inputs, 23 outputs)
â”œâ”€â”€ Internal Signals: 28 (12 wires, 16 regs)
â”œâ”€â”€ Always Blocks: 1
â”‚   â””â”€â”€ Sequential with async reset
â”œâ”€â”€ Clock Domains: 1 (clk)
â”œâ”€â”€ Reset Signals: 1 (rst_n, active-low)
â”œâ”€â”€ FSM Candidates: 0
â”œâ”€â”€ Pipeline Chains: 0
â”œâ”€â”€ Module Instances: 0 (leaf module)
â”œâ”€â”€ Assign Statements: 8
â””â”€â”€ Code Quality: âœ… No issues detected
```

---

## ðŸš§ Future Enhancements

- [ ] **Latch inference detection** (incomplete if/case)
- [ ] **Coverage analysis** (case statement completeness)
- [ ] **X-propagation analysis**
- [ ] **Formal property suggestions**
- [ ] **Auto-fix suggestions** (with code generation)
- [ ] **SVA assertion generation**
- [ ] **UPF power intent extraction**
- [ ] **Synthesis constraint generation** (SDC)

---

## ðŸŽ“ Educational Resources

### Included Examples:
- Coding style do's and don'ts
- FSM design patterns
- Pipeline implementation best practices
- Clock domain crossing techniques

### Recommended Reading:
1. **"RTL Modeling with SystemVerilog"** - Stuart Sutherland
2. **IEEE 1364-2005** - Verilog Standard
3. **Synopsys Design Compiler User Guide** - Chapter on RTL guidelines

---

## ðŸ“„ License

MIT License - Free for educational and commercial use

---

## ðŸ™‹ Support & Contribution

- **Issues**: Report bugs or request features
- **PRs**: Contributions welcome!
- **Documentation**: Help improve this README

---

## ðŸŽ‰ Summary

This **RTL Analyzer** fills the gap between:
- âŒ Basic text editor (no analysis)
- âŒ Commercial synthesis tools (expensive, complex)
- âœ… **THIS TOOL**: Free, focused, educational RTL analysis

**Perfect for:**
- Students learning Verilog
- Engineers doing code review
- Teams enforcing coding standards
- Anyone who wants to understand RTL without synthesis

---

**Happy Analyzing! ðŸ“ðŸš€**
