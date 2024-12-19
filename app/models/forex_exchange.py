
from app import db
from .base_exchange import BaseExchange

class ForexExchange(BaseExchange):
    """Modelo para exchanges de Forex"""
    __tablename__ = 'forex_exchanges'
    
    id = db.Column(db.Integer, db.ForeignKey('exchanges.id', ondelete='CASCADE'), primary_key=True)
    margin_rate = db.Column(db.Float, default=0.02)
    position_size_decimals = db.Column(db.Integer, default=2)
    base_currency = db.Column(db.String(3), default='USD')
    quote_precision = db.Column(db.Integer, default=5)
    
    __mapper_args__ = {
        'polymorphic_identity': 'forex'
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.market_type = 'forex'
        self.min_order_size = 1000.0  # Estándar para forex
        self.max_order_size = 100000.0
        self.max_leverage = 50  # Típico en forex
