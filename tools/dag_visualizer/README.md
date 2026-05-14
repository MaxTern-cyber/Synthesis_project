# 🌐 DAG Visualizer

Standalone tool for generating interactive 3D DAG visualizations from Verilog netlists.

## Features

- **Interactive 3D Graph**: Pan, zoom, drag nodes
- **Color-Coded Gates**: Different colors for different gate types
- **Physics Simulation**: Realistic node behavior
- **Standalone HTML**: No dependencies needed to view
- **Export & Share**: Save visualization as HTML file

## Launch

```powershell
cd dag_visualizer
streamlit run dag_visualizer.py --server.port 8650
```

**Access:** http://localhost:8650

## Usage

1. Upload netlist .v file or load from workspace
2. Click "Parse & Build DAG"
3. Configure output filename and physics settings
4. Click "Generate Interactive HTML"
5. Open the generated HTML file in your browser

## Color Legend

- **Teal**: Flip-flops/Registers
- **Red**: NAND gates
- **Orange**: NOR gates
- **Blue**: AND gates
- **Yellow**: OR gates
- **Purple**: XOR/XNOR gates
- **Mint**: Inverters
- **Peach**: Multiplexers
- **Light Green**: Other gates

## Output

Generates timestamped HTML files like `dag_visualization_20260122_143045.html` that can be:
- Opened directly in any browser
- Shared with team members
- Embedded in documentation
- Viewed offline (no internet needed)

## Benefits vs Embedded Visualization

- **Better Performance**: No Streamlit embedding overhead
- **Full Screen**: Utilize entire browser window
- **Portable**: Share HTML files easily
- **Professional**: Clean, standalone output
