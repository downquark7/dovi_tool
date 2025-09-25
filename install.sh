#!/bin/bash
# Installation script for Dolby Vision RPU to HDR10+ converter

set -e

echo "Dolby Vision RPU to HDR10+ Converter Installation"
echo "=================================================="

# Check if Python 3.8+ is available
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi

echo "✓ Python $python_version detected"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not available. Please install pip3 first."
    exit 1
fi

echo "✓ pip3 detected"

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Python dependencies installed successfully"
else
    echo "Error: Failed to install Python dependencies"
    exit 1
fi

# Check if Rust is installed (required for dovi_tool)
if ! command -v cargo &> /dev/null; then
    echo "Warning: Rust is not installed. dovi_tool requires Rust."
    echo "Please install Rust from https://rustup.rs/ and then run:"
    echo "  cargo install dovi_tool"
    echo ""
    echo "Alternatively, you can install dovi_tool manually:"
    echo "  git clone https://github.com/quietvoid/dovi_tool.git"
    echo "  cd dovi_tool"
    echo "  cargo build --release"
    echo "  sudo cp target/release/dovi_tool /usr/local/bin/"
    echo ""
    echo "Continuing with installation (dovi_tool will be required at runtime)..."
else
    echo "✓ Rust detected"
    
    # Install dovi_tool
    echo "Installing dovi_tool..."
    cargo install dovi_tool
    
    if [ $? -eq 0 ]; then
        echo "✓ dovi_tool installed successfully"
    else
        echo "Warning: Failed to install dovi_tool. You may need to install it manually."
    fi
fi

# Install the package in development mode
echo "Installing package in development mode..."
pip3 install -e .

if [ $? -eq 0 ]; then
    echo "✓ Package installed successfully"
else
    echo "Error: Failed to install package"
    exit 1
fi

# Run tests
echo "Running tests..."
python3 -m pytest tests/ -v

if [ $? -eq 0 ]; then
    echo "✓ All tests passed"
else
    echo "Warning: Some tests failed. Check the output above for details."
fi

# Create example directory
mkdir -p examples
echo "✓ Example directory created"

# Make example scripts executable
chmod +x examples/*.py 2>/dev/null || true
echo "✓ Example scripts made executable"

echo ""
echo "Installation completed successfully!"
echo ""
echo "Usage examples:"
echo "  # Convert HEVC file to HDR10+ JSON"
echo "  dovi-to-hdr10plus input.hevc output.json"
echo ""
echo "  # Use machine learning for conversion"
echo "  dovi-to-hdr10plus input.hevc output.json --use-ml"
echo ""
echo "  # Validate existing HDR10+ JSON file"
echo "  dovi-to-hdr10plus --validate input.json"
echo ""
echo "  # Generate example HDR10+ JSON"
echo "  dovi-to-hdr10plus --generate-example example.json"
echo ""
echo "  # Show RPU information"
echo "  dovi-to-hdr10plus --rpu-info input.hevc"
echo ""
echo "For more information, see README.md and API_REFERENCE.md"