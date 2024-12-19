"""
Crypto market integrations package.
Handles integrations with cryptocurrency exchanges like Binance and BingX.
"""

from flask import current_app
import logging

logger = logging.getLogger(__name__)

def init_crypto(app):
    """Initialize BingX cryptocurrency exchange integration."""
    logger.info("Initializing BingX market integration...")
    
    # Initialize BingX client if configured
    if app.config.get('BINGX_API_KEY') and app.config.get('BINGX_API_SECRET'):
        from .bingx_client import init_bingx
        init_bingx(app)
    else:
        logger.warning("BingX API credentials not configured")
