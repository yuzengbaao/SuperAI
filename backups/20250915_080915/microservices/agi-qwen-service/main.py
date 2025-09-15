"""
Gevent-compatible application entry point.

This file is crucial for ensuring that gevent's monkey-patching is applied
before any other modules (like Flask, Redis, etc.) are imported. This
prevents conflicts between standard blocking sockets and gevent's cooperative
green threads.

The `gunicorn` command should point to this file's `app` object.
Example: gunicorn -c gunicorn.conf.py main:app
"""

# Apply monkey-patching at the very beginning of the application's lifecycle.
# This is the most important step to ensure gevent compatibility.
from gevent import monkey
monkey.patch_all()

# Now that the environment is patched, we can safely import the Flask app.
# The Flask app and its dependencies (like redis-py) will now use gevent's
# non-blocking sockets without any modification.
from microservices.agi-qwen-service.app import app

# The 'app' object is now exposed for the WSGI server (Gunicorn) to use.
# When Gunicorn imports 'main:app', it will get the patched version.
