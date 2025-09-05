#!/usr/bin/env python
"""
System Check Script for RAG System
Verifies all components are properly installed and configured
"""

import sys
import os
import json
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version is 3.8+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_package_installed(package_name):
    """Check if a Python package is installed"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False

def check_dependencies():
    """Check all required packages are installed"""
    required = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "pyyaml",
        "requests",
        "PySide6"
    ]
    
    all_installed = True
    for package in required:
        if check_package_installed(package):
            print(f"✅ {package}")
        else:
            print(f"❌ {package} not installed")
            all_installed = False
    
    return all_installed

def check_directory_structure():
    """Verify the RAG module structure"""
    required_dirs = [
        "rag",
        "rag/core",
        "rag/di",
        "rag/adapters",
        "rag/chunkers",
        "rag/stores",
        "rag/retrievers",
        "rag/rerankers",
        "rag/parsers",
        "rag/pipeline",
        "rag/ingest"
    ]
    
    all_exists = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ missing")
            all_exists = False
    
    return all_exists

def check_files():
    """Check critical files exist"""
    critical_files = [
        "server.py",
        "run_server.py",
        "qt_app_styled.py",
        "requirements.txt",
        "sample_docs.json"
    ]
    
    all_exists = True
    for file_path in critical_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} missing")
            all_exists = False
    
    return all_exists

def check_server_connectivity():
    """Test server connectivity"""
    try:
        import requests
        response = requests.get("http://localhost:7001/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running on port 7001")
            return True
        else:
            print("⚠️ Server responded but with error")
            return False
    except:
        print("⚠️ Server not running (start with: python run_server.py)")
        return False

def main():
    print("=" * 60)
    print("RAG System Health Check")
    print("=" * 60)
    
    checks = []
    
    print("\n1. Python Version:")
    checks.append(check_python_version())
    
    print("\n2. Required Packages:")
    checks.append(check_dependencies())
    
    print("\n3. Directory Structure:")
    checks.append(check_directory_structure())
    
    print("\n4. Critical Files:")
    checks.append(check_files())
    
    print("\n5. Server Status:")
    server_running = check_server_connectivity()
    
    print("\n" + "=" * 60)
    if all(checks):
        print("✅ All system checks passed!")
        if not server_running:
            print("\nTo start the system:")
            print("1. Run: python run_server.py")
            print("2. Then: python qt_app_styled.py")
            print("\nOr use: start_rag.bat (Windows)")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nTo reinstall dependencies:")
        print("pip install -r requirements.txt")
    
    print("=" * 60)
    
    return 0 if all(checks) else 1

if __name__ == "__main__":
    sys.exit(main())
