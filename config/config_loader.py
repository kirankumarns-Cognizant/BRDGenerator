"""
Configuration Loader for BRD Agent Framework
Loads and provides access to config.yaml settings
"""

import yaml
from pathlib import Path

class ConfigLoader:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)
    
    def get(self, key: str, default=None):
        """Get configuration value by key (supports dot notation)"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def get_kb_dir(self):
        """Get KB directory path"""
        return self.get('paths.kb_dir', 'KB')
    
    def get_kb_store_dir(self):
        """Get KB store directory path"""
        return self.get('paths.kb_store_dir', 'kb_store')
    
    def get_repo_path(self):
        """Get repository path"""
        return self.get('paths.repo_path', '')
    
    def is_tool_enabled(self, agent: str, tool: str):
        """Check if a tool is enabled for an agent"""
        enabled = self.get(f'agents.{agent}.tools.{tool}.enabled', True)
        return enabled
    
    def get_threshold(self, threshold_name: str):
        """Get a confidence threshold"""
        return self.get(f'thresholds.{threshold_name}', 0.6)
    
    def get_agent_config(self, agent_name: str):
        """Get complete configuration for an agent"""
        return self.get(f'agents.{agent_name}', {})
    
    def get_vector_store_config(self):
        """Get vector store configuration"""
        return self.get('vector_store', {})
    
    def get_tool_adapter_config(self, adapter_name: str):
        """Get tool adapter configuration"""
        return self.get(f'tool_adapters.{adapter_name}', {})
    
    @property
    def config(self):
        """Get raw configuration dictionary"""
        return self._config
