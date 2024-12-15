from app import db
from app.models.crypto_exchange import CryptoExchange

class BinanceExchange(CryptoExchange):
    """Modelo específico para Binance"""
    __mapper_args__ = {
        'polymorphic_identity': 'binance'
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'Binance'
        self.trading_fee = 0.1  # Fee específico de Binance
