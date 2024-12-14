from app import db
from datetime import datetime

class TradingBot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    strategy = db.Column(db.String(50), nullable=False)
    active = db.Column(db.Boolean, default=False)
    trading_pair = db.Column(db.String(20), nullable=False)
    max_position = db.Column(db.Float, nullable=False)
    stop_loss = db.Column(db.Float)
    take_profit = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_trade = db.Column(db.DateTime)

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bot_id = db.Column(db.Integer, db.ForeignKey('trading_bot.id'))
    type = db.Column(db.String(4))  # BUY/SELL
    price = db.Column(db.Float)
    amount = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
