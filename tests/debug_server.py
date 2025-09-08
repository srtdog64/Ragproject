#!/usr/bin/env python
"""
Debug server startup with verbose logging
"""
import subprocess
import sys
import os

def start_debug_server():
    """Start server with maximum debugging output"""
    print("="*60)
    print("Starting RAG Server with Debug Mode")
    print("="*60)
    
    # Set environment variables for debugging
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'  # Unbuffered output
    env['LOG_LEVEL'] = 'DEBUG'     # Maximum logging
    
    # Command to start server
    cmd = [
        sys.executable,
        "-u",  # Unbuffered
        "-m",
        "uvicorn",
        "server:app",
        "--host", "0.0.0.0",
        "--port", "7001",
        "--log-level", "debug",
        "--reload"
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python: {sys.executable}")
    print("="*60)
    print("Server output:")
    print("-"*60)
    
    try:
        # Run with real-time output
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Print output line by line
        for line in process.stdout:
            print(line, end='')
            
            # Check for specific error patterns
            if "Failed to initialize" in line:
                print("\n" + "!"*60)
                print("! INITIALIZATION ERROR DETECTED!")
                print("!"*60)
            elif "Failed to include routers" in line:
                print("\n" + "!"*60)
                print("! ROUTER REGISTRATION ERROR DETECTED!")
                print("!"*60)
            elif "traceback" in line.lower():
                print("\n" + "!"*60)
                print("! EXCEPTION TRACEBACK DETECTED!")
                print("!"*60)
                
    except KeyboardInterrupt:
        print("\n" + "="*60)
        print("Server stopped by user")
        print("="*60)
    except Exception as e:
        print(f"\nError starting server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    start_debug_server()
