
from app import db
from .base_exchange import BaseExchange

class ForexExchange(BaseExchange):
    """Modelo para exchanges de Forex"""
    __tablename__ = 'forex_exchanges'
    
    id = db.Column(db.Integer, db.ForeignKey('exchanges.id', ondelete='CASCADE'), primary_key=True)
    margin_rate = db.Column(db.Float, default=0.02)  # 2% margen por defecto
    max_leverage = db.Column(db.Integer, default=50)
    position_size_decimals = db.Column(db.Integer, default=2)
    min_trade_size = db.Column(db.Float, default=1000.0)  
    max_trade_size = db.Column(db.Float, default=100000.0)
    
    __mapper_args__ = {
        'polymorphic_identity': 'forex'
    }
    
    def validate_trade_size(self, size):
        """Valida el tamaño del trade para Forex"""
        if size < self.min_trade_size:
            return False, f"Tamaño menor al mínimo permitido ({self.min_trade_size})"
        if size > self.max_trade_size:
            return False, f"Tamaño mayor al máximo permitido ({self.max_trade_size})"
        return True, None
