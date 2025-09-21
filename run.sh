#!/bin/bash

# Script om een commando uit te voeren na cd .. && clear
# Gebruik: ./run.sh "jouw commando hier"

# Controleer of er argumenten zijn meegegeven
if [ $# -eq 0 ]; then
    echo "Gebruik: $0 \"jouw commando hier\""
    echo "Voorbeeld: $0 \"ls -la\""
    echo "Voorbeeld: $0 \"git status\""
    exit 1
fi

# Ga naar de parent directory
cd ..

# Clear het scherm
clear

# Voer het commando uit met alle meegegeven argumenten
echo "Uitvoeren: $*"
echo "----------------------------------------"
"$@" 