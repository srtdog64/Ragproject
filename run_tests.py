#!/usr/bin/env python
"""
Test runner for RAG system
Run tests from the project root directory
"""
import sys
import os
import subprocess

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def run_test(test_file):
    """Run a single test file"""
    print(f"\n{'='*60}")
    print(f"Running: {test_file}")
    print('='*60)
    
    test_path = os.path.join('tests', test_file)
    try:
        result = subprocess.run(
            [sys.executable, test_path],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {test_file}: {e}")
        return False

def main():
    """Main test runner"""
    tests = {
        '1': ('test_embedder_manager.py', 'Embedder Manager Tests'),
        '2': ('test_chunking.py', 'Chunking Tests'),
        '3': ('test_client.py', 'Client Tests'),
        '4': ('test_gemini.py', 'Gemini API Tests'),
        '5': ('health_check.py', 'System Health Check'),
        '6': ('check_system.py', 'System Dependencies Check'),
        'a': ('all', 'Run All Tests'),
    }
    
    print("\nRAG System Test Suite")
    print("-" * 40)
    for key, (file, desc) in tests.items():
        if key != 'a':
            print(f"[{key}] {desc}")
    print(f"[a] Run All Tests")
    print("[q] Quit")
    
    choice = input("\nSelect test to run: ").strip().lower()
    
    if choice == 'q':
        print("Exiting...")
        return
    
    if choice == 'a':
        # Run all tests
        results = {}
        for key in ['1', '2', '3', '4', '5', '6']:
            file, desc = tests[key]
            results[desc] = run_test(file)
        
        # Summary
        print(f"\n{'='*60}")
        print("Test Summary")
        print('='*60)
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name}: {status}")
    
    elif choice in tests:
        file, desc = tests[choice]
        success = run_test(file)
        if success:
            print(f"\n✅ {desc} completed successfully!")
        else:
            print(f"\n❌ {desc} failed!")
    else:
        print("Invalid selection")

if __name__ == "__main__":
    main()
