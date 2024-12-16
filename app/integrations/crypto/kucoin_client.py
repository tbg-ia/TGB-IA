import hmac
import hashlib
import time
import requests
import logging
from urllib.parse import urlencode
from flask import current_app

logger = logging.getLogger(__name__)

class KuCoinClient:
    _instance = None
    BASE_URL = "https://api.kucoin.com"
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._api_key = None
        self._api_secret = None
        self._passphrase = None

    def init_client(self, api_key, api_secret, passphrase):
        """Initialize the KuCoin client with API credentials"""
        try:
            self._api_key = api_key
            self._api_secret = api_secret
            self._passphrase = passphrase
            
            # Test connection
            self.get_server_time()
            logger.info("KuCoin client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing KuCoin client: {str(e)}")
            return False

    def _generate_signature(self, timestamp, method, endpoint, body=''):
        """Generate signature for authenticated requests"""
        str_to_sign = f'{timestamp}{method}{endpoint}{body}'
        signature = hmac.new(
            self._api_secret.encode('utf-8'),
            str_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _make_request(self, method, endpoint, params=None, signed=False):
        """Make request to KuCoin API"""
        url = f"{self.BASE_URL}{endpoint}"
        timestamp = str(int(time.time() * 1000))
        headers = {
            'KC-API-KEY': self._api_key,
            'KC-API-TIMESTAMP': timestamp,
            'KC-API-PASSPHRASE': self._passphrase
        }
        
        if signed:
            body = '' if params is None else str(params)
            signature = self._generate_signature(timestamp, method, endpoint, body)
            headers['KC-API-SIGN'] = signature
        
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
        """Get KuCoin server time"""
        return self._make_request('GET', '/api/v1/timestamp')

    def get_symbol_price(self, symbol):
        """Get current price for a trading pair"""
        try:
            response = self._make_request(
                'GET', 
                '/api/v1/market/orderbook/level1', 
                {'symbol': symbol}
            )
            return float(response['data']['price'])
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {str(e)}")
            return None

    def get_account_balance(self):
        """Get account balance"""
        try:
            response = self._make_request(
                'GET',
                '/api/v1/accounts',
                signed=True
            )
            return response.get('data', [])
        except Exception as e:
            logger.error(f"Error getting account balance: {str(e)}")
            return None

def init_kucoin(app):
    """Initialize KuCoin client with app configuration."""
    api_key = app.config.get('KUCOIN_API_KEY')
    api_secret = app.config.get('KUCOIN_API_SECRET')
    passphrase = app.config.get('KUCOIN_API_PASSPHRASE')
    
    if not all([api_key, api_secret, passphrase]):
        logger.warning("KuCoin API credentials not configured")
        return
    
    client = KuCoinClient.get_instance()
    if client.init_client(api_key, api_secret, passphrase):
        logger.info("KuCoin integration initialized successfully")
    else:
        logger.error("Failed to initialize KuCoin integration")
