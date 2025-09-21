#!/bin/bash

echo "Stopping NiceGUI processes..."

# Stap 1: Kill alle processen met "main.py" in command line
echo "Killing main.py processes..."
pkill -f "main.py" 2>/dev/null || true

# Stap 2: Wacht even en controleer of poorten vrij zijn
sleep 0.5
lsof -ti:8080 2>/dev/null | xargs -r kill -9 2>/dev/null || true

# Stap 3: Zoek naar andere "poetry run python" processen
echo "Checking for other poetry run python processes..."
poetry_processes=$(pgrep -f "poetry run python" 2>/dev/null)

if [ -n "$poetry_processes" ]; then
    echo "Found other poetry run python processes:"
    
    for pid in $poetry_processes; do
        cmd=$(ps -p $pid -o args= 2>/dev/null)
        echo "PID $pid: $cmd"
        
        read -p "Kill this process? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Killing PID $pid..."
            kill -9 $pid 2>/dev/null || true
        else
            echo "Keeping PID $pid alive"
        fi
    done
else
    echo "No other poetry run python processes found"
fi

echo "Script completed"