"""
Kill all Python processes and restart server
"""
import subprocess
import time
import sys
import os

def kill_python_processes():
    """Kill all Python processes"""
    print("Stopping all Python processes...")
    try:
        # Windows command to kill Python processes
        subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
        subprocess.run(["taskkill", "/F", "/IM", "pythonw.exe"], capture_output=True)
        print("All Python processes stopped")
    except:
        print("Could not stop processes")
    
    time.sleep(2)

def start_server():
    """Start the server on port 7001"""
    print("\nStarting server on port 7001...")
    
    # Change to project directory
    os.chdir("E:\\Ragproject")
    
    # Start server
    cmd = [sys.executable, "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7001"]
    print(f"Command: {' '.join(cmd)}")
    
    process = subprocess.Popen(cmd)
    print(f"Server started with PID: {process.pid}")
    
    # Wait for server to initialize
    print("Waiting for server to initialize...")
    time.sleep(5)
    
    # Test the endpoint
    import requests
    try:
        response = requests.get("http://localhost:7001/api/rag/stats", timeout=2)
        print(f"\n/api/rag/stats status: {response.status_code}")
        if response.status_code == 200:
            print("✓ API endpoint is working!")
            print(f"Response: {response.json()}")
        else:
            print("✗ API endpoint returned error")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error testing endpoint: {e}")
    
    return process

if __name__ == "__main__":
    print("="*60)
    print("Server Restart Tool")
    print("="*60)
    
    # Kill existing processes
    kill_python_processes()
    
    # Start fresh server
    process = start_server()
    
    print("\n" + "="*60)
    print("Server is running. Press Ctrl+C to stop.")
    print("="*60)
    
    try:
        process.wait()
    except KeyboardInterrupt:
        print("\nStopping server...")
        process.terminate()
