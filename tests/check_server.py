#!/usr/bin/env python
"""
Quick server status check and startup helper
"""

import subprocess
import requests
import time
import sys
import os

def check_server():
    """Check if server is running"""
    try:
        response = requests.get("http://localhost:7001/health", timeout=1)
        if response.status_code == 200:
            return True
    except:
        pass
    return False

def start_server():
    """Start the RAG server"""
    print("Starting RAG server...")
    
    # Check if start_server.py exists
    if not os.path.exists("start_server.py"):
        print("❌ start_server.py not found!")
        print("Please create it or run: python server.py")
        return False
    
    # Start server in background
    if sys.platform == "win32":
        # Windows
        subprocess.Popen(
            ["python", "start_server.py"],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        # Linux/Mac
        subprocess.Popen(
            ["python", "start_server.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    
    # Wait for server to start
    print("Waiting for server to start", end="")
    for i in range(30):  # Wait up to 30 seconds
        print(".", end="", flush=True)
        time.sleep(1)
        if check_server():
            print("\n✅ Server started successfully!")
            return True
    
    print("\n❌ Server failed to start within 30 seconds")
    return False

def main():
    print("="*60)
    print("RAG Server Status Check")
    print("="*60)
    
    if check_server():
        print("✅ Server is already running at http://localhost:7001")
        
        # Get more info
        try:
            response = requests.get("http://localhost:7001/api/chunkers/strategy")
            if response.status_code == 200:
                data = response.json()
                print(f"   Current strategy: {data.get('strategy', 'unknown')}")
        except:
            pass
            
    else:
        print("❌ Server is not running")
        
        response = input("\nWould you like to start the server? (y/n): ")
        if response.lower() == 'y':
            if start_server():
                print("\nYou can now:")
                print("1. Run Qt app: python qt_app.py")
                print("2. Test the system: python test_persistence_reranking.py")
            else:
                print("\nPlease start the server manually:")
                print("  python start_server.py")
                print("or")
                print("  python server.py")

if __name__ == "__main__":
    main()
