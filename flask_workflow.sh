#!/bin/bash
# Stop any running Node.js processes
pkill -f "node.*server/index.ts" || true
# Run the Flask application
python flask_techblog.py