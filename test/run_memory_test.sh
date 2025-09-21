#!/bin/bash
# Memory Test Runner voor Fill Database V2

echo "🧪 Fill Database V2 - Memory Test Runner"
echo "========================================"
echo ""

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
poetry run python -c "import psutil" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: psutil not installed"
    echo "Installing psutil..."
    poetry add psutil
fi

echo "🚀 Starting Memory Monitor..."
echo "=============================="
echo "📊 Monitor will log to: /workspaces/test/memory_log.txt"
echo "📈 Report will be saved to: /workspaces/test/memory_report.txt"
echo ""
echo "⏹️  Press Ctrl+C to stop monitoring"
echo ""

# Start memory monitor
poetry run python test/memory_monitor.py
