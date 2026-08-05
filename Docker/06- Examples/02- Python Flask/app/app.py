"""
Main application module for the Python Flask Docker project.
This simple API demonstrates running a Python web service in a container.
"""

import os
import platform
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

# Fetch the app name from environment variables, defaulting if not set.
app_name = os.getenv("APP_NAME", "Python Flask Docker App")

@app.route("/")
def home():
    # Return JSON response containing environment and system info
    return jsonify({
        "app": app_name,
        "message": "Hello from Flask inside Docker!",
        "hostname": platform.node(),
        "time": datetime.now().isoformat(),
        "python_version": platform.python_version()
    })

@app.route("/health")
def health():
    # Health endpoint commonly used by Docker/Kubernetes to check app status
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    # Run the server on all network interfaces (0.0.0.0) so it's accessible outside the container
    app.run(host="0.0.0.0", port=5000)
