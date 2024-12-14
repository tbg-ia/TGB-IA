"""
Integrations package for external APIs.
This module handles all external API integrations for different financial markets.
"""

from flask import current_app
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_app(app):
    """Initialize all integrations with the Flask application."""
    logger.info("Initializing integrations...")
    
    # Import and initialize all market integrations
    from .crypto import init_crypto
    from .forex import init_forex
    from .stocks import init_stocks
    from .futures import init_futures
    
    init_crypto(app)
    init_forex(app)
    init_stocks(app)
    init_futures(app)
