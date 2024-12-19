
from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .base_exchange import BaseExchange

class Exchange(BaseExchange):
    """Model for managing exchange connections and credentials"""
    is_forex = db.Column(db.Boolean, default=False)  
    is_testnet = db.Column(db.Boolean, default=False)  
    max_positions = db.Column(db.Integer, default=5)  
    max_leverage = db.Column(db.Integer, default=20)  
    quote_currency = db.Column(db.String(10), default='USDT')  
    min_order_size = db.Column(db.Float, default=10.0)  
    max_order_size = db.Column(db.Float, default=1000.0)  
    trading_fee = db.Column(db.Float, default=0.1)  
    last_error = db.Column(db.String(500))

    # Relaciones
    bots = db.relationship('TradingBot', 
                          backref=db.backref('exchange', lazy=True),
                          lazy='dynamic',
                          cascade='all, delete-orphan',
                          foreign_keys='TradingBot.exchange_id')
    trades = db.relationship('Trade', 
                           backref=db.backref('exchange', lazy=True),
                           lazy='dynamic',
                           foreign_keys='Trade.exchange_id')
    
    def validate_trading_params(self, order_size, leverage=1):
        """Valida los parámetros de trading"""
        if not self.trading_enabled:
            return False, "Trading no está habilitado para este exchange"
        if order_size < self.min_order_size:
            return False, f"Tamaño de orden menor al mínimo ({self.min_order_size} {self.quote_currency})"
        if order_size > self.max_order_size:
            return False, f"Tamaño de orden mayor al máximo ({self.max_order_size} {self.quote_currency})"
        if leverage > self.max_leverage:
            return False, f"Apalancamiento mayor al máximo permitido ({self.max_leverage}x)"
        return True, None
