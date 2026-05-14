"""
PRESENTATION LAUNCHER - Master Control for Buildathon Demos
Run this script to check setup, launch demos, or get quick help
"""

import sys
import subprocess
import os
from pathlib import Path
import importlib.util

# Ensure emoji / Unicode works on Windows cp1252 consoles
try:
    sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding='utf-8')  # type: ignore[union-attr]
except Exception:
    pass

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}   🎯 BUILDATHON PRESENTATION LAUNCHER 🎯{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}\n")

def check_dependencies():
    """Check if all required packages are installed"""
    print(f"{Colors.OKBLUE}📦 Checking Dependencies...{Colors.ENDC}\n")
    
    required = {
        'streamlit': '1.53.0',
        'networkx': '3.0',
        'pandas': '2.0.0',
        'plotly': '5.0.0',
        'pyvis': '0.3.0',
        'matplotlib': '3.7.0'
    }
    
    all_good = True
    for package, min_version in required.items():
        spec = importlib.util.find_spec(package)
        if spec is None:
            print(f"  {Colors.FAIL}❌ {package:15s} - NOT INSTALLED{Colors.ENDC}")
            all_good = False
        else:
            print(f"  {Colors.OKGREEN}✅ {package:15s} - Installed{Colors.ENDC}")
    
    print()
    if not all_good:
        print(f"{Colors.WARNING}⚠️  Some dependencies are missing!{Colors.ENDC}")
        print(f"{Colors.OKBLUE}Run: pip install -r requirements.txt{Colors.ENDC}\n")
        return False
    else:
        print(f"{Colors.OKGREEN}✅ All dependencies installed!{Colors.ENDC}\n")
        return True

def check_files():
    """Check if all demo files exist"""
    print(f"{Colors.OKBLUE}📁 Checking Demo Files...{Colors.ENDC}\n")
    
    required_files = {
        'Demo 1': 'tools/demo3/debug_assistant.py',
        'Demo 2': 'tools/demo2/local_analyzer.py',
        'Demo 3': 'tools/rtl_analyzer/rtl_analyzer.py',
        'Demo 4': 'tools/final_debugger/advanced_debugger.py',
        'Sample': 'tools/rtl_analyzer/sample_counter.v'
    }
    
    all_good = True
    for name, filepath in required_files.items():
        if os.path.exists(filepath):
            print(f"  {Colors.OKGREEN}✅ {name:10s} - {filepath}{Colors.ENDC}")
        else:
            print(f"  {Colors.FAIL}❌ {name:10s} - {filepath} (NOT FOUND){Colors.ENDC}")
            all_good = False
    
    print()
    if not all_good:
        print(f"{Colors.WARNING}⚠️  Some demo files are missing!{Colors.ENDC}\n")
        return False
    else:
        print(f"{Colors.OKGREEN}✅ All demo files ready!{Colors.ENDC}\n")
        return True

def show_menu():
    """Display the main menu"""
    print(f"{Colors.BOLD}Choose an option:{Colors.ENDC}\n")
    print("  1️⃣  Launch Demo 1: Hardware Debug Assistant (Port 8610)")
    print("  2️⃣  Launch Demo 2: Netlist Analyzer (Port 8620)")
    print("  3️⃣  Launch Demo 3: RTL Analyzer (Port 8630)")
    print("  4️⃣  Launch Demo 4: Advanced Debugger (Port 8640)")
    print(f"  {Colors.OKCYAN}5️⃣  Launch ALL Demos (Parallel){Colors.ENDC}")
    print("  6️⃣  Launch DAG Visualizer (Port 8650)")
    print("  7️⃣  Check System Status")
    print("  8️⃣  Show Quick Commands")
    print("  0️⃣  Exit")
    print()

def launch_demo(demo_num):
    """Launch a specific demo"""
    demos = {
        1: {
            'name': 'Hardware Debug Assistant',
            'dir': 'tools/demo3',
            'file': 'debug_assistant.py',
            'port': 8610
        },
        2: {
            'name': 'Netlist Analyzer',
            'dir': 'tools/demo2',
            'file': 'local_analyzer.py',
            'port': 8620
        },
        3: {
            'name': 'RTL Analyzer',
            'dir': 'tools/rtl_analyzer',
            'file': 'rtl_analyzer.py',
            'port': 8630
        },
        4: {
            'name': 'Advanced Debugger',
            'dir': 'tools/final_debugger',
            'file': 'advanced_debugger.py',
            'port': 8640
        },
        6: {
            'name': 'DAG Visualizer',
            'dir': 'tools/dag_visualizer',
            'file': 'dag_visualizer.py',
            'port': 8650
        }
    }
    
    if demo_num not in demos:
        print(f"{Colors.FAIL}Invalid demo number!{Colors.ENDC}")
        return
    
    demo = demos[demo_num]
    demo_path = os.path.join(demo['dir'], demo['file'])
    
    if not os.path.exists(demo_path):
        print(f"{Colors.FAIL}❌ Demo file not found: {demo_path}{Colors.ENDC}")
        return
    
    print(f"\n{Colors.OKGREEN}🚀 Launching {demo['name']}...{Colors.ENDC}")
    print(f"{Colors.OKCYAN}📍 Access at: http://localhost:{demo['port']}{Colors.ENDC}")
    print(f"{Colors.WARNING}Press Ctrl+C to stop the demo{Colors.ENDC}\n")
    
    try:
        # Change to demo directory and run streamlit
        os.chdir(demo['dir'])
        subprocess.run([
            'streamlit', 'run', demo['file'],
            '--server.port', str(demo['port'])
        ])
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Demo stopped by user{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}Error launching demo: {e}{Colors.ENDC}")
    finally:
        # Return to original directory
        os.chdir('..')

