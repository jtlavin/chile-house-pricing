#!/bin/bash

# Setup script for Chile House Pricing MLOps project

set -e

echo "🏠 Setting up Chile House Pricing MLOps Project"
echo "================================================"

# Check Python version
echo "Checking Python version..."
python --version

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -e .

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

# Create necessary directories
echo "Creating data directories..."
mkdir -p ml/data/raw ml/data/processed ml/data/splits
mkdir -p ml/experiments ml/models

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source .venv/bin/activate"
echo "2. Run scraper demo: python -m data-pipeline.jobs.scrape_job --demo"
echo "3. Start API: uvicorn api.app.main:app --reload"
echo "4. Open Jupyter: jupyter notebook ml/notebooks"
