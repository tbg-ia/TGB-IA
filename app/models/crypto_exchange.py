from app import db
from .base_exchange import BaseExchange

class CryptoExchange(BaseExchange):
    """Modelo específico para BingX"""
    __tablename__ = 'crypto_exchanges'
    
    id = db.Column(db.Integer, db.ForeignKey('exchanges.id'), primary_key=True)
    supports_spot = db.Column(db.Boolean, default=True)
    supports_futures = db.Column(db.Boolean, default=True)
    maker_fee = db.Column(db.Float, default=0.1)
    taker_fee = db.Column(db.Float, default=0.1)
    withdrawal_fee = db.Column(db.Float, default=0.0)
    trading_pairs = db.Column(db.JSON, default=list)
    
    __mapper_args__ = {
        'polymorphic_identity': 'crypto'
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'BINGX'
        self.exchange_type = 'bingx'
        self.quote_currency = 'USDT'
        self.min_order_size = 10.0
        self.max_order_size = 100000.0
        self.max_leverage = 50
        self.max_positions = 10
