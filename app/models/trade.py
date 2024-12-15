from app import db
from datetime import datetime

class Trade(db.Model):
    __tablename__ = 'trades'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)  # Par de trading (ej: BTC-USDT)
    side = db.Column(db.String(10), nullable=False)  # 'buy' o 'sell'
    order_type = db.Column(db.String(20), nullable=False)  # 'market', 'limit', etc.
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    leverage = db.Column(db.Integer, default=1)
    pnl = db.Column(db.Float)  # Profit/Loss en quote_currency
    pnl_percentage = db.Column(db.Float)  # Profit/Loss en porcentaje
    status = db.Column(db.String(20), default='open')  # 'open', 'closed', 'cancelled'
    close_price = db.Column(db.Float)
    close_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    exchange_id = db.Column(db.Integer, db.ForeignKey('exchanges.id'), nullable=False)
    bot_id = db.Column(db.Integer, db.ForeignKey('trading_bots.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def close_trade(self, close_price):
        """Cierra un trade y calcula el P&L"""
        if self.status != 'open':
            return False, "Trade ya está cerrado"
            
        self.close_price = close_price
        self.close_time = datetime.utcnow()
        self.status = 'closed'
        
        # Calcular P&L
        if self.side == 'buy':
            self.pnl = (close_price - self.price) * self.quantity * self.leverage
        else:
            self.pnl = (self.price - close_price) * self.quantity * self.leverage
            
        self.pnl_percentage = (self.pnl / (self.price * self.quantity)) * 100
        
        return True, None
        
    def to_dict(self):
        """Convierte el trade a diccionario para API/JSON"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side,
            'order_type': self.order_type,
            'quantity': self.quantity,
            'price': self.price,
            'leverage': self.leverage,
            'pnl': self.pnl,
            'pnl_percentage': self.pnl_percentage,
            'status': self.status,
            'close_price': self.close_price,
            'close_time': self.close_time.isoformat() if self.close_time else None,
            'created_at': self.created_at.isoformat(),
            'exchange_id': self.exchange_id,
            'bot_id': self.bot_id
        }
