# Quick Start: DAG Visualization

## 🚀 Generate DAG in 3 Steps

### Step 1: Navigate to folder
```bash
cd rtl_analyzer
```

### Step 2: Run generator
```bash
python generate_dag_visualization.py your_file.v
```

### Step 3: Open HTML
```bash
# Windows
start dag_visualization.html

# Linux/Mac
open dag_visualization.html
```

## ⚡ Examples

### Basic Usage
```bash
python generate_dag_visualization.py netlist.v
```

### Custom Output
```bash
python generate_dag_visualization.py netlist.v --output my_dag.html
```

### Force Layout
```bash
python generate_dag_visualization.py netlist.v --layout force
```

### Large Designs (Hide Labels)
```bash
python generate_dag_visualization.py big_design.v --no-labels
```

## 💡 Windows Users

Use the batch file for automatic opening:
```cmd
generate_dag.bat your_file.v
```

## 📝 What You'll See

The generated HTML includes:
- **Loading Bar**: Shows 0-100% progress
- **Interactive Graph**: Zoom, pan, drag nodes
- **Control Buttons**:
  - ❄️ Freeze Layout - Stop physics for smooth interaction
  - 🔍 Reset Zoom - Fit entire graph in view
- **Info Panel**: Module name, node/edge counts

## 🎨 Node Colors & Shapes

- 🔷 **Diamond (Blue)** = Input Port
- 🔺 **Triangle (Red)** = Output Port
- ◻️ **Box (Green)** = Register/Sequential
- ⚪ **Ellipse (Orange)** = Combinational Logic

## 🔧 Troubleshooting

### "Module not found: pyvis"
```bash
pip install pyvis networkx
```

### File Not Found
Check the path to your Verilog file

### Slow Loading
- Use `--no-labels` for large designs
- Try `--layout hierarchical` (faster)
- Wait for auto-freeze after 2 seconds

## 📚 More Info

- Full documentation: [DAG_GENERATOR_README.md](DAG_GENERATOR_README.md)
- Performance guide: [PERFORMANCE_OPTIMIZATIONS.md](PERFORMANCE_OPTIMIZATIONS.md)
- Changes summary: [DAG_SEPARATION_SUMMARY.md](DAG_SEPARATION_SUMMARY.md)

---

**That's it! Simple and fast.** 🎉
