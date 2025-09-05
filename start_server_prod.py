#!/usr/bin/env python
"""
Production RAG Server Runner
Runs the RAG service without auto-reload for production stability
"""

import sys
import os
import uvicorn
from pathlib import Path

# Add rag module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rag'))

def main():
    # Try to load config
    try:
        import yaml
        config_path = Path("config/config.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                host = config.get('server', {}).get('host', '0.0.0.0')
                port = config.get('server', {}).get('port', 7001)
                log_level = config.get('server', {}).get('log_level', 'info')
        else:
            host = "0.0.0.0"
            port = 7001
            log_level = "info"
    except Exception as e:
        print(f"Warning: Could not load config: {e}")
        host = "0.0.0.0"
        port = 7001
        log_level = "info"
    
    print("=" * 60)
    print("Starting RAG Service (Production Mode)")
    print("=" * 60)
    print(f"Server will be available at: http://{host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print("Auto-reload: DISABLED (Production Mode)")
    print("Press CTRL+C to stop")
    print("=" * 60)
    
    # Run without reload for production
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=False,  # Disabled for production
        log_level=log_level,
        access_log=True
    )

if __name__ == "__main__":
    main()
