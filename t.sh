#!/bin/bash

echo "Setting timezone to Europe/Amsterdam..."

# Set timezone symlink
sudo ln -sf /usr/share/zoneinfo/Europe/Amsterdam /etc/localtime

# Set timezone file
echo "Europe/Amsterdam" | sudo tee /etc/timezone

# Verify the change
echo "Current timezone:"
date

echo "Timezone setup complete!" 