#!/bin/bash
set -e

echo "=== Audio-to-Text Installer ==="

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    PKG_MANAGER="apt-get"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    PKG_MANAGER="brew"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

# Install ffmpeg
echo "[1/3] Installing ffmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "ffmpeg already installed"
else
    if [[ "$OS" == "linux" ]]; then
        sudo apt-get update && sudo apt-get install -y ffmpeg
    else
        brew install ffmpeg
    fi
fi

# Install uv
echo "[2/3] Installing uv..."
if command -v uv &> /dev/null; then
    echo "uv already installed"
else
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install Python dependencies
echo "[3/3] Installing Python dependencies..."
uv sync

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Usage:"
echo "  uv run att stt /path/to/audio.mp3"
echo ""
echo "For GPU support, ensure CUDA and cuDNN are installed."
