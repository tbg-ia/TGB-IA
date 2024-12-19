
from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .base_exchange import BaseExchange

class Exchange(BaseExchange):
    """Model for managing exchange connections and credentials"""
    __tablename__ = 'exchanges_extended'
    
    id = db.Column(db.Integer, db.ForeignKey('exchanges.id'), primary_key=True)
    is_forex = db.Column(db.Boolean, default=False)  
    is_testnet = db.Column(db.Boolean, default=False)  
    quote_currency = db.Column(db.String(10), default='USDT')  
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
