from app import db
from datetime import datetime

class ExchangeSettings(db.Model):
    """Modelo para configuraciones específicas de exchange por usuario"""
    __tablename__ = 'exchange_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exchange_id = db.Column(db.Integer, db.ForeignKey('exchanges.id'), nullable=False)
    
    # Configuraciones de trading
    trading_enabled = db.Column(db.Boolean, default=False)
    max_positions = db.Column(db.Integer, default=5)
    max_leverage = db.Column(db.Integer, default=20)
    quote_currency = db.Column(db.String(10), default='USDT')
    min_order_size = db.Column(db.Float, default=10.0)
    max_order_size = db.Column(db.Float, default=1000.0)
    
    # Timestamps y estado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'trading_enabled': self.trading_enabled,
            'max_positions': self.max_positions,
            'max_leverage': self.max_leverage,
            'quote_currency': self.quote_currency,
            'min_order_size': self.min_order_size,
            'max_order_size': self.max_order_size,
            'last_updated': self.last_updated.isoformat()
        }
