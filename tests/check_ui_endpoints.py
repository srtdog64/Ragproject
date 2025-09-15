#!/usr/bin/env python
"""
UI Endpoint Verification Script
Checks all UI files for correct API endpoint usage
"""
import os
import re
from pathlib import Path

def check_ui_endpoints():
    """Check all UI files for API endpoint consistency"""
    
    # Define correct endpoints (all with /api prefix)
    correct_endpoints = {
        '/api/ask': 'Question answering',
        '/api/ingest': 'Document ingestion',
        '/api/config/reload': 'Configuration reload',
        '/api/rag/stats': 'RAG statistics',
        '/api/chunkers/strategy': 'Chunker strategy',
        '/api/namespaces': 'Namespace management',
        '/api/switch_namespace': 'Switch namespace',
    }
    
    # Define old endpoints that should be updated
    old_endpoints = {
        '/ask': '/api/ask',
        '/ingest': '/api/ingest',
        '/config/reload': '/api/config/reload',
    }
    
    issues = []
    
    # UI directories to check
    ui_dirs = [
        'E:\\Ragproject\\ui',
        'E:\\Ragproject'  # For qt_app.py
    ]
    
    for base_dir in ui_dirs:
        for root, dirs, files in os.walk(base_dir):
            # Skip backup files and non-UI directories
            if 'backup' in root or 'old_files' in root or 'tests' in root:
                continue
                
            for file in files:
                if file.endswith('.py') and not file.endswith('.backup'):
                    filepath = os.path.join(root, file)
                    
                    # Read file content
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            lines = content.split('\n')
                            
                        # Check for old endpoints
                        for line_num, line in enumerate(lines, 1):
                            # Check for requests calls
                            if 'requests.' in line:
                                # Check for old endpoints
                                for old_ep, new_ep in old_endpoints.items():
                                    if f'"{old_ep}"' in line or f"'{old_ep}'" in line:
                                        issues.append({
                                            'file': filepath,
                                            'line': line_num,
                                            'issue': f'Old endpoint {old_ep} should be {new_ep}',
                                            'content': line.strip()
                                        })
                                
                                # Check if using correct endpoints
                                for endpoint in correct_endpoints:
                                    if endpoint in line:
                                        # This is good, using correct endpoint
                                        pass
                            
                            # Check for f-strings with endpoints
                            if 'f"{' in line or "f'{" in line:
                                for old_ep, new_ep in old_endpoints.items():
                                    if old_ep in line and 'baseUrl' in line:
                                        # Check if it's not already using /api
                                        if '/api' + old_ep not in line:
                                            issues.append({
                                                'file': filepath,
                                                'line': line_num,
                                                'issue': f'Old endpoint {old_ep} should be {new_ep}',
                                                'content': line.strip()
                                            })
                                            
                    except Exception as e:
                        print(f"Error reading {filepath}: {e}")
    
    return issues

def main():
    print("="*60)
    print("UI Endpoint Verification")
    print("="*60)
    
    issues = check_ui_endpoints()
    
    if not issues:
        print("All UI endpoints are using correct /api prefix!")
    else:
        print(f"Found {len(issues)} issues:\n")
        
        # Group by file
        files_with_issues = {}
        for issue in issues:
            file = issue['file']
            if file not in files_with_issues:
                files_with_issues[file] = []
            files_with_issues[file].append(issue)
        
        # Display issues
        for file, file_issues in files_with_issues.items():
            print(f"\n{Path(file).name}")
            print(f"   Path: {file}")
            for issue in file_issues:
                print(f"   Line {issue['line']}: {issue['issue']}")
                print(f"   >>> {issue['content']}")
    
    print("\n" + "="*60)
    print("Verification complete!")
    
    # Summary of endpoints
    print("\nCorrect endpoint structure:")
    print("  /api/ask - Question answering")
    print("  /api/ingest - Document ingestion")
    print("  /api/config/reload - Config reload")
    print("  /api/rag/stats - Statistics")
    print("  /api/chunkers/* - Chunker management")
    print("  /api/namespaces - Namespace management")
    
    return len(issues) == 0

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
