"""
SYNTHESIS PROJECT TOOL LAUNCHER
==============================
Clean and simple launcher for all hardware debugging and analysis tools.

Usage:
    python launchers/TOOL_LAUNCHER.py           # Interactive menu
    python launchers/TOOL_LAUNCHER.py --all     # Launch all tools
    python launchers/TOOL_LAUNCHER.py --check   # Check system status
"""

import sys
import subprocess
import os
from pathlib import Path
import webbrowser
import time

# Ensure emoji / Unicode works on Windows cp1252 consoles
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

# Tool configurations
TOOLS = {
    '1': {
        'name': 'Hardware Debug Assistant',
        'dir': 'tools/demo3',
        'script': 'debug_assistant.py',
        'port': 8501,
        'description': 'Interactive hardware debugging with AI assistance'
    },
    '2': {
        'name': 'Netlist Analyzer',
        'dir': 'tools/demo2',
        'script': 'local_analyzer.py',
        'port': 8502,
        'description': 'Analyze and visualize Verilog netlists'
    },
    '3': {
        'name': 'DAG Visualizer',
        'dir': 'tools/dag_visualizer',
        'script': 'dag_visualizer.py',
        'port': 8503,
        'description': 'Visualize directed acyclic graphs'
    },
    '4': {
        'name': 'RTL Analyzer',
        'dir': 'tools/rtl_analyzer',
        'script': 'rtl_analyzer.py',
        'port': 8504,
        'description': 'Comprehensive RTL analysis and optimization'
    },
    '5': {
        'name': 'RTL Visualizer (DAG Generator)',
        'dir': 'tools/rtl_analyzer',
        'script': 'generate_dag_visualization.py',
        'port': None,
        'description': 'Generate DAG visualizations from Verilog RTL',
        'type': 'standalone'
    }
}

def print_banner():
    """Display welcome banner"""
    print(f"\n{Colors.HEADER}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}   🔧 BUILDATHON TOOL LAUNCHER 🔧{Colors.END}")
    print(f"{Colors.HEADER}{'='*70}{Colors.END}\n")

def print_menu():
    """Display interactive menu"""
    print(f"{Colors.BOLD}Available Tools:{Colors.END}\n")
    
    for key, tool in TOOLS.items():
        port_info = f"Port: {tool['port']}" if tool['port'] else "Standalone"
        print(f"  {Colors.CYAN}[{key}]{Colors.END} {tool['name']:<30} ({port_info})")
        print(f"      {Colors.BLUE}{tool['description']}{Colors.END}\n")
    
    print(f"{Colors.BOLD}Actions:{Colors.END}\n")
    print(f"  {Colors.CYAN}[A]{Colors.END} Launch ALL web-based tools")
    print(f"  {Colors.CYAN}[C]{Colors.END} Check system status")
    print(f"  {Colors.CYAN}[H]{Colors.END} Show help")
    print(f"  {Colors.CYAN}[Q]{Colors.END} Quit\n")

def check_system():
    """Check if required packages and files exist"""
    print(f"\n{Colors.BLUE}🔍 Checking System Status...{Colors.END}\n")
    
    # Check Python packages
    print(f"{Colors.BOLD}Required Packages:{Colors.END}")
    packages = ['streamlit', 'networkx', 'pandas', 'plotly', 'matplotlib']
    all_installed = True
    
    for package in packages:
        try:
            __import__(package)
            print(f"  {Colors.GREEN}✓{Colors.END} {package}")
        except ImportError:
            print(f"  {Colors.RED}✗{Colors.END} {package} (NOT INSTALLED)")
            all_installed = False
    
    # Check tool files
    print(f"\n{Colors.BOLD}Tool Files:{Colors.END}")
    all_files_exist = True
    
    for key, tool in TOOLS.items():
        tool_path = Path(tool['dir']) / tool['script']
        if tool_path.exists():
            print(f"  {Colors.GREEN}✓{Colors.END} {tool['name']}")
        else:
            print(f"  {Colors.RED}✗{Colors.END} {tool['name']} (File not found: {tool_path})")
            all_files_exist = False
    
    print()
    if all_installed and all_files_exist:
        print(f"{Colors.GREEN}✅ All systems ready!{Colors.END}\n")
        return True
    else:
        print(f"{Colors.YELLOW}⚠️  Some components missing. Install with:{Colors.END}")
        print(f"    pip install -r requirements.txt\n")
        return False

