import subprocess
import time
import sys

print("Starting Flask TechBlog application on port 5001...")
try:
    # Run the Flask application
    flask_process = subprocess.Popen(["python", "flask_techblog.py"])
    
    # Keep script running to maintain the Flask process
    while True:
        # Check if the Flask process is still running
        if flask_process.poll() is not None:
            print("Flask application stopped unexpectedly with code:", flask_process.returncode)
            break
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping Flask application...")
    flask_process.terminate()
    flask_process.wait()
    print("Flask application stopped.")
except Exception as e:
    print(f"Error: {e}")
    if 'flask_process' in locals():
        flask_process.terminate()
        flask_process.wait()
    sys.exit(1)