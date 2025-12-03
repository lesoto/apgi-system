#!/bin/bash
# Setup script for APGI REST API

echo "Setting up APGI REST API..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env with your configuration"
fi

echo "Setup complete!"
echo ""
echo "To start the API server:"
echo "  source venv/bin/activate"
echo "  python -m api.main"
echo ""
echo "Or using uvicorn:"
echo "  uvicorn api.main:app --reload"
