"""
Crypto market integrations package.
Handles integrations with cryptocurrency exchanges like Binance and BingX.
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
    
    # Initialize BingX client if configured
    if app.config.get('BINGX_API_KEY') and app.config.get('BINGX_API_SECRET'):
        from .bingx_client import init_bingx
        init_bingx(app)
