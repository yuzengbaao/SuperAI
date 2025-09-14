# gunicorn.conf.py
# Configuration for Gunicorn running the agi-qwen-service

import sys
import os

# Add the service's app directory to the Python path
# This ensures that the 'app' module can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

# --- Gunicorn Settings ---
bind = f"0.0.0.0:{os.getenv('SERVICE_PORT', 8400)}"
workers = 2  # Start with 2 workers
worker_class = "gevent"  # Use gevent for asynchronous workers
timeout = 120
keepalive = 5

# --- Logging ---
accesslog = "-"  # Log access to stdout
errorlog = "-"   # Log errors to stdout
loglevel = "info"

# --- Hooks ---
def post_fork(server, worker):
    """
    Called just after a worker has been forked.
    This is the ideal place to initialize our background tasks,
    ensuring each worker process has its own instance.
    """
    server.log.info(f"Worker spawned (pid: {worker.pid}). Initializing background tasks...")
    
    # We need to import the app module *within the hook* to ensure
    # it's loaded correctly in the context of the worker process.
    from app import start_background_tasks
    
    start_background_tasks()
    server.log.info(f"Worker (pid: {worker.pid}) background tasks initialized.")

def on_exit(server):
    """
    Called just before Gunicorn exits.
    """
    server.log.info("Gunicorn is shutting down...")

