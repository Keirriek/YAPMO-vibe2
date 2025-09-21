#!/bin/bash
# Poetry Memory Test Runner voor Fill Database V2

echo "🧪 Fill Database V2 - Poetry Memory Test Runner"
echo "=============================================="
echo ""

# Check if we're in the right directory
if [ ! -f "/workspaces/pyproject.toml" ]; then
    echo "❌ Error: Not in Poetry project directory"
    echo "Please run from /workspaces directory"
    exit 1
fi

# Check if main.py exists in app directory
if [ ! -f "/workspaces/app/main.py" ]; then
    echo "❌ Error: main.py not found in /workspaces/app"
    echo "Please check app directory structure"
    exit 1
fi

# Check if Poetry is available
if ! command -v poetry &> /dev/null; then
    echo "❌ Error: Poetry not installed"
    echo "Please install Poetry first"
    exit 1
fi

echo "📁 Working directory: $(pwd)"
echo "🐍 Poetry project detected"
echo ""

# Check if psutil is available
poetry run python -c "import psutil" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: psutil not installed"
    echo "Installing psutil..."
    poetry add psutil
fi

echo "🚀 Starting Memory Monitor with Poetry..."
echo "========================================"
echo "📊 Monitor will log to: /workspaces/test/memory_log.txt"
echo "📈 Report will be saved to: /workspaces/test/memory_report.txt"
echo ""
echo "📱 To start the app, run in another terminal:"
echo "   cd /workspaces/app && poetry run python main.py"
echo ""
echo "⏹️  Press Ctrl+C to stop monitoring"
echo ""

# Start memory monitor with Poetry
poetry run python test/memory_monitor.py
