#!/usr/bin/env python
"""
Test Qt App status bar initialization
"""

import sys
import time
import requests

def check_server_status():
    """Check server status"""
    try:
        response = requests.get("http://localhost:7001/health")
        if response.status_code == 200:
            print("✅ Server is online")
            return True
    except:
        print("❌ Server is offline")
    return False

def get_current_strategy():
    """Get current strategy from server"""
    try:
        response = requests.get("http://localhost:7001/api/chunkers/strategy")
        if response.status_code == 200:
            data = response.json()
            strategy = data.get('strategy', 'unknown')
            print(f"📦 Current server strategy: {strategy}")
            return strategy
    except Exception as e:
        print(f"❌ Failed to get strategy: {e}")
    return None

def set_strategy(strategy):
    """Set strategy on server"""
    try:
        response = requests.post(
            "http://localhost:7001/api/chunkers/strategy",
            json={"strategy": strategy},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print(f"✅ Strategy set to: {strategy}")
            return True
    except Exception as e:
        print(f"❌ Failed to set strategy: {e}")
    return False

def main():
    print("="*60)
    print("Qt App Status Bar Test")
    print("="*60)
    
    # Check server
    if not check_server_status():
        print("\nPlease start the server first:")
        print("  python start_server.py")
        return
    
    # Get current strategy
    current = get_current_strategy()
    
    # Test setting different strategies
    test_strategies = ["adaptive", "sentence", "paragraph"]
    
    print("\n" + "="*60)
    print("Testing strategy changes...")
    print("="*60)
    
    for strategy in test_strategies:
        print(f"\n1. Setting strategy to: {strategy}")
        if set_strategy(strategy):
            time.sleep(0.5)
            
            print("2. Verifying on server...")
            server_strategy = get_current_strategy()
            
            if server_strategy == strategy:
                print(f"✅ Server correctly shows: {server_strategy}")
            else:
                print(f"❌ Mismatch! Expected {strategy}, got {server_strategy}")
            
            print("3. Now start Qt App and check if status bar shows:")
            print(f"   Expected: 📦 Strategy: {strategy}")
            print("   NOT: 📦 Strategy: Loading...")
            
            input("\nPress Enter after checking Qt App...")
    
    print("\n" + "="*60)
    print("Test complete!")
    print("\nThe Qt App status bar should:")
    print("1. Show the current strategy immediately (not 'Loading...')")
    print("2. Update when you change strategy in Options tab")
    print("3. Stay synced with server")
    print("="*60)

if __name__ == "__main__":
    main()
