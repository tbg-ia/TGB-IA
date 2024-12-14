"""
Futures market integrations package.
Handles integrations with futures brokers.
"""

from flask import current_app
import logging

logger = logging.getLogger(__name__)

def init_futures(app):
    """Initialize futures broker integrations."""
    logger.info("Initializing futures market integrations...")
    
    # Initialize futures broker clients if configured
    if app.config.get('FUTURES_API_KEY'):
        from .futures_client import init_futures_broker
        init_futures_broker(app)
