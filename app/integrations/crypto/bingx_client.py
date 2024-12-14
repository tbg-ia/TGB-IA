import hmac
import hashlib
import time
import requests
import logging
from urllib.parse import urlencode
from flask import current_app

logger = logging.getLogger(__name__)

class BingXClient:
    _instance = None
    BASE_URL = "https://open-api.bingx.com"
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._api_key = None
        self._api_secret = None

    def init_client(self, api_key, api_secret):
        """Initialize the BingX client with API credentials"""
        try:
            self._api_key = api_key
            self._api_secret = api_secret
            
            # Test connection
            self.get_server_time()
            logger.info("BingX client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing BingX client: {str(e)}")
            return False

    def _generate_signature(self, params):
        """Generate signature for authenticated requests"""
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _make_request(self, method, endpoint, params=None, signed=False):
        """Make request to BingX API"""
        url = f"{self.BASE_URL}{endpoint}"
        headers = {'X-BX-APIKEY': self._api_key}
        
        if params is None:
            params = {}
            
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers)
            else:
                response = requests.post(url, json=params, headers=headers)
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            raise

    def get_server_time(self):
        """Get BingX server time"""
        return self._make_request('GET', '/openApi/swap/v2/server/time')

    def get_symbol_price(self, symbol):
        """Get current price for a trading pair"""
        try:
            response = self._make_request(
                'GET', 
                '/openApi/swap/v2/quote/price', 
                {'symbol': symbol}
            )
            return float(response['data']['price'])
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {str(e)}")
            return None

    def place_order(self, symbol, side, quantity, price=None, order_type="MARKET"):
        """Place a new order"""
        try:
            params = {
                'symbol': symbol,
                'side': side.upper(),
                'type': order_type,
                'quantity': quantity,
            }
            if price and order_type == "LIMIT":
                params['price'] = price

            response = self._make_request(
                'POST',
                '/openApi/swap/v2/trade/order',
                params,
                signed=True
            )
            logger.info(f"Order placed successfully: {response}")
            return response
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return None

def init_bingx(app):
    """Initialize BingX client with app configuration."""
    api_key = app.config.get('BINGX_API_KEY')
    api_secret = app.config.get('BINGX_API_SECRET')
    
    if not all([api_key, api_secret]):
        logger.warning("BingX API credentials not configured")
        return
    
    client = BingXClient.get_instance()
    if client.init_client(api_key, api_secret):
        logger.info("BingX integration initialized successfully")
    else:
        logger.error("Failed to initialize BingX integration")
