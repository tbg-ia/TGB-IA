import logging
from oandapyV20 import API
from oandapyV20.exceptions import V20Error
from flask import current_app

logger = logging.getLogger(__name__)

class OandaClient:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._client = None
        self._account_id = None

    def init_client(self, api_key, account_id):
        """Initialize OANDA client with API credentials"""
        try:
            self._client = API(access_token=api_key)
            self._account_id = account_id
            
            # Test connection by getting account details
            self._client.request(f"v3/accounts/{account_id}")
            logger.info("OANDA client initialized successfully")
            return True
        except V20Error as e:
            logger.error(f"Error initializing OANDA client: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error initializing OANDA client: {str(e)}")
            return False

    def get_client(self):
        return self._client

    def get_account_id(self):
        return self._account_id

    def get_price(self, instrument):
        """Get current price for an instrument"""
        try:
            params = {"instruments": instrument}
            response = self._client.request("v3/instruments/{}/candles".format(instrument))
            if response and "candles" in response:
                return float(response["candles"][-1]["mid"]["c"])
            return None
        except V20Error as e:
            logger.error(f"Error getting price for {instrument}: {str(e)}")
            return None

def init_oanda(app):
    """Initialize OANDA client with app configuration."""
    api_key = app.config.get('OANDA_API_KEY')
    account_id = app.config.get('OANDA_ACCOUNT_ID')
    
    if not all([api_key, account_id]):
        logger.warning("OANDA API credentials not configured")
        return
    
    client = OandaClient.get_instance()
    if client.init_client(api_key, account_id):
        logger.info("OANDA integration initialized successfully")
    else:
        logger.error("Failed to initialize OANDA integration")
