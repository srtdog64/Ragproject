"""
Quick test to check server status on both ports
"""
import requests
import time

def check_server(port):
    """Check if server is running on specified port"""
    print(f"\nChecking port {port}...")
    base_url = f"http://localhost:{port}"
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=2)
        print(f"  ✓ Server is running on port {port}")
        print(f"  Health response: {response.json()}")
        
        # Test /api/rag/stats
        response = requests.get(f"{base_url}/api/rag/stats", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ /api/rag/stats works!")
            print(f"    Vectors: {data.get('total_vectors', 0)}")
            print(f"    Store: {data.get('store_type', 'unknown')}")
        else:
            print(f"  ✗ /api/rag/stats returned: {response.status_code}")
            
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"  ✗ No server on port {port}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Server Port Check")
    print("="*60)
    
    # Check both ports
    ports = [7001, 8000, 8001]
    active_ports = []
    
    for port in ports:
        if check_server(port):
            active_ports.append(port)
    
    print("\n" + "="*60)
    print("Summary:")
    if active_ports:
        print(f"Active servers found on ports: {active_ports}")
        if len(active_ports) > 1:
            print("\n⚠ WARNING: Multiple servers running!")
            print("This may cause conflicts. Stop unnecessary servers.")
    else:
        print("No servers found running.")
        print("\nTo start the server:")
        print("  python -m uvicorn server:app --port 7001")
    
    print("="*60)
