#!/bin/bash
#===============================================
# RAG System Launcher for Linux/Mac
#===============================================

echo "========================================"
echo "     RAG System Launcher"
echo "========================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check dependencies
echo "Checking dependencies..."
pip install -q -r requirements.txt

# Run the cross-platform main script
echo ""
echo "Starting RAG System..."
python main.py "$@"

deactivate
