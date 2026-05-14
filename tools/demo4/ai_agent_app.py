import streamlit as st
import os
from dotenv import load_dotenv
from ai_agent import GeminiAgent

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="EDA Netlist AI Analyzer",
    page_icon="ðŸ”Œ",
    layout="wide"
)

st.title("ðŸ”Œ EDA Netlist AI Analyzer - Powered by Gemini")
st.caption("Intelligent analysis for Verilog netlists and HDL code")

# Check if API key is configured
if not os.getenv('GEMINI_API_KEY'):
    st.error("âš ï¸ GEMINI_API_KEY not found!")
    st.info("""
    To set up:
    1. Get your API key from https://makersuite.google.com/app/apikey
    2. Edit `.env` file in the demo2 folder
    3. Replace YOUR_API_KEY_HERE with your actual key
    4. Restart the application
    """)
    st.stop()

# Initialize agent
try:
    agent = GeminiAgent()
    st.success("âœ… Gemini API connected!")
except Exception as e:
    st.error(f"Failed to initialize: {str(e)}")
    st.stop()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "loaded_netlist" not in st.session_state:
    st.session_state.loaded_netlist = None

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "ðŸ”Œ Netlist Analysis",
    "ðŸ› Debug Assistant", 
    "ðŸ“ Verilog Code Review",
    "ðŸ’¬ Chat",
    "ðŸŽ“ Learn & Explain"
])

with tab1:
    st.header("ðŸ”Œ Comprehensive Netlist Analysis")
    st.info("Upload or paste your Verilog netlist for AI-powered analysis")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload netlist.v file",
        type=['v', 'sv', 'verilog'],
        help="Upload your synthesized netlist file"
    )
    
    netlist_content = ""
    
    if uploaded_file is not None:
        netlist_content = uploaded_file.read().decode('utf-8')
        st.success(f"âœ… Loaded: {uploaded_file.name} ({len(netlist_content)} characters, {len(netlist_content.split())} lines)")
        
        with st.expander("ðŸ“„ Preview first 50 lines"):
            lines = netlist_content.split('\n')[:50]
            st.code('\n'.join(lines), language='verilog')
    elif st.session_state.loaded_netlist:
        netlist_content = st.session_state.loaded_netlist
        st.success(f"âœ… Using loaded netlist from sidebar ({len(netlist_content)} characters)")
    else:
        netlist_content = st.text_area(
            "Or paste your netlist here:",
            height=300,
            placeholder="module sample_counter(rst_n, clk, ...)\n  // Your netlist code\nendmodule"
        )
    
    # Analysis type
    col1, col2 = st.columns([2, 1])
    
    with col1:
        analysis_type = st.selectbox(
            "Analysis Type:",
            ["overview", "debugging", "optimization", "connectivity"],
            format_func=lambda x: {
                "overview": "ðŸ“Š Design Overview & Summary",
                "debugging": "ðŸ› Debug & Find Issues",
                "optimization": "âš¡ Optimization Suggestions",
                "connectivity": "ðŸ”— Connectivity Analysis"
            }[x]
        )
    
    with col2:
        st.write("")
        st.write("")
        analyze_btn = st.button("ðŸš€ Analyze Netlist", type="primary", use_container_width=True)
    
    if analyze_btn:
        if netlist_content.strip():
            with st.spinner(f"ðŸ¤– AI is analyzing your netlist ({analysis_type})..."):
                result = agent.analyze_netlist(netlist_content, analysis_type)
                
                st.markdown("---")
                st.markdown("### ðŸ“‹ Analysis Results")
                st.markdown(result)
                
                st.download_button(
                    "ðŸ’¾ Download Analysis Report",
                    result,
                    file_name=f"netlist_analysis_{analysis_type}.txt",
                    mime="text/plain"
                )
        else:
            st.warning("âš ï¸ Please upload or paste a netlist first")

with tab2:
    st.header("ðŸ› Debug Assistant")
    st.info("Find and fix issues in your netlist")
    
    debug_option = st.radio(
        "Select debugging mode:",
        ["ðŸ” Signal Trace", "âš ï¸ Find Issues", "ðŸ“Š Full Debug Report"],
        horizontal=True
    )
    
    debug_netlist = st.text_area(
        "Paste netlist to debug:",
        height=250,
        key="debug_netlist",
        value=st.session_state.loaded_netlist if st.session_state.loaded_netlist else ""
    )
    
    if debug_option == "ðŸ” Signal Trace":
        signal_name = st.text_input(
            "Enter signal name to trace:",
            placeholder="e.g., clk, rst_n, data_out"
        )
        
        if st.button("ðŸ” Trace Signal", type="primary"):
            if debug_netlist and signal_name:
                with st.spinner(f"Tracing signal '{signal_name}'..."):
                    result = agent.debug_specific_signal(debug_netlist, signal_name)
                    st.markdown("### ðŸ” Signal Trace Results")
                    st.markdown(result)
            else:
                st.warning("Please provide both netlist and signal name")
    
    elif debug_option == "âš ï¸ Find Issues":
        if st.button("ðŸ› Find Issues", type="primary"):
            if debug_netlist:
                with st.spinner("Scanning for issues..."):
                    result = agent.analyze_netlist(debug_netlist, "debugging")
                    st.markdown("### âš ï¸ Issues Found")
                    st.markdown(result)
            else:
                st.warning("Please paste a netlist to debug")
    
    else:  # Full Debug Report
        if st.button("ðŸ“Š Generate Debug Report", type="primary"):
            if debug_netlist:
                with st.spinner("Generating comprehensive debug report..."):
                    st.markdown("### ðŸ“Š Comprehensive Debug Report")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Issues & Warnings")
                        with st.spinner("Analyzing..."):
                            issues = agent.analyze_netlist(debug_netlist, "debugging")
                            st.markdown(issues)
                    
                    with col2:
                        st.markdown("#### Connectivity Check")
                        with st.spinner("Analyzing..."):
                            connectivity = agent.analyze_netlist(debug_netlist, "connectivity")
                            st.markdown(connectivity)
            else:
                st.warning("Please paste a netlist")

