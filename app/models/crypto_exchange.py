from app import db
from .base_exchange import BaseExchange

class CryptoExchange(BaseExchange):
    """Modelo base para exchanges de criptomonedas"""
    __tablename__ = 'crypto_exchanges'
    
    id = db.Column(db.Integer, db.ForeignKey('base_exchanges.id'), primary_key=True)
    max_positions = db.Column(db.Integer, default=5)
    max_leverage = db.Column(db.Integer, default=20)
    quote_currency = db.Column(db.String(10), default='USDT')
    min_order_size = db.Column(db.Float, default=10.0)
    max_order_size = db.Column(db.Float, default=1000.0)
    trading_fee = db.Column(db.Float, default=0.1)
    supports_spot = db.Column(db.Boolean, default=True)
    supports_margin = db.Column(db.Boolean, default=False)
    supports_futures = db.Column(db.Boolean, default=False)
    supports_options = db.Column(db.Boolean, default=False)
    min_leverage = db.Column(db.Integer, default=1)
    maker_fee = db.Column(db.Float, default=0.1)
    taker_fee = db.Column(db.Float, default=0.1)
    withdrawal_fee = db.Column(db.Float, default=0.0)
    requires_kyc = db.Column(db.Boolean, default=False)
    supported_countries = db.Column(db.JSON, default=list)
    trading_pairs = db.Column(db.JSON, default=dict)
    
    __mapper_args__ = {
        'polymorphic_identity': 'crypto'
    }
    
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
