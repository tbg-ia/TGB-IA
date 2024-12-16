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
        
    def get_account_info(self):
        """Get account information including balance"""
        try:
            response = self._client.request(f"v3/accounts/{self._account_id}")
            if response and "account" in response:
                account = response["account"]
                return {
                    "balance": float(account.get("balance", 0)),
                    "currency": account.get("currency", "USD"),
                    "margin_rate": float(account.get("marginRate", 0)),
                }
            return None
        except V20Error as e:
            logger.error(f"Error getting account info: {str(e)}")
            return None
            
    def get_price(self, instrument):
        """Get current price for an instrument"""
        try:
            response = self._client.request(f"v3/instruments/{instrument}/candles")
            if response and "candles" in response:
                return float(response["candles"][-1]["mid"]["c"])
            return None
        except V20Error as e:
            logger.error(f"Error getting price for {instrument}: {str(e)}")
            return None
            
    def get_orderbook(self, instrument):
        """Get order book for an instrument"""
        try:
            response = self._client.request(f"v3/instruments/{instrument}/orderBook")
            if response and "orderBook" in response:
                book = response["orderBook"]
                return {
                    "asks": [[float(price), float(size)] for price, size in book.get("asks", [])],
                    "bids": [[float(price), float(size)] for price, size in book.get("bids", [])]
                }
            return None
        except V20Error as e:
            logger.error(f"Error getting orderbook: {str(e)}")
            return None
            
    def get_open_orders(self):
        """Get list of open orders"""
        try:
            response = self._client.request(f"v3/accounts/{self._account_id}/orders")
            if response and "orders" in response:
                return [{
                    "id": order["id"],
                    "instrument": order["instrument"],
                    "units": float(order["units"]),
                    "price": float(order.get("price", 0)),
                    "type": order["type"]
                } for order in response["orders"]]
            return []
        except V20Error as e:
            logger.error(f"Error getting open orders: {str(e)}")
            return []
            
    def place_order(self, symbol, side, units, price=None):
        """Place a new order"""
        try:
            order_data = {
                "order": {
                    "type": "MARKET" if price is None else "LIMIT",
                    "instrument": symbol,
                    "units": str(units if side.upper() == "BUY" else -units),
                }
            }
            
            if price is not None:
                order_data["order"]["price"] = str(price)
                
            response = self._client.request(
                f"v3/accounts/{self._account_id}/orders",
                "POST",
                data=order_data
            )
            
            if response and "orderFillTransaction" in response:
                return {
                    "id": response["orderFillTransaction"]["id"],
                    "price": float(response["orderFillTransaction"]["price"]),
                    "units": float(response["orderFillTransaction"]["units"])
                }
            return None
                
        except V20Error as e:
            logger.error(f"Error placing order: {str(e)}")
            return None

def init_oanda(app):
    """Initialize OANDA client with app configuration."""
    api_key = app.config.get('OANDA_API_KEY')
    account_id = app.config.get('OANDA_ACCOUNT_ID')
    
    if not all([api_key, account_id]):
        logger.warning("Credenciales de OANDA no configuradas")
        return None
        
    try:
        logger.info(f"Inicializando integración de OANDA con cuenta {account_id}")
        client = OandaClient.get_instance()
        
        if client.init_client(api_key, account_id):
            logger.info("Integración de OANDA inicializada exitosamente")
            return client
        else:
            logger.error("Falló la inicialización de la integración de OANDA")
            return None
            
    except Exception as e:
        logger.error(f"Error al inicializar OANDA: {str(e)}")
        return None
