from app import db
from .base_exchange import BaseExchange

class ForexExchange(BaseExchange):
    """Modelo específico para OANDA"""
    __tablename__ = 'forex_exchanges'
    
    id = db.Column(db.Integer, db.ForeignKey('exchanges.id'), primary_key=True)
    account_id = db.Column(db.String(100), nullable=False)
    base_currency = db.Column(db.String(3), default='USD')
    margin_rate = db.Column(db.Float, default=0.02)
    position_size_decimals = db.Column(db.Integer, default=2)
    available_instruments = db.Column(db.JSON, default=list)
    
    __mapper_args__ = {
        'polymorphic_identity': 'forex'
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'OANDA'
        self.exchange_type = 'oanda'
        self.quote_currency = 'USD'
        self.min_order_size = 1000.0  # 1k unidades mínimo
        self.max_order_size = 100000.0  # 100k unidades máximo
        self.max_leverage = 30
        self.max_positions = 10
    
    def validate_trade_size(self, size):
        """Valida el tamaño del trade específico para OANDA"""
        if size < self.min_order_size:
            return False, f"Tamaño menor al mínimo permitido ({self.min_order_size} unidades)"
        if size > self.max_order_size:
            return False, f"Tamaño mayor al máximo permitido ({self.max_order_size} unidades)"
        return True, None
