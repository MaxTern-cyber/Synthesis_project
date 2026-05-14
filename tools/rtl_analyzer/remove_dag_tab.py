"""
Script to remove DAG visualization tab from rtl_analyzer.py
"""

with open('rtl_analyzer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the start and end of the DAG visualization section
start_line = None
end_line = None

for i, line in enumerate(lines):
    if '# ===== TAB 8: DAG Visualization =====' in line:
        start_line = i
    if start_line is not None and '# ===== TAB' in line and i > start_line:
        end_line = i
        break

if start_line and end_line:
    print(f"Found DAG visualization section from line {start_line+1} to {end_line}")
    print(f"Removing {end_line - start_line} lines...")
    
    # Remove the section
    new_lines = lines[:start_line] + lines[end_line:]
    
    # Write back
    with open('rtl_analyzer.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ DAG visualization tab removed successfully!")
    print(f"   Old file: {len(lines)} lines")
    print(f"   New file: {len(new_lines)} lines")
else:
    print("❌ Could not find DAG visualization section")
