#!/bin/bash
# Agentic Calendar - Setup Script for macOS (Homebrew)
# This script sets up the development environment

set -e

echo "=========================================="
echo "  Agentic Calendar - Setup Script"
echo "=========================================="
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✓ Homebrew is installed"
fi

# Check if Python 3.11+ is installed
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Python 3.10+ is required. Installing Python 3.11 via Homebrew..."
    brew install python@3.11
    PYTHON_CMD="python3.11"
else
    echo "✓ Python $PYTHON_VERSION is installed"
    PYTHON_CMD="python3"
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API key!"
    echo "   You need either an OpenAI or Anthropic API key."
else
    echo "✓ .env file already exists"
fi

# Create necessary directories
mkdir -p sessions exports

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "To run the application:"
echo ""
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Make sure you've added your API key to .env"
echo ""
echo "  3. Run the app:"
echo "     streamlit run app.py"
echo ""
echo "The app will open in your browser at http://localhost:8501"
echo ""
