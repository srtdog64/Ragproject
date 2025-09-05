# chunkers/registry.py
from __future__ import annotations
from typing import Dict, Type, Optional, List, Any
import json
import os
import sys
sys.path.append('E:/Ragproject/rag')
from chunkers.base import IChunker, ChunkingParams


class ChunkerRegistry:
    """Optimized Registry for managing chunking strategies"""
    
    _instance = None
    _strategies_cache = None  # Cache for strategies list
    
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
        
        # Register default chunkers (lazy loading)
        self._register_defaults()
        
        # Load configuration if exists
        self._load_config()
        
        self._initialized = True
    
    def _register_defaults(self):
        """Register all default chunking strategies (lazy loading)"""
        # Store class paths instead of importing immediately
        self._chunker_paths = {
            "sentence": ("chunkers.sentence_chunker", "SentenceChunker"),
            "paragraph": ("chunkers.paragraph_chunker", "ParagraphChunker"),
            "sliding_window": ("chunkers.sliding_window_chunker", "SlidingWindowChunker"),
            "adaptive": ("chunkers.adaptive_chunker", "AdaptiveChunker"),
            "simple_overlap": ("chunkers.overlap_chunker", "SimpleOverlapChunker")
        }
        
        # Mark all as registered but not loaded
        for name in self._chunker_paths:
            self._chunkers[name] = None
    
    def _lazy_load_chunker(self, name: str) -> Type[IChunker]:
        """Lazy load a chunker class when needed"""
        if name not in self._chunker_paths:
            raise ValueError(f"Unknown chunker: {name}")
        
        if self._chunkers[name] is None:
            module_path, class_name = self._chunker_paths[name]
            module = __import__(module_path, fromlist=[class_name])
            self._chunkers[name] = getattr(module, class_name)
        
        return self._chunkers[name]
    
    def register(self, name: str, chunker_class: Type[IChunker]):
        """Register a new chunking strategy"""
        self._chunkers[name] = chunker_class
        self._strategies_cache = None  # Invalidate cache
    
    def get_chunker(self, name: Optional[str] = None) -> IChunker:
        """Get a chunker instance by name"""
        if name is None:
            name = self._current_strategy
        
        # Lazy load the chunker class if needed
        if name in self._chunker_paths and self._chunkers[name] is None:
            self._chunkers[name] = self._lazy_load_chunker(name)
        
        if name not in self._chunkers:
            raise ValueError(f"Unknown chunker: {name}")
        
        # Create instance if not exists
        if name not in self._instances:
            chunker_class = self._chunkers[name]
            if chunker_class is None:
                chunker_class = self._lazy_load_chunker(name)
            self._instances[name] = chunker_class()
        
        return self._instances[name]
    
    def list_strategies(self) -> List[Dict[str, str]]:
        """List all available strategies (with caching)"""
        # Return cached result if available and strategy hasn't changed
        if self._strategies_cache is not None:
            # Update active status
            for strategy in self._strategies_cache:
                strategy["active"] = strategy["name"] == self._current_strategy
            return self._strategies_cache
        
        # Static descriptions to avoid loading all chunkers
        descriptions = {
            "sentence": "Split text into individual sentences. Best for Q&A and chat-like content.",
            "paragraph": "Split text by paragraphs. Ideal for structured documents and manuals.",
            "sliding_window": "Use fixed-size sliding windows. Good for long narratives and novels.",
            "adaptive": "Automatically choose the best strategy based on text characteristics.",
            "simple_overlap": "Fixed-size chunks with overlap. Simple and predictable chunking."
        }
        
        strategies = []
        for name in self._chunker_paths.keys():
            strategies.append({
                "name": name,
                "description": descriptions.get(name, "Custom chunking strategy"),
                "active": name == self._current_strategy
            })
        
        # Cache the result
        self._strategies_cache = strategies
        return strategies
    
    def set_strategy(self, name: str):
        """Set the active chunking strategy"""
        if name not in self._chunker_paths and name not in self._chunkers:
            raise ValueError(f"Unknown strategy: {name}")
        
        self._current_strategy = name
        self._strategies_cache = None  # Invalidate cache
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
    
    def get_params_dict(self) -> Dict:
        """Get parameters as dictionary"""
        return self._params.__dict__.copy()
    
    def _save_config(self):
        """Save configuration to file (with error handling)"""
        try:
            config = {
                "strategy": self._current_strategy,
                "params": self._params.__dict__
            }
            
            os.makedirs(os.path.dirname(self._config_file), exist_ok=True)
            with open(self._config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            # Don't fail if config save fails
            print(f"Warning: Failed to save config: {e}")
    
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
            # Use defaults on error
            pass
    
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
