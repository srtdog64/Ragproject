#!/usr/bin/env python
"""
Unified RAG Server Launcher
Reads configuration from config/config.yaml
"""

import sys
import os
import uvicorn
from pathlib import Path

# Add rag module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rag'))

def main():
    # Try to load config to get port
    try:
        import yaml
        config_path = Path("config/config.yaml")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                host = config.get('server', {}).get('host', '127.0.0.1')
                port = config.get('server', {}).get('port', 7001)
                reload = config.get('server', {}).get('reload', True)
                log_level = config.get('server', {}).get('log_level', 'info')
        else:
            # Default values
            host = "127.0.0.1"
            port = 7001
            reload = True
            log_level = "info"
    except Exception as e:
        print(f"Warning: Could not load config: {e}")
        print("Using default settings...")
        host = "127.0.0.1"
        port = 7001
        reload = True
        log_level = "info"
    
    print("=" * 60)
    print("Starting RAG Service with Chunking Strategy Control")
    print("=" * 60)
    print(f"Server will be available at: http://localhost:{port}")
    print(f"API Documentation: http://localhost:{port}/docs")
    print(f"Chunking API: http://localhost:{port}/api/chunkers/strategies")
    print("Press CTRL+C to stop")
    print("=" * 60)
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=reload,
        reload_excludes=["tests/*", "*.md", "*.txt", "*.json", "*.yaml", "*.yml"],
        log_level=log_level
    )

if __name__ == "__main__":
    main()
