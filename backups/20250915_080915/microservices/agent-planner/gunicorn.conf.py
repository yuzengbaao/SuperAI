# gunicorn.conf.py
# Configuration for Gunicorn running the agent-planner service

import sys
import os

# Add the service's app directory to the Python path
# This ensures that the 'app' module can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

# --- Gunicorn Settings ---
bind = f"0.0.0.0:{os.getenv('SERVICE_PORT', 8300)}"
workers = 1  # Set to 1 to avoid multi-process conflicts
# worker_class = "gevent" # No longer using gevent worker class
worker_connections = 1000 # Increase connections for single worker
timeout = 120
keepalive = 5

# --- Logging ---
accesslog = "-"  # Log access to stdout
errorlog = "-"   # Log errors to stdout
loglevel = "info"

# --- Hooks ---
# post_fork hook is removed as we are using @app.before_first_request

def on_exit(server):
    """
    Called just before Gunicorn exits.
    """
    server.log.info("Gunicorn is shutting down...")

