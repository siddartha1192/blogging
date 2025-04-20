#!/bin/bash
# Stop any running Python processes
pkill -f "python.*run.py" || true
# Run the Flask application
python run.py