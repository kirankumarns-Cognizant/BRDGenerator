"""
Real-time LLM Model Display for Streamlit
Shows which agent is running with which model during execution
Supports multiple providers (Anthropic, OpenAI, etc.)
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
from typing import Optional, Dict, List

# Ensure imports work
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from config.config_loader import ConfigLoader
    from config.llm_selector import LLMSelector
except ImportError:
    st.error("Failed to import configuration modules")
    st.stop()


class ModelDisplayUI:
    """Streamlit UI component for displaying LLM model selection and execution."""
    
    def __init__(self):
        """Initialize model display UI."""
        try:
            config_path = Path(__file__).parent / "config" / "config.yaml"
            self.config = ConfigLoader(str(config_path))
            self.llm_config = self.config.get("llm", {})
        except Exception as e:
            self.config = None
            self.llm_config = {}
        
    def show_sidebar_model_config(self):
        """Display LLM model configuration in Streamlit sidebar (DEPRECATED - use during pipeline execution instead)."""
        # This method is kept for backward compatibility but is no longer used in sidebar
        # Model information is now displayed after each agent runs in the pipeline
        pass
    
    def _show_cost_breakdown(self):
        """Display cost breakdown by agent (REMOVED)."""
        # Cost analysis section has been removed as per user request
        pass
    
    def _show_available_models(self):
        """Display all available models by provider."""
        providers = self.llm_config.get("providers", {})
        
        for provider_name, provider_data in providers.items():
            with st.expander(f"🔵 {provider_name.upper()}", expanded=False):
                models = provider_data.get("available_models", [])
                
                for model in models:
                    model_id = model.get("id", "?")
                    display = model.get("display", model_id)
                    best_for = model.get("best_for", "")
                    input_cost = model.get("input_cost_per_mtok", 0)
                    output_cost = model.get("output_cost_per_mtok", 0)
                    
                    st.markdown(f"**{display}**")
                    st.caption(f"Model ID: `{model_id}`")
                    st.caption(f"Best for: {best_for}")
                    st.caption(
                        f"Cost: Input=${input_cost:.5f}/MTok | "
                        f"Output=${output_cost:.5f}/MTok"
                    )
                    st.markdown("")
    
    def show_execution_progress(self, agent_num: int, status: str = "running"):
        """Display execution progress with model info during pipeline run."""
        agent_key = f"agent{agent_num}"
        agent_config = self.llm_config.get("models", {}).get(agent_key, {})
        
        model = agent_config.get("model", "N/A")
        provider = agent_config.get("provider", "anthropic").upper()
        complexity = agent_config.get("complexity", "UNKNOWN")
        agent_name = agent_config.get("name", f"Agent {agent_num}")
        
        # Color coding
        complexity_colors = {
            "HIGH": "🔴",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }
        emoji = complexity_colors.get(complexity, "⚪")
        
        # Status indicators
        status_icons = {
            "running": "🔄",
            "complete": "✅",
            "error": "❌",
            "pending": "⏳"
        }
        status_icon = status_icons.get(status, "❓")
        
        # Display execution info
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 2])
            with col1:
                st.markdown(f"### {status_icon}")
            with col2:
                st.markdown(f"**Agent {agent_num}: {agent_name}**")
            with col3:
                st.markdown(f"**{emoji} {complexity}**")
            
            st.markdown(f"🔹 **Model:** `{model}` • **Provider:** `{provider}`")
            st.divider()
    
    def show_pipeline_execution_tracker(self, current_agent: Optional[int] = None):
        """Display pipeline execution with agent progression."""
        st.markdown("### 📊 Pipeline Execution Tracker")
        
        agents = []
        for agent_num in range(1, 9):
            agent_key = f"agent{agent_num}"
            agent_config = self.llm_config.get("models", {}).get(agent_key, {})
            
            if agent_config:
                agents.append({
                    "num": agent_num,
                    "name": agent_config.get("name", f"Agent {agent_num}"),
                    "model": agent_config.get("model", "?"),
                    "provider": agent_config.get("provider", "anthropic"),
                    "complexity": agent_config.get("complexity", "?")
                })
        
        # Create progress visualization
        cols = st.columns(8)
        for idx, agent in enumerate(agents):
            with cols[idx]:
                status = "running" if current_agent == agent["num"] else "pending"
                
                if current_agent and current_agent > agent["num"]:
                    status = "complete"
                
                status_emoji = {
                    "complete": "✅",
                    "running": "🔄",
                    "pending": "⏳"
                }.get(status, "❓")
                
                complexity_emoji = {
                    "HIGH": "🔴",
                    "MEDIUM": "🟡",
                    "LOW": "🟢"
                }.get(agent["complexity"], "⚪")
                
                st.markdown(
                    f"### {status_emoji}\n"
                    f"**Agent {agent['num']}**\n"
                    f"{complexity_emoji}\n"
                    f"`{agent['model']}`"
                )
    
    def show_model_comparison_table(self):
        """Display comparison table of all models."""
        st.markdown("### 📋 Model Comparison")
        
        providers = self.llm_config.get("providers", {})
        
        # Collect all models
        all_models = []
        for provider_name, provider_data in providers.items():
            models = provider_data.get("available_models", [])
            for model in models:
                all_models.append({
                    "Provider": provider_name.upper(),
                    "Model": model.get("display", ""),
                    "ID": model.get("id", ""),
                    "Input Cost/MTok": f"${model.get('input_cost_per_mtok', 0):.5f}",
                    "Output Cost/MTok": f"${model.get('output_cost_per_mtok', 0):.5f}",
                    "Best For": model.get("best_for", "")
                })
        
        # Display as table
        if all_models:
            st.dataframe(
                all_models,
                use_container_width=True,
                hide_index=True
            )
    
    def show_agent_execution_log(self, log_entries: List[Dict]):
        """Display execution log of agents."""
        st.markdown("### 📝 Execution Log")
        
        for entry in log_entries:
            timestamp = entry.get("timestamp", "")
            agent_num = entry.get("agent", "?")
            model = entry.get("model", "?")
            provider = entry.get("provider", "?").upper()
            status = entry.get("status", "unknown")
            duration = entry.get("duration", "N/A")
            
            col1, col2, col3 = st.columns([1, 2, 2])
            with col1:
                status_emoji = {
                    "complete": "✅",
                    "running": "🔄",
                    "error": "❌"
                }.get(status, "❓")
                st.markdown(f"{status_emoji} Agent {agent_num}")
            
            with col2:
                st.markdown(f"`{model}` ({provider})")
            
            with col3:
                st.caption(f"{timestamp} • {duration}s")


def initialize_session_state():
    """Initialize Streamlit session state for model tracking."""
    if "execution_log" not in st.session_state:
        st.session_state.execution_log = []
    
    if "current_agent" not in st.session_state:
        st.session_state.current_agent = None
    
    if "agent_models" not in st.session_state:
        st.session_state.agent_models = {}


def log_agent_execution(agent_num: int, model: str, provider: str, 
                       status: str, duration: float = 0):
    """Log agent execution for display."""
    initialize_session_state()
    
    entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "agent": agent_num,
        "model": model,
        "provider": provider,
        "status": status,
        "duration": duration
    }
    
    st.session_state.execution_log.append(entry)
    
    # Store model for agent
    st.session_state.agent_models[f"agent{agent_num}"] = {
        "model": model,
        "provider": provider
    }


def show_agent_model_display(agent_num: int, status: str = "complete"):
    """
    Simple function to display agent model after execution in pipeline.
    
    Usage in pipeline:
        from ui_model_display import show_agent_model_display
        show_agent_model_display(agent_num=1, status="complete")
    """
    ui = ModelDisplayUI()
    ui.show_execution_progress(agent_num, status)
