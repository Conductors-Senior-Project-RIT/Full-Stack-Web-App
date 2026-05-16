"""
WSGI entry point for production deployments (e.g. uWSGI, and more).
"""

from backend import create_app

application = create_app("prod")