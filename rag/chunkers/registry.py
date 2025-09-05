# chunkers/registry.py
from __future__ import annotations
from typing import Dict, Type, Optional, List, Any
import json
import os
import sys
sys.path.append('E:/Ragproject/rag')
from chunkers.base import IChunker, ChunkingParams
from chunkers.sentence_chunker import SentenceChunker
from chunkers.paragraph_chunker import ParagraphChunker
from chunkers.sliding_window_chunker import SlidingWindowChunker
from chunkers.adaptive_chunker import AdaptiveChunker


class ChunkerRegistry:
    """Registry for managing chunking strategies"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._chunkers: Dict[str, Type[IChunker]] = {}
        self._instances: Dict[str, IChunker] = {}
        self._current_strategy = "adaptive"
        self._params = ChunkingParams()
        self._config_file = "E:/Ragproject/rag/chunkers/config.json"
        
        # Register default chunkers
        self._register_defaults()
        
        # Load configuration if exists
        self._load_config()
        
        self._initialized = True
    
    def _register_defaults(self):
        """Register all default chunking strategies"""
        self.register("sentence", SentenceChunker)
        self.register("paragraph", ParagraphChunker)
        self.register("sliding_window", SlidingWindowChunker)
        self.register("adaptive", AdaptiveChunker)
        # Import and register SimpleOverlapChunker
        from chunkers.overlap_chunker import SimpleOverlapChunker
        self.register("simple_overlap", SimpleOverlapChunker)
    
    def register(self, name: str, chunker_class: Type[IChunker]):
        """Register a new chunking strategy"""
        self._chunkers[name] = chunker_class
    
    def get_chunker(self, name: Optional[str] = None) -> IChunker:
        """Get a chunker instance by name"""
        if name is None:
            name = self._current_strategy
        
        if name not in self._chunkers:
            raise ValueError(f"Unknown chunker: {name}")
        
        # Create instance if not exists
        if name not in self._instances:
            self._instances[name] = self._chunkers[name]()
        
        return self._instances[name]
    
    def list_strategies(self) -> List[Dict[str, str]]:
        """List all available strategies"""
        strategies = []
        for name in self._chunkers:
            chunker = self.get_chunker(name)
            strategies.append({
                "name": name,
                "description": chunker.description(),
                "active": name == self._current_strategy
            })
        return strategies
    
    def set_strategy(self, name: str):
        """Set the active chunking strategy"""
        if name not in self._chunkers:
            raise ValueError(f"Unknown strategy: {name}")
        
        self._current_strategy = name
        self._save_config()
    
    def get_current_strategy(self) -> str:
        """Get the current active strategy"""
        return self._current_strategy
    
    def set_params(self, **kwargs):
        """Update chunking parameters"""
        # Update only provided parameters
        current_dict = self._params.__dict__.copy()
        for key, value in kwargs.items():
            if hasattr(self._params, key):
                current_dict[key] = value
        
        self._params = ChunkingParams(**current_dict)
        self._save_config()
    
    def get_params(self) -> ChunkingParams:
        """Get current chunking parameters"""
        return self._params
    
    def _save_config(self):
        """Save configuration to file"""
        config = {
            "strategy": self._current_strategy,
            "params": self._params.__dict__
        }
        
        os.makedirs(os.path.dirname(self._config_file), exist_ok=True)
        with open(self._config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _load_config(self):
        """Load configuration from file"""
        if not os.path.exists(self._config_file):
            self._save_config()  # Create default config
            return
        
        try:
            with open(self._config_file, 'r') as f:
                config = json.load(f)
            
            if "strategy" in config:
                self._current_strategy = config["strategy"]
            
            if "params" in config:
                self._params = ChunkingParams(**config["params"])
        except Exception as e:
            print(f"Failed to load config: {e}")
            # Use defaults on error
    
    def analyze_text(self, text: str) -> str:
        """Analyze text and suggest best chunking strategy"""
        if not text:
            return "adaptive"
        
        # Simple heuristics
        lines = text.split('\n')
        double_newlines = text.count('\n\n')
        avg_line_length = sum(len(line) for line in lines) / max(1, len(lines))
        
        # Check for structured content
        has_headers = any(line.startswith('#') for line in lines)
        has_lists = any(line.strip().startswith(('-', '*', '1.')) for line in lines)
        
        # Suggest strategy
        if has_headers or has_lists or double_newlines > 10:
            return "paragraph"
        elif avg_line_length < 100 and len(lines) > 20:
            return "sentence"
        elif len(text) > 10000:
            return "sliding_window"
        else:
            return "adaptive"


# Global registry instance
registry = ChunkerRegistry()
