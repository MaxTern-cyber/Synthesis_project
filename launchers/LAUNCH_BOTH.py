"""
Launch Hardware Debug Assistant and Netlist Analyzer in parallel
"""
import subprocess
import time
import webbrowser
import os

def launch_apps():
    print("🚀 Starting both applications...\n")
    
    # Launch Hardware Debug Assistant (demo3) on port 8610
    demo3_path = os.path.join(os.path.dirname(__file__), "tools/demo3")
    print("📌 Starting Hardware Debug Assistant on port 8610...")
    process1 = subprocess.Popen(
        ["python", "-m", "streamlit", "run", "debug_assistant.py", "--server.port", "8610"],
        cwd=demo3_path,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    # Launch Netlist Analyzer (demo4) on port 8550
    demo4_path = os.path.join(os.path.dirname(__file__), "tools/demo4")
    print("📌 Starting Netlist Analyzer on port 8550...")
    process2 = subprocess.Popen(
        ["python", "-m", "streamlit", "run", "local_analyzer.py", "--server.port", "8550"],
        cwd=demo4_path,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    # Wait for apps to start
    print("\n⏳ Waiting for applications to start...")
    time.sleep(5)
    
    # Open browsers
    print("\n🌐 Opening browsers...\n")
    print("✅ Hardware Debug Assistant: http://localhost:8610")
    webbrowser.open("http://localhost:8610")
    
    time.sleep(2)
    
    print("✅ Netlist Analyzer: http://localhost:8550")
    webbrowser.open("http://localhost:8550")
    
    print("\n" + "="*60)
    print("✅ Both applications are running!")
    print("="*60)
    print("\n📌 URLs:")
    print("   • Hardware Debug Assistant: http://localhost:8610")
    print("   • Netlist Analyzer:        http://localhost:8550")
    print("\n⚠️  Press Ctrl+C in the terminal windows to stop the apps")
    print("="*60 + "\n")

if __name__ == "__main__":
    # Anchor to repo root so 'tools/demo3', 'tools/demo4' paths resolve
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    launch_apps()