def launch_tool(tool_key):
    """Launch a specific tool"""
    if tool_key not in TOOLS:
        print(f"{Colors.RED}Invalid tool key: {tool_key}{Colors.END}")
        return False
    
    tool = TOOLS[tool_key]
    tool_path = Path(tool['dir']) / tool['script']
    
    if not tool_path.exists():
        print(f"{Colors.RED}✗ Tool not found: {tool_path}{Colors.END}")
        return False
    
    print(f"{Colors.BLUE}🚀 Launching {tool['name']}...{Colors.END}")
    
    # Handle standalone tools differently
    if tool.get('type') == 'standalone':
        try:
            # Change to tool directory
            original_dir = os.getcwd()
            os.chdir(tool['dir'])
            
            # Run the script
            result = subprocess.run(
                [sys.executable, tool['script']],
                capture_output=False
            )
            
            os.chdir(original_dir)
            print(f"{Colors.GREEN}✓ {tool['name']} executed{Colors.END}")
            return True
        except Exception as e:
            print(f"{Colors.RED}✗ Error running {tool['name']}: {e}{Colors.END}")
            os.chdir(original_dir)
            return False
    else:
        # Web-based tools with Streamlit
        tool_dir = Path(tool['dir']).absolute()
        port = tool['port']
        
        # Launch in new PowerShell window
        cmd = f'start powershell -NoExit -Command "cd \'{tool_dir}\'; streamlit run {tool['script']} --server.port {port} --server.headless true"'
        
        try:
            subprocess.Popen(cmd, shell=True)
            time.sleep(2)  # Give it time to start
            
            url = f"http://localhost:{port}"
            print(f"{Colors.GREEN}✓ {tool['name']}{Colors.END}")
            print(f"  URL: {Colors.CYAN}{url}{Colors.END}")
            
            # Auto-open browser
            try:
                webbrowser.open(url)
            except:
                pass
            
            return True
        except Exception as e:
            print(f"{Colors.RED}✗ Error launching {tool['name']}: {e}{Colors.END}")
            return False

def launch_all():
    """Launch all web-based tools"""
    print(f"\n{Colors.BLUE}🚀 Launching all web-based tools...{Colors.END}\n")
    
    launched = []
    failed = []
    
    for key, tool in TOOLS.items():
        # Skip standalone tools
        if tool.get('type') == 'standalone':
            continue
        
        print(f"Starting {tool['name']}...", end=" ")
        if launch_tool(key):
            launched.append(tool)
            time.sleep(1)  # Stagger launches
        else:
            failed.append(tool)
    
    print(f"\n{Colors.BOLD}Summary:{Colors.END}")
    if launched:
        print(f"{Colors.GREEN}✓ Launched {len(launched)} tool(s):{Colors.END}")
        for tool in launched:
            print(f"  • {tool['name']:<30} http://localhost:{tool['port']}")
    
    if failed:
        print(f"\n{Colors.RED}✗ Failed to launch {len(failed)} tool(s):{Colors.END}")
        for tool in failed:
            print(f"  • {tool['name']}")
    
    print(f"\n{Colors.YELLOW}💡 Tip: Close the PowerShell windows to stop each tool{Colors.END}\n")

def show_help():
    """Display help information"""
    print(f"\n{Colors.BOLD}📖 Help{Colors.END}\n")
    print("Tool Descriptions:\n")
    
    for key, tool in TOOLS.items():
        print(f"{Colors.CYAN}{key}. {tool['name']}{Colors.END}")
        print(f"   {tool['description']}")
        if tool['port']:
            print(f"   Access at: http://localhost:{tool['port']}")
        print()
    
    print(f"{Colors.BOLD}Quick Commands:{Colors.END}\n")
    print("  Launch individual tool:")
    print("    python launchers/TOOL_LAUNCHER.py")
    print()
    print("  Launch all tools:")
    print("    python launchers/TOOL_LAUNCHER.py --all")
    print()
    print("  Check system:")
    print("    python launchers/TOOL_LAUNCHER.py --check")
    print()

def main():
    """Main entry point"""
    print_banner()
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg == '--all':
            launch_all()
            return
        elif arg == '--check':
            check_system()
            return
        elif arg in ['--help', '-h']:
            show_help()
            return
        else:
            print(f"{Colors.RED}Unknown argument: {arg}{Colors.END}")
            print("Use --help for usage information")
            return
    
    # Interactive mode
    while True:
        print_menu()
        choice = input(f"{Colors.BOLD}Enter choice: {Colors.END}").strip().upper()
        
        if choice == 'Q':
            print(f"\n{Colors.GREEN}Goodbye! 👋{Colors.END}\n")
            break
        elif choice == 'A':
            launch_all()
            input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.END}")
        elif choice == 'C':
            check_system()
            input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.END}")
        elif choice == 'H':
            show_help()
            input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.END}")
        elif choice in TOOLS:
            launch_tool(choice)
            input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.END}")
        else:
            print(f"{Colors.RED}Invalid choice. Try again.{Colors.END}\n")

if __name__ == '__main__':
    # Anchor to repo root so all 'tools/...' paths resolve
    os.chdir(Path(__file__).resolve().parent.parent)
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted{Colors.END}\n")
        sys.exit(0)
