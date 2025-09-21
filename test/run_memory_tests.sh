#!/bin/bash
# Memory Leak Test Runner voor Fill Database V2

echo "🔍 Fill Database V2 - Memory Leak Testing"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "/workspaces/app/pages/fill_db_page_v2.py" ]; then
    echo "❌ Error: Not in correct directory"
    echo "Please run from /workspaces directory"
    exit 1
fi

# Set Python path
export PYTHONPATH="/workspaces:$PYTHONPATH"

echo "📁 Working directory: $(pwd)"
echo "🐍 Python path: $PYTHONPATH"
echo ""

# Check if psutil is available
python3 -c "import psutil" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: psutil not installed"
    echo "Installing psutil..."
    pip install psutil
fi

echo "🚀 Running quick memory test..."
echo "================================"
python3 test/test_memory_quick.py

echo ""
echo "🧪 Running full memory test..."
echo "=============================="
python3 test/test_memory_leaks.py

echo ""
echo "✅ Memory leak testing completed"
