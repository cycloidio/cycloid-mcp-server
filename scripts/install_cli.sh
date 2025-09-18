#!/bin/sh

# Install Cycloid CLI - Use local binary if available, otherwise download official one
echo "Installing Cycloid CLI..."

# Function to detect architecture
detect_arch() {
    local arch=$(uname -m)
    case $arch in
        x86_64|amd64)
            echo "amd64"
            ;;
        aarch64|arm64)
            echo "arm64"
            ;;
        armv7l)
            echo "arm"
            ;;
        *)
            echo "unsupported"
            ;;
    esac
}

# Function to get latest release version
get_latest_version() {
    curl -s https://api.github.com/repos/cycloidio/cycloid-cli/releases/latest | \
    grep '"tag_name"' | \
    sed -E 's/.*"([^"]+)".*/\1/'
}

# Check for local binary first (for development)
if [ -f "/app/bin/cy" ]; then
    echo "Using local CLI binary (cy) for development..."
    cp /app/bin/cy /usr/local/bin/cy
    chmod +x /usr/local/bin/cy
else
    echo "No local CLI binary found, downloading official binary..."

    # Detect architecture
    ARCH=$(detect_arch)
    echo "Detected architecture: $ARCH"

    if [ "$ARCH" = "unsupported" ]; then
        echo "ERROR: Unsupported architecture: $(uname -m)"
        exit 1
    fi

    # Get latest version
    VERSION=$(get_latest_version)
    echo "Latest version: $VERSION"

    # Construct download URL
    # Note: Cycloid CLI provides cy-linux-amd64 for AMD64, but no cy-linux-arm64
    # For ARM64/ARM, we'll use the generic 'cy' binary which is AMD64 but works with emulation
    if [ "$ARCH" = "amd64" ]; then
        BINARY_NAME="cy-linux-amd64"
    elif [ "$ARCH" = "arm64" ]; then
        echo "WARNING: Linux ARM64 binary not available, using generic binary (requires emulation)"
        BINARY_NAME="cy"
    elif [ "$ARCH" = "arm" ]; then
        echo "WARNING: Linux ARM binary not available, using generic binary (requires emulation)"
        BINARY_NAME="cy"
    fi

    DOWNLOAD_URL="https://github.com/cycloidio/cycloid-cli/releases/download/${VERSION}/${BINARY_NAME}"
    echo "Downloading from: $DOWNLOAD_URL"

    # Download and install
    rm -f /usr/local/bin/cy
    if ! curl -L "$DOWNLOAD_URL" -o /usr/local/bin/cy; then
        echo "ERROR: Failed to download CLI binary"
        exit 1
    fi
    chmod +x /usr/local/bin/cy
fi

echo "CLI installation complete:"
echo "  - Binary location: /usr/local/bin/cy"
echo "  - Version: $(/usr/local/bin/cy --version 2>/dev/null || echo 'Version check failed')"

# Set environment variable to point to the installed CLI
export CY_CLI_PATH="/usr/local/bin/cy"
echo "  - CY_CLI_PATH set to: $CY_CLI_PATH"
