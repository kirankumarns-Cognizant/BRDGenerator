"""
Real-Time Model Tracking for Pipeline Execution
Shows which model each agent is using during BRD generation in Streamlit

INTEGRATION GUIDE:
1. In your agent execution code, import log_agent_execution from ui_model_display
2. Call log_agent_execution(agent_num, model, provider, status, duration)
3. This updates the execution log in Streamlit session state
4. The UI automatically displays the model progression
"""

import streamlit as st
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path
import sys
import json

PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from config.config_loader import ConfigLoader
    from config.llm_selector import LLMSelector
except ImportError:
    try:
        from config_loader import ConfigLoader
        from llm_selector import LLMSelector
    except ImportError as e:
        print(f"Error importing config modules: {e}")


class PipelineExecutionTracker:
    """Track and display pipeline execution with real-time model information."""
    
    def __init__(self):
        """Initialize the tracker."""
        try:
            config_path = Path(__file__).parent / "config" / "config.yaml"
            self.config = ConfigLoader(str(config_path))
            self.llm_config = self.config.get("llm", {})
        except Exception as e:
            self.config = None
            self.llm_config = {}
    
    def show_execution_header(self):
        """Display header for pipeline execution."""
        st.markdown("""
        ## 🚀 BRD Pipeline Execution
        
        Real-time tracking of agent execution with model selection.
        """)
        
        # Show provider info
        provider = self.llm_config.get("default_provider", "anthropic").upper()
        st.info(f"🔵 **LLM Provider:** {provider}")
    
    def show_execution_progress_table(self):
        """Display table showing execution progress for all agents."""
        st.markdown("### 📊 Agent Execution Progress")
        
        # Get all agents with their models
        agents_data = []
        for agent_num in range(1, 9):
            agent_key = f"agent{agent_num}"
            agent_config = self.llm_config.get("models", {}).get(agent_key, {})
            
            if not agent_config:
                continue
            
            # Check session state for execution status
            execution_status = "pending"
            model_used = agent_config.get("model", "?")
            provider = agent_config.get("provider", "anthropic").upper()
            duration = 0
            
            # Check if this agent has been executed
            exec_log = st.session_state.get("execution_log", [])
            for entry in exec_log:
                if entry.get("agent") == agent_num:
                    execution_status = entry.get("status", "pending")
                    model_used = entry.get("model", model_used)
                    duration = entry.get("duration", 0)
                    provider = entry.get("provider", provider)
            
            agents_data.append({
                "Agent": f"Agent {agent_num}",
                "Task": agent_config.get("name", ""),
                "Model": model_used,
                "Provider": provider,
                "Complexity": agent_config.get("complexity", "?"),
                "Status": execution_status,
                "Duration": f"{duration}s" if duration > 0 else "—"
            })
        
        # Display table
        if agents_data:
            st.dataframe(agents_data, use_container_width=True, hide_index=True)
    
    def show_current_execution(self, agent_num: Optional[int] = None):
        """Display currently executing agent with full model details."""
        if agent_num is None:
            agent_num = st.session_state.get("current_agent")
        
        if agent_num is None:
            return
        
        agent_key = f"agent{agent_num}"
        agent_config = self.llm_config.get("models", {}).get(agent_key, {})
        
        if not agent_config:
            return
        
        model = agent_config.get("model", "N/A")
        provider = agent_config.get("provider", "anthropic").upper()
        complexity = agent_config.get("complexity", "?")
        agent_name = agent_config.get("name", f"Agent {agent_num}")
        task = agent_config.get("task", "")
        
        # Complexity emoji
        complexity_emoji = {
            "HIGH": "🔴",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }.get(complexity, "⚪")
        
        # Display current execution
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            st.markdown(f"### 🔄 Running")
        
        with col2:
            st.markdown(f"#### Agent {agent_num}: {agent_name}")
        
        with col3:
            st.markdown(f"### {complexity_emoji}")
        
        # Show model details
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Model:** `{model}`")
            st.markdown(f"**Provider:** {provider}")
        
        with col2:
            st.markdown(f"**Complexity:** {complexity}")
            st.markdown(f"**Task:** {task}")
        
        # Show model capabilities
        providers = self.llm_config.get("providers", {})
        provider_key = agent_config.get("provider", "anthropic")
        provider_data = providers.get(provider_key, {})
        available_models = provider_data.get("available_models", [])
        
        for model_info in available_models:
            if model_info.get("id") == model:
                st.info(f"**Best for:** {model_info.get('best_for', 'General tasks')}")
                break
    
    def show_agent_progression(self):
        """Show visual progression of agent execution."""
        st.markdown("### 🎯 Agent Progression")
        
        exec_log = st.session_state.get("execution_log", [])
        
        # Create progress visualization
        progress_cols = st.columns(8)
        
        for agent_num in range(1, 9):
            with progress_cols[agent_num - 1]:
                # Find this agent in execution log
                agent_status = "pending"
                for entry in exec_log:
                    if entry.get("agent") == agent_num:
                        agent_status = entry.get("status", "pending")
                        break
                
                # Status emoji
                status_emoji = {
                    "complete": "✅",
                    "running": "🔄",
                    "error": "❌",
                    "pending": "⏳"
                }.get(agent_status, "❓")
                
                # Color background based on status
                status_color = {
                    "complete": "✅",
                    "running": "🔄",
                    "error": "❌",
                    "pending": "⚪"
                }.get(agent_status, "❓")
                
                st.markdown(
                    f"<div style='text-align: center; padding: 10px; border: 2px solid #ccc; border-radius: 5px;'>"
                    f"<h4>{status_emoji}</h4>"
                    f"<p>Agent {agent_num}</p>"
                    f"</div>",
                    unsafe_allow_html=True
                )
    
    def show_execution_log(self):
        """Display detailed execution log."""
        exec_log = st.session_state.get("execution_log", [])
        
        if not exec_log:
            st.info("No agents have executed yet.")
            return
        
        st.markdown("### 📝 Execution Log")
        
        for entry in exec_log:
            with st.expander(f"Agent {entry.get('agent')} - {entry.get('status', 'unknown').upper()}"):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown(f"**Time:** {entry.get('timestamp', '?')}")
                    st.markdown(f"**Duration:** {entry.get('duration', '?')}s")
                
                with col2:
                    st.markdown(f"**Model:** `{entry.get('model', '?')}`")
                    st.markdown(f"**Provider:** {entry.get('provider', '?').upper()}")
    
    def show_cost_during_execution(self):
        """Show cost breakdown during execution."""
        st.markdown("### 💰 Cost Tracking")
        
        exec_log = st.session_state.get("execution_log", [])
        
        # Calculate costs
        total_cost = 0
        cost_by_agent = {}
        
        providers = self.llm_config.get("providers", {})
        
        for entry in exec_log:
            agent_num = entry.get("agent", 0)
            model = entry.get("model", "")
            provider = entry.get("provider", "anthropic")
            
            # Look up model cost
            provider_data = providers.get(provider, {})
            available_models = provider_data.get("available_models", [])
            
            agent_cost = 0
            for model_info in available_models:
                if model_info.get("id") == model:
                    # Estimate cost (simplified)
                    input_cost = model_info.get("input_cost_per_mtok", 0) * 0.5  # Estimate 500K input tokens
                    output_cost = model_info.get("output_cost_per_mtok", 0) * 0.3  # Estimate 300K output tokens
                    agent_cost = (input_cost + output_cost) / 1000000
                    break
            
            cost_by_agent[f"Agent {agent_num}"] = agent_cost
            total_cost += agent_cost
        
        # Display costs
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Cost So Far", f"${total_cost:.4f}")
        
        with col2:
            if cost_by_agent:
                max_cost = max(cost_by_agent.values())
                max_agent = [k for k, v in cost_by_agent.items() if v == max_cost][0]
                st.metric("Most Expensive Agent", max_agent)
        
        # Show breakdown
        if cost_by_agent:
            st.bar_chart(cost_by_agent)


