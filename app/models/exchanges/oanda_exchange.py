from app import db
from app.models.forex_exchange import ForexExchange

class OandaExchange(ForexExchange):
    """Modelo específico para OANDA"""
    __mapper_args__ = {
        'polymorphic_identity': 'oanda'
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'OANDA'
        self.margin_rate = 0.02  # Margen específico de OANDA
        self.max_leverage = 30  # Leverage máximo de OANDA
