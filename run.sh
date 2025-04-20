#!/bin/bash

# Kill any existing Python processes running app.py
pkill -f "python app.py" || true

# Wait a moment for ports to be released
sleep 2

# Run the application on port 8080 (which is the default port expected by Replit)
python app.py