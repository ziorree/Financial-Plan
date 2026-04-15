#!/bin/bash
# Setup and run script for Financial Planner App

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3.8 or later."
    exit 1
fi

# Create virtual environment (optional but recommended)
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install requirements
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run the Streamlit app
echo ""
echo "Starting Financial Planner App..."
echo "The app will open at http://localhost:8501"
echo ""

streamlit run app.py

