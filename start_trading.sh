#!/bin/bash

# Trading script starter with virtual environment
# Save this as: /home/siddartha1192/blogging/start_trading.sh

# Set script directory
SCRIPT_DIR="/home/siddartha1192/blogging"
VENV_PATH="/home/siddartha1192/.virtualenvs/flaskapp"
PYTHON_SCRIPT="UpdatedLatest.py"
LOG_FILE="trading_log.txt"

# Change to script directory
cd "$SCRIPT_DIR" || {
    echo "Error: Cannot change to script directory $SCRIPT_DIR"
    exit 1
}

# Check if virtual environment exists
if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script $PYTHON_SCRIPT not found in $SCRIPT_DIR"
    exit 1
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate" || {
    echo "Error: Failed to activate virtual environment"
    exit 1
}

# Verify Python is from virtual environment
echo "Using Python: $(which python)"
echo "Python version: $(python --version)"

# Start the trading script with logging
echo "Starting trading script at $(date)"
exec python "$PYTHON_SCRIPT" > "$LOG_FILE" 2>&1
