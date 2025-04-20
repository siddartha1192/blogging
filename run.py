#!/usr/bin/env python3
# Simple launcher for the Flask app
from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)