def example_usage():
    """Example of how to use the pipeline execution tracker in Streamlit."""
    
    # In your pipeline execution code:
    
    # At the start of pipeline
    st.session_state.current_agent = 1
    log_agent_execution(1, "claude-3-opus", "anthropic", "running")
    
    # Show current execution
    tracker = PipelineExecutionTracker()
    tracker.show_current_execution(1)
    
    # Simulate agent work...
    # (In real code, this would be actual agent execution)
    import time
    time.sleep(2)
    
    # When agent completes
    log_agent_execution(1, "claude-3-opus", "anthropic", "complete", duration=2)
    st.session_state.current_agent = 2
    
    # Show progression
    tracker.show_agent_progression()
    
    # Show log
    tracker.show_execution_log()
    
    # Show costs
    tracker.show_cost_during_execution()


# ============================================================================
# INTEGRATION WITH PIPELINE EXECUTION
# ============================================================================

"""
To integrate this into your pipeline execution:

1. Import in your pipeline runner:
   from pipeline_execution_tracker import PipelineExecutionTracker, log_agent_execution

2. At the start of each agent:
   log_agent_execution(agent_num, model, provider, "running")
   tracker = PipelineExecutionTracker()
   tracker.show_current_execution(agent_num)

3. When agent completes:
   log_agent_execution(agent_num, model, provider, "complete", duration=elapsed_time)

4. Display progress:
   tracker.show_execution_progress_table()
   tracker.show_agent_progression()
   tracker.show_execution_log()
   tracker.show_cost_during_execution()

Example:

```python
def run_agent(agent_num, repo_path):
    # Get model configuration
    from config.llm_selector import LLMSelector
    model_config = LLMSelector.get_model_for_agent(agent_num)
    
    # Log execution start
    log_agent_execution(
        agent_num, 
        model_config["model"], 
        model_config["provider"], 
        "running"
    )
    
    # Show current execution
    tracker = PipelineExecutionTracker()
    tracker.show_current_execution(agent_num)
    
    # Run agent (timing it)
    import time
    start_time = time.time()
    
    try:
        result = execute_agent(agent_num, model_config, repo_path)
        
        # Log completion
        duration = time.time() - start_time
        log_agent_execution(
            agent_num,
            model_config["model"],
            model_config["provider"],
            "complete",
            duration=duration
        )
        
        return result
    
    except Exception as e:
        # Log error
        duration = time.time() - start_time
        log_agent_execution(
            agent_num,
            model_config["model"],
            model_config["provider"],
            "error",
            duration=duration
        )
        raise

# In your pipeline execution loop:
for agent_num in range(1, 9):
    run_agent(agent_num, repo_path)
    
    # Show current progress
    tracker = PipelineExecutionTracker()
    tracker.show_execution_progress_table()
    tracker.show_agent_progression()
```
"""