with tab3:
    st.header("ðŸ“ Verilog Code Review")
    st.info("Get AI feedback on your Verilog/SystemVerilog code")
    
    verilog_input = st.text_area(
        "Paste your Verilog code:",
        height=300,
        placeholder="module example(...)\n  // Your Verilog code\nendmodule",
        key="verilog_review"
    )
    
    if st.button("ðŸ“ Review Code", type="primary"):
        if verilog_input.strip():
            with st.spinner("Reviewing your code..."):
                analysis = agent.analyze_verilog(verilog_input)
                st.markdown("### ðŸ“‹ Code Review Results")
                st.markdown(analysis)
        else:
            st.warning("Please enter some Verilog code")

with tab4:
    st.header("ðŸ’¬ Chat with Gemini")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about EDA, Verilog, or your netlist..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            response = agent.generate_response(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

with tab5:
    st.header("ðŸŽ“ Learn & Explain")
    st.info("Understand complex netlists and EDA concepts")
    
    explain_mode = st.radio(
        "What would you like to understand?",
        ["ðŸŽ¯ Explain Netlist", "â“ Ask EDA Question", "ðŸ”¬ Compare Modules"],
        horizontal=True
    )
    
    if explain_mode == "ðŸŽ¯ Explain Netlist":
        netlist_to_explain = st.text_area(
            "Paste netlist to explain:",
            height=200,
            key="explain_netlist",
            value=st.session_state.loaded_netlist[:3000] if st.session_state.loaded_netlist else ""
        )
        
        if st.button("ðŸŽ“ Explain in Simple Terms", type="primary"):
            if netlist_to_explain:
                with st.spinner("Creating simple explanation..."):
                    explanation = agent.explain_to_non_expert(netlist_to_explain)
                    st.markdown("### ðŸŽ“ Simple Explanation")
                    st.markdown(explanation)
            else:
                st.warning("Please paste a netlist")
    
    elif explain_mode == "â“ Ask EDA Question":
        question = st.text_area(
            "Ask your EDA question:",
            height=100,
            placeholder="e.g., What is the difference between synthesis and place & route?"
        )
        
        if st.button("ðŸ’¡ Get Answer", type="primary"):
            if question:
                with st.spinner("Thinking..."):
                    answer = agent.generate_response(question)
                    st.markdown("### ðŸ’¡ Answer")
                    st.markdown(answer)
            else:
                st.warning("Please ask a question")
    
    else:  # Compare Modules
        st.write("Compare two modules from your netlist")
        
        netlist_compare = st.text_area(
            "Paste netlist:",
            height=150,
            key="compare_netlist",
            value=st.session_state.loaded_netlist if st.session_state.loaded_netlist else ""
        )
        
        col1, col2 = st.columns(2)
        with col1:
            module1 = st.text_input("First module name:", placeholder="e.g., sample_counter")
        with col2:
            module2 = st.text_input("Second module name:", placeholder="e.g., control_unit")
        
        if st.button("ðŸ”¬ Compare Modules", type="primary"):
            if netlist_compare and module1 and module2:
                with st.spinner(f"Comparing {module1} and {module2}..."):
                    comparison = agent.compare_modules(netlist_compare, module1, module2)
                    st.markdown("### ðŸ”¬ Module Comparison")
                    st.markdown(comparison)
            else:
                st.warning("Please provide netlist and both module names")

# Sidebar
with st.sidebar:
    st.header("ðŸ“š About")
    st.info("""
    **EDA Netlist AI Analyzer**
    
    Powered by Google Gemini AI for intelligent hardware design analysis.
    """)
    
    st.markdown("### ðŸŽ¯ Capabilities")
    st.markdown("""
    - ðŸ”Œ Netlist parsing & analysis
    - ðŸ› Bug detection & debugging
    - âš¡ Optimization suggestions
    - ðŸ”— Connectivity tracing
    - ðŸ“ Code review
    - ðŸŽ“ Educational explanations
    """)
    
    st.markdown("### ðŸ“‚ Quick Actions")
    
    # Quick load netlist.v
    if st.button("ðŸ“‚ Load netlist.v", use_container_width=True):
        try:
            netlist_path = "../netlist.v"
            if os.path.exists(netlist_path):
                with open(netlist_path, 'r') as f:
                    st.session_state['loaded_netlist'] = f.read()
                st.success("âœ… netlist.v loaded!")
                st.rerun()
            else:
                # Try current directory
                netlist_path = "netlist.v"
                with open(netlist_path, 'r') as f:
                    st.session_state['loaded_netlist'] = f.read()
                st.success("âœ… netlist.v loaded!")
                st.rerun()
        except Exception as e:
            st.error(f"Could not load: {e}")
    
    if st.button("ðŸ—‘ï¸ Clear Loaded Netlist", use_container_width=True):
        st.session_state.loaded_netlist = None
        st.success("Cleared!")
        st.rerun()
    
    if st.button("ðŸ—‘ï¸ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.caption("ðŸ’¡ **Tip**: Load your netlist.v using the button above, then explore different analysis tabs!")
