import os
import re
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

class GeminiAgent:
    def __init__(self):
        # Get API key from environment variable
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file")
        
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel('gemini-pro')
        
    def generate_response(self, prompt):
        """Generate a response using Gemini API"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def analyze_verilog(self, verilog_code):
        """Analyze Verilog code using Gemini"""
        prompt = f"""
        Analyze the following Verilog code and provide:
        1. A brief description of what it does
        2. Any potential issues or improvements
        3. Key modules and their connections
        
        Verilog Code:
        {verilog_code}
        """
        return self.generate_response(prompt)
    
    def analyze_netlist(self, netlist_content, analysis_type="overview"):
        """Comprehensive netlist analysis for EDA workflows"""
        
        # Extract basic statistics
        stats = self._extract_netlist_stats(netlist_content)
        
        if analysis_type == "overview":
            prompt = f"""
            You are an expert EDA engineer analyzing a synthesized netlist.
            
            Netlist Statistics:
            - Total Lines: {stats['total_lines']}
            - Modules Found: {stats['module_count']}
            - Module Names: {', '.join(stats['modules'][:10])}
            - Total Ports: ~{stats['port_count']}
            - Wire Declarations: ~{stats['wire_count']}
            
            First 200 lines of netlist:
            {netlist_content[:5000]}
            
            Provide:
            1. **Design Overview**: What this netlist implements
            2. **Hierarchy**: Key modules and their relationships
            3. **Complexity Assessment**: Design size and complexity
            4. **Potential Issues**: Any red flags or concerns
            5. **EDA Tool Info**: What synthesis tool was used
            """
            
        elif analysis_type == "debugging":
            prompt = f"""
            You are debugging a netlist. Analyze for common issues:
            
            Netlist snippet:
            {netlist_content[:8000]}
            
            Check for:
            1. Unconnected signals (UNCONNECTED wires)
            2. Naming convention issues
            3. Potential timing problems
            4. Clock domain issues
            5. Reset signal problems
            6. Port mismatch possibilities
            
            Provide specific line numbers or signal names where issues are found.
            """
            
        elif analysis_type == "optimization":
            prompt = f"""
            As an EDA optimization expert, analyze this netlist for improvements:
            
            {netlist_content[:8000]}
            
            Suggest:
            1. Logic optimization opportunities
            2. Resource utilization improvements
            3. Synthesis constraint recommendations
            4. Potential bottlenecks
            5. Power optimization hints
            """
            
        elif analysis_type == "connectivity":
            prompt = f"""
            Analyze the connectivity and signal flow in this netlist:
            
            {netlist_content[:8000]}
            
            Describe:
            1. Input/Output interfaces
            2. Key signal paths
            3. Clock and reset networks
            4. Data flow patterns
            5. Control signal routing
            """
        
        else:  # custom
            prompt = netlist_content
        
        return self.generate_response(prompt)
    
    def _extract_netlist_stats(self, content):
        """Extract basic statistics from netlist"""
        lines = content.split('\n')
        
        # Find modules
        modules = re.findall(r'^module\s+(\w+)', content, re.MULTILINE)
        
        # Count ports and wires
        port_count = len(re.findall(r'\b(input|output|inout)\b', content))
        wire_count = len(re.findall(r'\bwire\b', content))
        
        return {
            'total_lines': len(lines),
            'modules': modules,
            'module_count': len(modules),
            'port_count': port_count,
            'wire_count': wire_count
        }
    
    def debug_specific_signal(self, netlist_content, signal_name):
        """Debug a specific signal in the netlist"""
        prompt = f"""
        Find and analyze the signal '{signal_name}' in this netlist:
        
        {netlist_content[:10000]}
        
        Provide:
        1. Where the signal is declared
        2. Where it's driven (assigned)
        3. Where it's used
        4. Its bit width
        5. Any potential issues with this signal
        """
        return self.generate_response(prompt)
    
    def compare_modules(self, netlist_content, module1, module2):
        """Compare two modules in the netlist"""
        prompt = f"""
        Compare modules '{module1}' and '{module2}' in this netlist:
        
        {netlist_content[:10000]}
        
        Analyze:
        1. Functional differences
        2. Interface differences (ports)
        3. Complexity comparison
        4. Usage patterns
        """
        return self.generate_response(prompt)
    
    def explain_to_non_expert(self, netlist_content):
        """Explain netlist in simple terms"""
        prompt = f"""
        Explain this hardware netlist to someone without EDA experience:
        
        {netlist_content[:5000]}
        
        Use simple analogies and avoid technical jargon. Focus on:
        1. What this hardware does
        2. Main components (like building blocks)
        3. How data flows through the design
        4. Real-world application
        """
        return self.generate_response(prompt)
