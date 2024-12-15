from app import db
from datetime import datetime

class TradingBot(db.Model):
    __tablename__ = 'trading_bot'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exchange_id = db.Column(db.Integer, db.ForeignKey('exchange.id'), nullable=False)
    name = db.Column(db.String(100))
    strategy = db.Column(db.String(50), nullable=False)
    active = db.Column(db.Boolean, default=False)
    trading_pair = db.Column(db.String(20), nullable=False)
    interval = db.Column(db.String(3), default='1h')  # Timeframe: 1m, 5m, 15m, 1h, etc
    max_position = db.Column(db.Float, nullable=False)
    stop_loss = db.Column(db.Float)
    take_profit = db.Column(db.Float)
    leverage = db.Column(db.Integer, default=1)
    margin_type = db.Column(db.String(10), default='isolated')  # isolated or cross
    position_mode = db.Column(db.String(10), default='one_way')  # one_way or hedge
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_trade = db.Column(db.DateTime)
    total_trades = db.Column(db.Integer, default=0)
    successful_trades = db.Column(db.Integer, default=0)
    current_profit = db.Column(db.Float, default=0.0)
    risk_level = db.Column(db.String(10), default='medium')  # low, medium, high
    max_daily_trades = db.Column(db.Integer, default=10)
    trailing_stop = db.Column(db.Float)  # Porcentaje de trailing stop

    # Relaciones
    trades = db.relationship('Trade', backref='bot', lazy='dynamic')
    
    def __repr__(self):
        return f'<TradingBot {self.name}>'
        
    def to_dict(self):
        """Convierte el bot a diccionario para API/JSON"""
        return {
            'id': self.id,
            'name': self.name,
            'strategy': self.strategy,
            'active': self.active,
            'trading_pair': self.trading_pair,
            'interval': self.interval,
            'max_position': self.max_position,
            'leverage': self.leverage,
            'margin_type': self.margin_type,
            'position_mode': self.position_mode,
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'current_profit': self.current_profit,
            'risk_level': self.risk_level
        }
