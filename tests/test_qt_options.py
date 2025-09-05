#!/usr/bin/env python
"""
Test Qt Options Widget server synchronization
"""

import sys
import os
import requests
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt

# Add paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.options_widget import OptionsWidget
from ui.config_manager import ConfigManager

def check_server():
    """Check if server is running"""
    try:
        response = requests.get("http://localhost:7001/health")
        if response.status_code == 200:
            print("✅ Server is running")
            return True
    except:
        print("❌ Server is not running")
        print("Please start the server: python start_server.py")
        return False

def check_current_strategy():
    """Check current strategy on server"""
    try:
        response = requests.get("http://localhost:7001/api/chunkers/current")
        if response.status_code == 200:
            data = response.json()
            print(f"📦 Current server strategy: {data.get('strategy', 'unknown')}")
            return data.get('strategy')
    except Exception as e:
        print(f"❌ Failed to get strategy: {e}")
    return None

def main():
    print("=" * 60)
    print("Qt Options Widget Server Sync Test")
    print("=" * 60)
    
    # Check server
    if not check_server():
        return
    
    # Check current strategy
    server_strategy = check_current_strategy()
    
    # Create Qt app
    app = QApplication(sys.argv)
    
    # Create config manager
    config = ConfigManager()
    
    # Create options widget
    widget = OptionsWidget(config)
    
    # Check if widget loaded the correct strategy
    print(f"\nWidget strategy: {widget.currentStrategy}")
    print(f"Combo selection: {widget.strategyCombo.currentText()}")
    
    if server_strategy and widget.currentStrategy == server_strategy:
        print("✅ Widget correctly synced with server!")
    else:
        print("❌ Widget not synced with server")
    
    # Create main window for display
    window = QMainWindow()
    window.setCentralWidget(widget)
    window.setWindowTitle("Options Widget Test")
    window.resize(800, 600)
    window.show()
    
    print("\n" + "="*60)
    print("Test the following:")
    print("1. Check if current strategy matches server")
    print("2. Try changing strategy and see if it syncs")
    print("3. Use the 🔄 refresh button to sync from server")
    print("="*60)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
