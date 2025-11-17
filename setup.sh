#!/bin/bash

# GEPA Multi-Disease Antibody Optimization Setup Script

echo "======================================"
echo "GEPA Setup Script"
echo "======================================"
echo ""

# Check Python version
echo "[1/4] Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Found Python $python_version"

# Create virtual environment (optional)
echo ""
echo "[2/4] Creating virtual environment (optional)..."
read -p "Create virtual environment? (y/n): " create_venv

if [ "$create_venv" = "y" ]; then
    python3 -m venv venv
    echo "  Virtual environment created"
    echo "  To activate: source venv/bin/activate"
fi

# Install dependencies
echo ""
echo "[3/4] Installing dependencies..."
pip install -r requirements.txt
echo "  Dependencies installed"

# Check API key
echo ""
echo "[4/4] Checking OpenAI API key..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "  ⚠️  WARNING: OPENAI_API_KEY not set"
    echo "  Please set it before running:"
    echo "    export OPENAI_API_KEY='your-api-key-here'"
else
    echo "  ✓ OPENAI_API_KEY is set"
fi

echo ""
echo "======================================"
echo "Setup complete!"
echo "======================================"
echo ""
echo "To run the optimizer:"
echo "  python main.py"
echo ""

