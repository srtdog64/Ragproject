# chunkers/registry.py
from __future__ import annotations
from typing import Dict, Type, Optional, List, Any
import json
import os
import sys
sys.path.append('E:/Ragproject/rag')
from chunkers.base import IChunker, ChunkingParams


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
        self._current_strategy = "adaptive"  # Default strategy
        self._params = ChunkingParams()
        self._config_file = "E:/Ragproject/rag/chunkers/config.json"
        
        # Register default chunkers FIRST
        self._register_defaults()
        
        # Then load configuration (which may override defaults)
        self._load_config()
        
        # Ensure we have a valid strategy
        if self._current_strategy not in self._chunkers:
            # Fallback to first available strategy
            if self._chunkers:
                self._current_strategy = list(self._chunkers.keys())[0]
                print(f"Warning: Strategy reset to '{self._current_strategy}'")
            else:
                # This should never happen if _register_defaults worked
                raise RuntimeError("No chunkers available!")
        
        self._initialized = True
    
    def _register_defaults(self):
        """Register all default chunking strategies"""
        try:
            from chunkers.sentence_chunker import SentenceChunker
            from chunkers.paragraph_chunker import ParagraphChunker
            from chunkers.sliding_window_chunker import SlidingWindowChunker
            from chunkers.adaptive_chunker import AdaptiveChunker
            from chunkers.overlap_chunker import SimpleOverlapChunker
            
            self.register("sentence", SentenceChunker)
            self.register("paragraph", ParagraphChunker)
            self.register("sliding_window", SlidingWindowChunker)
            self.register("adaptive", AdaptiveChunker)
            self.register("simple_overlap", SimpleOverlapChunker)
        except ImportError as e:
            print(f"Warning: Failed to import chunker: {e}")
            # Register at least one fallback chunker
            from chunkers.sentence_chunker import SentenceChunker
            self.register("sentence", SentenceChunker)
            self._current_strategy = "sentence"
    
    def register(self, name: str, chunker_class: Type[IChunker]):
        """Register a new chunking strategy"""
        self._chunkers[name] = chunker_class
    
    def get_chunker(self, name: Optional[str] = None) -> IChunker:
        """Get a chunker instance by name"""
        if name is None:
            name = self._current_strategy
        
        if name not in self._chunkers:
            # Try to use fallback
            if self._chunkers:
                name = list(self._chunkers.keys())[0]
            else:
                raise ValueError(f"No chunkers registered")
        
        # Create instance if not exists
        if name not in self._instances:
            self._instances[name] = self._chunkers[name]()
        
        return self._instances[name]
    
    def list_strategies(self) -> List[Dict[str, str]]:
        """List all available strategies"""
        strategies = []
        for name, chunker_class in self._chunkers.items():
            try:
                # Get instance to get description
                if name not in self._instances:
                    self._instances[name] = chunker_class()
                chunker = self._instances[name]
                desc = chunker.description() if hasattr(chunker, 'description') else "Chunking strategy"
            except:
                # Use static descriptions as fallback
                desc = {
                    "sentence": "Split text into individual sentences. Best for Q&A and chat-like content.",
                    "paragraph": "Split text by paragraphs. Ideal for structured documents and manuals.",
                    "sliding_window": "Use fixed-size sliding windows. Good for long narratives and novels.",
                    "adaptive": "Automatically choose the best strategy based on text characteristics.",
                    "simple_overlap": "Fixed-size chunks with overlap. Simple and predictable chunking."
                }.get(name, "Custom chunking strategy")
            
            strategies.append({
                "name": name,
                "description": desc,
                "active": name == self._current_strategy
            })
        
        return strategies
    
    def set_strategy(self, name: str):
        """Set the active chunking strategy"""
        if name not in self._chunkers:
            raise ValueError(f"Unknown strategy: {name}. Available: {list(self._chunkers.keys())}")
        
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
    
    def get_params_dict(self) -> Dict:
        """Get parameters as dictionary"""
        return self._params.__dict__.copy()
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            config = {
                "strategy": self._current_strategy,
                "params": self._params.__dict__
            }
            
            os.makedirs(os.path.dirname(self._config_file), exist_ok=True)
            with open(self._config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save config: {e}")
    
    def _load_config(self):
        """Load configuration from file"""
        if not os.path.exists(self._config_file):
            self._save_config()  # Create default config
            return
        
        try:
            with open(self._config_file, 'r') as f:
                config = json.load(f)
            
            if "strategy" in config and config["strategy"] in self._chunkers:
                self._current_strategy = config["strategy"]
            
            if "params" in config:
                self._params = ChunkingParams(**config["params"])
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")
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
