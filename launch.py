import os
import subprocess
import signal
import sys
import time

# Kill any existing Python processes
os.system("pkill -f 'python app.py' || true")
time.sleep(1)

# Start the Flask app in a new process
print("Starting Flask application...")
process = subprocess.Popen(["python", "app.py"])

try:
    # Keep the script running
    print("Flask app is running, press Ctrl+C to stop")
    process.wait()
except KeyboardInterrupt:
    # Handle Ctrl+C
    print("\nShutting down Flask application...")
    process.send_signal(signal.SIGINT)
    process.wait()
    sys.exit(0)