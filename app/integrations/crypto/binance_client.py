from binance.client import Client
from binance.exceptions import BinanceAPIException
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class BinanceWrapper:
    _instance = None
    _client = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._client = None

    def init_client(self, api_key, api_secret):
        try:
            self._client = Client(api_key, api_secret)
            # Test connection
            self._client.get_system_status()
            logger.info("Binance client initialized successfully")
            return True
        except BinanceAPIException as e:
            logger.error(f"Error initializing Binance client: {str(e)}")
            return False

    def get_client(self):
        return self._client

    def get_symbol_price(self, symbol):
        try:
            ticker = self._client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            logger.error(f"Error getting price for {symbol}: {str(e)}")
            return None

    def place_order(self, symbol, side, quantity):
        try:
            order = self._client.create_order(
                symbol=symbol,
                side=side,
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity
            )
            logger.info(f"Order placed successfully: {order}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Error placing order: {str(e)}")
            return None

def init_binance(app):
    """Initialize Binance client with app configuration."""
    api_key = app.config.get('BINANCE_API_KEY')
    api_secret = app.config.get('BINANCE_API_SECRET')
    
    if not all([api_key, api_secret]):
        logger.warning("Binance API credentials not configured")
        return
    
    client = BinanceWrapper.get_instance()
    if client.init_client(api_key, api_secret):
        logger.info("Binance integration initialized successfully")
    else:
        logger.error("Failed to initialize Binance integration")
