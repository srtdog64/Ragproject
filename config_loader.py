# config_loader.py
"""Configuration loader for RAG system"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigLoader:
    """Load and manage configuration from YAML file"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Try multiple locations for config file
            possible_paths = [
                Path(__file__).parent / "config" / "config.yaml",
                Path(__file__).parent / "config.yaml",
                Path("config/config.yaml"),
                Path("config.yaml")
            ]
            
            for path in possible_paths:
                if path.exists():
                    config_path = path
                    break
            
            if config_path is None:
                raise FileNotFoundError(f"Config file not found. Tried: {possible_paths}")
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Override with environment variables if they exist
        self._apply_env_overrides(config)
        
        return config
    
    def _apply_env_overrides(self, config: Dict[str, Any]):
        """Apply environment variable overrides"""
        # Example: RAG_POLICY_MAXTOKENS=1000 would override policy.maxTokens
        for key in os.environ:
            if key.startswith('RAG_'):
                # Convert RAG_SECTION_KEY to section.key path
                path = key[4:].lower().replace('_', '.')
                parts = path.split('.')
                
                # Navigate to the right place in config
                current = config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # Set the value (try to parse as appropriate type)
                value = os.environ[key]
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                else:
                    try:
                        value = float(value)
                    except ValueError:
                        pass  # Keep as string
                
                current[parts[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key"""
        parts = key.split('.')
        current = self.config
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        
        return current
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self.config.get(section, {})
    
    def reload(self):
        """Reload configuration from file"""
        self.config = self._load_config()
    
    @property
    def all(self) -> Dict[str, Any]:
        """Get entire configuration"""
        return self.config

# Global config instance
config = ConfigLoader()