def launch_all_demos():
    """Launch all demos in parallel (Windows)"""
    print(f"\n{Colors.OKGREEN}🚀 Launching ALL Demos...{Colors.ENDC}\n")
    
    demos = [
        ('tools/demo3/debug_assistant.py', '8610', 'Hardware Debug Assistant'),
        ('tools/demo2/local_analyzer.py', '8620', 'Netlist Analyzer'),
        ('tools/rtl_analyzer/rtl_analyzer.py', '8630', 'RTL Analyzer'),
        ('tools/final_debugger/advanced_debugger.py', '8640', 'Advanced Debugger')
    ]
    
    print(f"{Colors.OKCYAN}Opening new terminal windows for each demo...{Colors.ENDC}\n")
    
    for demo_file, port, name in demos:
        # Extract directory and filename
        demo_dir = os.path.dirname(demo_file)
        demo_script = os.path.basename(demo_file)
        
        # Launch in new PowerShell window
        cmd = f'start powershell -NoExit -Command "cd {demo_dir}; streamlit run {demo_script} --server.port {port}"'
        subprocess.Popen(cmd, shell=True)
        
        print(f"  {Colors.OKGREEN}✅ {name:30s} - http://localhost:{port}{Colors.ENDC}")
    
    print(f"\n{Colors.OKGREEN}All demos launched!{Colors.ENDC}")
    print(f"{Colors.WARNING}Close each terminal window to stop demos{Colors.ENDC}\n")

def show_quick_commands():
    """Show quick command reference"""
    print(f"\n{Colors.BOLD}📝 Quick Commands Reference{Colors.ENDC}\n")

    print(f"{Colors.OKCYAN}Demo 1: Hardware Debug Assistant{Colors.ENDC}")
    print("  streamlit run tools/demo3/debug_assistant.py --server.port 8610\n")

    print(f"{Colors.OKCYAN}Demo 2: Netlist Analyzer{Colors.ENDC}")
    print("  streamlit run tools/demo2/local_analyzer.py --server.port 8620\n")

    print(f"{Colors.OKCYAN}Demo 3: RTL Analyzer{Colors.ENDC}")
    print("  streamlit run tools/rtl_analyzer/rtl_analyzer.py --server.port 8630\n")

    print(f"{Colors.OKCYAN}Demo 4: Advanced Debugger{Colors.ENDC}")
    print("  streamlit run tools/final_debugger/advanced_debugger.py --server.port 8640\n")

    print(f"{Colors.BOLD}Install Dependencies:{Colors.ENDC}")
    print("  pip install -r requirements.txt\n")

def main():
    print_banner()
    
    # Check if --check flag is provided
    if len(sys.argv) > 1 and sys.argv[1] == '--check':
        deps_ok = check_dependencies()
        files_ok = check_files()
        
        if deps_ok and files_ok:
            print(f"{Colors.OKGREEN}✅ System ready for presentation!{Colors.ENDC}\n")
            sys.exit(0)
        else:
            print(f"{Colors.FAIL}❌ Please fix the issues above{Colors.ENDC}\n")
            sys.exit(1)
    
    # Check if --help flag is provided
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("Usage:")
        print("  python launchers/PRESENTATION_LAUNCHER.py          - Interactive menu")
        print("  python launchers/PRESENTATION_LAUNCHER.py --check  - Check system status")
        print("  python launchers/PRESENTATION_LAUNCHER.py --help   - Show this help")
        print()
        sys.exit(0)
    
    # Interactive menu
    while True:
        show_menu()
        choice = input(f"{Colors.BOLD}Enter your choice: {Colors.ENDC}").strip()
        
        if choice == '0':
            print(f"\n{Colors.OKGREEN}Good luck with your presentation! 🎉{Colors.ENDC}\n")
            break
        elif choice == '1':
            launch_demo(1)
        elif choice == '2':
            launch_demo(2)
        elif choice == '3':
            launch_demo(3)
        elif choice == '4':
            launch_demo(4)
        elif choice == '5':
            launch_all_demos()
        elif choice == '6':
            launch_demo(6)
        elif choice == '7':
            check_dependencies()
            check_files()
        elif choice == '8':
            show_quick_commands()
        else:
            print(f"{Colors.FAIL}Invalid choice! Please try again.{Colors.ENDC}\n")

if __name__ == '__main__':
    # Anchor to repo root so all 'tools/...' paths resolve
    os.chdir(Path(__file__).resolve().parent.parent)
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Launcher interrupted{Colors.ENDC}\n")
        sys.exit(0)
