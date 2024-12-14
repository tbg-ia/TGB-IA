from app import db
from datetime import datetime

class TradingBot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100))
    exchange = db.Column(db.String(20), default='bingx')
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
    api_key = db.Column(db.String(64))  # Encrypted API key
    api_secret = db.Column(db.String(64))  # Encrypted API secret
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_trade = db.Column(db.DateTime)
    total_trades = db.Column(db.Integer, default=0)
    successful_trades = db.Column(db.Integer, default=0)
    current_profit = db.Column(db.Float, default=0.0)
    risk_level = db.Column(db.String(10), default='medium')  # low, medium, high
    max_daily_trades = db.Column(db.Integer, default=10)
    trailing_stop = db.Column(db.Float)  # Porcentaje de trailing stop

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bot_id = db.Column(db.Integer, db.ForeignKey('trading_bot.id'))
    type = db.Column(db.String(4))  # BUY/SELL
    price = db.Column(db.Float)
    amount = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
