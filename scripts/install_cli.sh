#!/bin/sh

# Install Cycloid CLI - Use local binary if available, otherwise download official one
echo "Installing Cycloid CLI..."

# Debug: Check what's in /app/bin directory
echo "DEBUG: Contents of /app/bin directory:"
if [ -d "/app/bin" ]; then
    ls -la /app/bin/
else
    echo "DEBUG: /app/bin directory does not exist"
fi

# Check for local binaries in mounted volume
if [ -f "/app/bin/cy" ]; then
    echo "Using local CLI binary (cy)..."
    cp /app/bin/cy /usr/local/bin/cy
    chmod +x /usr/local/bin/cy
elif [ -f "/app/bin/cy-linux-amd64" ]; then
    echo "Using local CLI binary (cy-linux-amd64)..."
    cp /app/bin/cy-linux-amd64 /usr/local/bin/cy
    chmod +x /usr/local/bin/cy
else
    echo "No local CLI binary found, downloading official binary..."
    rm -f /usr/local/bin/cy
    curl -L https://github.com/cycloidio/cycloid-cli/releases/latest/download/cy-linux-amd64 -o /usr/local/bin/cy
    chmod +x /usr/local/bin/cy
fi

echo "CLI installation complete:"
echo "  - Binary location: /usr/local/bin/cy"
echo "  - Version: $(/usr/local/bin/cy --version 2>/dev/null || echo 'Version check failed')"

# Set environment variable to point to the installed CLI
export CY_CLI_PATH="/usr/local/bin/cy"
echo "  - CY_CLI_PATH set to: $CY_CLI_PATH"
