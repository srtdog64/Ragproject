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
    
    print("="*60)
    print("Starting Modular RAG Server")
    print("="*60)
    print(f"Working directory: {os.getcwd()}")
    print(f"Server module: server.main:app")
    print("="*60)
    
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=7001,
        reload=True,
        log_level="info"
    )
