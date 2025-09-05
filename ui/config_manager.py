# ui/config_manager.py
"""
Configuration Manager for Qt Application
"""
import yaml
from pathlib import Path
from typing import Dict, Any, List

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self):
        self.app_config = self._load_config("config/qt_app_config.yaml")
        self.server_config = self._load_config("config/config.yaml")
    
    def _load_config(self, path: str) -> Dict:
        """Load configuration from YAML file"""
        config_path = Path(path)
        if not config_path.exists():
            return {}
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def save_config(self, path: str, config: Dict):
        """Save configuration to YAML file"""
        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    def get(self, key: str, default=None, config_type='app'):
        """Get configuration value by dot notation"""
        config = self.app_config if config_type == 'app' else self.server_config
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    def set(self, key: str, value: Any, config_type='app'):
        """Set configuration value by dot notation"""
        config = self.app_config if config_type == 'app' else self.server_config
        keys = key.split('.')
        
        # Navigate to the parent of the key to set
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the value
        current[keys[-1]] = value
        
        # Save the config
        if config_type == 'app':
            self.save_config("config/qt_app_config.yaml", self.app_config)
        else:
            self.save_config("config/config.yaml", self.server_config)
    
    def get_server_url(self) -> str:
        """Get server URL"""
        return self.get("server.url", "http://localhost:7001", 'app')
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get available models by provider"""
        return self.get("llm.available_models", {}, 'server')
    
    def get_current_model(self) -> str:
        """Get current model"""
        return self.get("llm.model", "gemini-pro", 'server')
    
    def get_current_provider(self) -> str:
        """Get current LLM provider"""
        return self.get("llm.type", "gemini", 'server')
    
    def set_model(self, provider: str, model: str):
        """Set the LLM provider and model"""
        self.set("llm.type", provider, 'server')
        self.set("llm.model", model, 'server')
