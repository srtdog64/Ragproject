#!/usr/bin/env python
"""
Start the new modular server
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn
    from config_loader import config
    
    # Get server config
    server_config = config.get_section('server')
    host = server_config.get('host', '127.0.0.1')
    port = server_config.get('port', 7001)
    
    print("="*60)
    print("Starting Modular RAG Server")
    print("="*60)
    print(f"Working directory: {os.getcwd()}")
    print(f"Server module: server.main:app")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print("="*60)
    
    uvicorn.run(
        "server.main:app",
        host=host,
        port=port,
        reload=False,  # Disable reload for stability
        log_level="info"
    )
