"""
Forex market integrations package.
Handles integrations with forex brokers like OANDA.
"""

from flask import current_app
import logging

logger = logging.getLogger(__name__)

def init_forex(app):
    """Initialize forex broker integrations."""
    logger.info("Initializing forex market integrations...")
    
    # Initialize OANDA client if configured
    if app.config.get('OANDA_API_KEY'):
        from .oanda_client import init_oanda
        init_oanda(app)
