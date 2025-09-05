#!/usr/bin/env python
"""
RAG Server Runner
Runs the RAG service on localhost:7001
"""

import os
import sys
import uvicorn

if __name__ == "__main__":
    # Add rag module to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rag'))
    
    print("Starting RAG Service...")
    print("Server will be available at: http://localhost:7001")
    print("API Documentation: http://localhost:7001/docs")
    print("Press CTRL+C to stop")
    
    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=7001,
        reload=True,
        reload_excludes=["tests/*", "*.md", "*.txt", "*.json", "*.yaml", "*.yml"],
        log_level="info"
    )
