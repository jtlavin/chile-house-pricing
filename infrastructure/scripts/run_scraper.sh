#!/bin/bash

# Script to run the web scraper

set -e

echo "🕷️ Running House Pricing Scraper"
echo "================================"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Check for command line arguments
if [ "$1" == "--demo" ]; then
    echo "Running in DEMO mode (3 properties only)..."
    python -m data-pipeline.jobs.scrape_job --demo
else
    echo "Running in INTERACTIVE mode..."
    python -m data-pipeline.jobs.scrape_job
fi
