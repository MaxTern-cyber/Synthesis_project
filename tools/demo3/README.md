# ï¿½ Hardware Debug Assistant

A real-time signal tracing and connectivity analysis tool for hardware netlists.

## Features

### ðŸŽ¯ Signal Trace & Analysis
- **Instant Signal Lookup**: Search any signal by name
- **Driver/Reader Identification**: See all connections at a glance
- **Fanout Health Scoring**: 4-level severity indicators
  - ðŸŸ¢ GOOD (0-10): Healthy fanout
  - ðŸŸ¡ MODERATE (10-20): Acceptable range
  - ðŸŸ  WARNING (20-30): Consider buffering
  - ðŸ”´ CRITICAL (>30): Immediate attention needed

### âš¡ Load Estimation
- **28nm CMOS Model**: Industry-standard capacitance values
- **Per-Gate Breakdown**: See load contribution by each gate
- **Timing Impact**: Estimate delay penalties from capacitive loading

### ðŸŒ³ Buffer Planning
- **Automatic Tree Generation**: Balanced buffer insertion strategy
- **Load Clustering**: Optimize buffer placement
- **Before/After Metrics**: Quantify improvements

## Quick Start

### Launch Application
```bash
cd demo3
streamlit run debug_assistant.py --server.port 8610
```

Access at: http://localhost:8610

### Launch with Netlist Analyzer
```bash
# From project root
python LAUNCH_BOTH.py
```

This opens:
- Hardware Debug Assistant: http://localhost:8610
- Netlist Analyzer: http://localhost:8550

## Usage Example

### 1. Load Netlist
The tool auto-loads `your_netlist.v` on startup. You'll see:
```
âœ… your_netlist.v is loaded and parsed!
Total gates: 2000+
```

### 2. Search Signal
Go to "ðŸ” Signal Trace & Analysis" tab:
- Enter signal name (e.g., `data_out`)
- Click "ðŸ” Trace Signal"

### 3. View Results
```
Signal: data_out
Type: wire
Drivers: [AND2_g_1234]
Readers: [DFF_reg_456, NAND_g_789, OR_g_101]
Fanout: 3 ðŸŸ¢ GOOD

Estimated Load: 6.5 fF
Timing Impact: +0.065 ns
```

### 4. High-Fanout Analysis
For critical signals with high fanout:
```
Signal: clk
Fanout: 45 ðŸ”´ CRITICAL
Estimated Load: 112.5 fF
Timing Impact: +1.125 ns âš ï¸

Buffer Suggestions:
  clk â†’ BUF_1 â†’ [gates 1-15]
      â†’ BUF_2 â†’ [gates 16-30]
      â†’ BUF_3 â†’ [gates 31-45]

Improvement: 67% fanout reduction
```

## Use Cases

### Design Engineers
- Quick signal lookup during debug sessions
- Verify connectivity in post-synthesis netlist
- Pre-synthesis fanout checking

### Verification Engineers
- Trace signal paths through design
- Identify unconnected or floating signals
- Validate driver/load relationships

### Physical Design Engineers
- Plan buffer insertion for high-fanout nets
- Estimate capacitive loads for timing analysis
- Identify potential routing bottlenecks

## Technical Details

### Load Model (28nm CMOS)
```
INV/BUF:  0.8 fF
NAND/NOR: 1.2 fF  
AND/OR:   1.5 fF
DFF:      2.5 fF
MUX:      2.0 fF
```

### Timing Penalty
```
delay_penalty = total_load Ã— 0.01 ns/fF
```

### Fanout Health Thresholds
```python
0-10:   GOOD       (green)
10-20:  MODERATE   (yellow)
20-30:  WARNING    (orange)
30+:    CRITICAL   (red)
```

## Dependencies

```
streamlit >= 1.53.0
pandas >= 2.0.0
```

Install via:
```bash
pip install -r ../requirements.txt
```

## Project Structure

```
demo3/
â”œâ”€â”€ debug_assistant.py    # Main application
â”œâ”€â”€ README.md             # This file
â””â”€â”€ ...
```

## Related Tools

**Netlist Analyzer** (demo4): Advanced analysis with clock domains, loop detection, and congestion prediction.

Launch both tools:
```bash
python LAUNCH_BOTH.py
```

## Documentation

- **Main README**: [../README.md](../README.md)
- **Technical Docs**: [../DOCUMENTATION.md](../DOCUMENTATION.md)
- **Usage Guide**: [../USAGE_GUIDE.md](../USAGE_GUIDE.md)
- **Presentation**: [../PRESENTATION.md](../PRESENTATION.md)

## Support

For issues, questions, or feature requests, see the main project documentation
- **Design verification**: Check for multiple drivers
- **Signal tracing**: Follow signals through complex logic
- **Quick reports**: Export signal/gate lists
- **Pattern detection**: Find clocks, resets automatically

### ðŸŽ¨ Demo Comparison:

| Feature | Demo 1 | Demo 2 (DAG Viz) | Demo 3 (Debug) |
|---------|--------|------------------|----------------|
| Visualization | Basic | Interactive DAG | None |
| Signal Trace | No | Limited | Advanced |
| Issue Detection | No | Basic | Comprehensive |
| Fanout Analysis | No | No | Yes |
| Auto-scan | No | No | Yes |
| Speed | Fast | Medium | Fast |
| Best For | Learning | Visualization | Debugging |

### ðŸ”§ Perfect For:
- Debug engineers finding connectivity issues
- Verification teams checking design integrity
- Timing engineers identifying bottlenecks
- Anyone troubleshooting netlists quickly

No API required - 100% local processing!
