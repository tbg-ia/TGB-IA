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
    from .crypto import init_crypto, init_binance, init_bingx, init_kucoin, init_bybit
    from .forex import init_forex, init_oanda, init_ig, init_fxcm
    from .stocks import init_stocks
    from .futures import init_futures
    
    # Initialize crypto exchanges
    init_crypto(app)
    init_binance(app)
    init_bingx(app)
    init_kucoin(app)
    init_bybit(app)
    
    # Initialize forex brokers
    init_forex(app)
    init_oanda(app)
    init_ig(app)
    init_fxcm(app)
    
    # Initialize other markets
    init_stocks(app)
    init_futures(app)
    
    logger.info("Market integrations initialized")
