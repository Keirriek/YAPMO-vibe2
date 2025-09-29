#!/bin/bash

echo "Checking NiceGUI processes..."

# Stap 1: Toon alle processen met "main.py" in command line
echo "Processes with 'main.py' in command line:"
main_processes=$(pgrep -f "main.py" 2>/dev/null)

if [ -n "$main_processes" ]; then
    for pid in $main_processes; do
        cmd=$(ps -p $pid -o pid,args= 2>/dev/null)
        echo "  $cmd"
    done
else
    echo "  No processes found with 'main.py'"
fi

echo

# Stap 2: Controleer poort 8080
echo "Processes using port 8080:"
port_processes=$(lsof -ti:8080 2>/dev/null)

if [ -n "$port_processes" ]; then
    for pid in $port_processes; do
        cmd=$(ps -p $pid -o pid,args= 2>/dev/null)
        echo "  $cmd"
    done
else
    echo "  No processes found using port 8080"
fi

echo

# Stap 3: Zoek naar "poetry run python" processen
echo "Poetry run python processes:"
poetry_processes=$(pgrep -f "poetry run python" 2>/dev/null)

if [ -n "$poetry_processes" ]; then
    for pid in $poetry_processes; do
        cmd=$(ps -p $pid -o pid,args= 2>/dev/null)
        echo "  $cmd"
    done
else
    echo "  No poetry run python processes found"
fi

echo
echo "Script completed - no processes were killed"
