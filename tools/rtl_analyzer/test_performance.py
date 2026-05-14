"""
Quick test script to verify DAG visualization performance optimizations
"""

# Test that the HTML file has the loading bar and controls
import os

output_file = "possible_dag_rep.html"

if os.path.exists(output_file):
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for loading bar components
    checks = {
        "Loading Overlay": "id=\"loading-overlay\"" in content,
        "Loading Bar": "id=\"loading-bar\"" in content,
        "Loading Percentage": "id=\"loading-percentage\"" in content,
        "Control Panel": "id=\"control-panel\"" in content,
        "Freeze Button": "id=\"freeze-btn\"" in content,
        "Reset Zoom Button": "id=\"reset-btn\"" in content,
        "Stabilization Progress": "stabilizationProgress" in content,
        "Auto Freeze": "setTimeout(togglePhysics" in content,
    }
    
    print("🔍 DAG Visualization Performance Checks:")
    print("=" * 50)
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}: {'Present' if result else 'MISSING'}")
        if not result:
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("✅ All performance optimizations are present!")
        print("\n📊 Features included:")
        print("  • Loading progress bar (0-100%)")
        print("  • Auto-freeze physics after load")
        print("  • Freeze/Enable Physics button")
        print("  • Reset Zoom button")
        print("  • 30-second timeout fallback")
        print("\n💡 Tip: Open possible_dag_rep.html in browser to test!")
    else:
        print("⚠️ Some optimizations are missing. Regenerate the DAG.")
    
else:
    print("❌ possible_dag_rep.html not found.")
    print("💡 Generate a DAG visualization first from the RTL Analyzer.")
