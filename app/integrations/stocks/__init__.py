"""
Stock market integrations package.
Handles integrations with stock brokers like Alpaca.
"""

from flask import current_app
import logging

logger = logging.getLogger(__name__)

def init_stocks(app):
    """Initialize stock broker integrations."""
    logger.info("Initializing stock market integrations...")
    
    # Initialize Alpaca client if configured
    if app.config.get('ALPACA_API_KEY') and app.config.get('ALPACA_API_SECRET'):
        from .alpaca_client import init_alpaca
        init_alpaca(app)
