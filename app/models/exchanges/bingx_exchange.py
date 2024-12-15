from app import db
from app.models.crypto_exchange import CryptoExchange

class BingXExchange(CryptoExchange):
    """Modelo específico para BingX"""
    __mapper_args__ = {
        'polymorphic_identity': 'bingx'
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'BingX'
        self.trading_fee = 0.075  # Fee específico de BingX
