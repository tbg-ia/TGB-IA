"""
Crypto market integrations package.
Handles integrations with cryptocurrency exchanges like Binance.
"""

from flask import current_app
import logging

logger = logging.getLogger(__name__)

def init_crypto(app):
    """Initialize cryptocurrency exchange integrations."""
    logger.info("Initializing crypto market integrations...")
    
    # Initialize Binance client if configured
    if app.config.get('BINANCE_API_KEY') and app.config.get('BINANCE_API_SECRET'):
        from .binance_client import init_binance
        init_binance(app)
