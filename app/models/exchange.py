from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
class Exchange(db.Model):
    """Model for managing exchange connections and credentials"""
    __tablename__ = 'exchanges'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    exchange_type = db.Column(db.String(20), nullable=False)  # 'binance', 'bingx', 'oanda'
    api_key = db.Column(db.String(200))
    api_secret_hash = db.Column(db.String(256))
    account_id = db.Column(db.String(100))  # Para OANDA
    is_active = db.Column(db.Boolean, default=False)
    is_testnet = db.Column(db.Boolean, default=False)  # Para distinguir entre mainnet/testnet
    trading_enabled = db.Column(db.Boolean, default=False)  # Para control de trading
    max_positions = db.Column(db.Integer, default=5)  # Número máximo de posiciones simultáneas
    max_leverage = db.Column(db.Integer, default=20)  # Apalancamiento máximo permitido
    quote_currency = db.Column(db.String(10), default='USDT')  # Moneda base para trading
    min_order_size = db.Column(db.Float, default=10.0)  # Tamaño mínimo de orden en quote_currency
    max_order_size = db.Column(db.Float, default=1000.0)  # Tamaño máximo de orden en quote_currency
    trading_fee = db.Column(db.Float, default=0.1)  # Comisión de trading en porcentaje
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    last_error = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relaciones
    bots = db.relationship('TradingBot', 
                          backref=db.backref('exchange', lazy=True),
                          lazy='dynamic',
                          cascade='all, delete-orphan',
                          foreign_keys='TradingBot.exchange_id')
    trades = db.relationship('Trade', 
                           backref=db.backref('exchange', lazy=True),
                           lazy='dynamic',
                           foreign_keys='Trade.exchange_id')
    
    def __init__(self, **kwargs):
        self.api_secret = kwargs.pop('api_secret', None)
        super(Exchange, self).__init__(**kwargs)
        if self.api_secret:
            self.set_api_secret(self.api_secret)
    
    def set_api_secret(self, api_secret):
        """Almacena el API secret de forma segura"""
        self.api_secret_hash = generate_password_hash(api_secret)
    
    def check_api_secret(self, api_secret):
        """Verifica el API secret"""
        return check_password_hash(self.api_secret_hash, api_secret)
    
    def to_dict(self):
        """Convierte el exchange a diccionario para API/JSON"""
        return {
            'id': self.id,
            'name': self.name,
            'exchange_type': self.exchange_type,
            'is_active': self.is_active,
            'is_testnet': self.is_testnet,
            'trading_enabled': self.trading_enabled,
            'max_positions': self.max_positions,
            'max_leverage': self.max_leverage,
            'quote_currency': self.quote_currency,
            'min_order_size': self.min_order_size,
            'max_order_size': self.max_order_size,
            'trading_fee': self.trading_fee,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'last_error': self.last_error
        }
    
    def validate_trading_params(self, order_size, leverage=1):
        """Valida los parámetros de trading"""
        if not self.trading_enabled:
            return False, "Trading no está habilitado para este exchange"
        if order_size < self.min_order_size:
            return False, f"Tamaño de orden menor al mínimo ({self.min_order_size} {self.quote_currency})"
        if order_size > self.max_order_size:
            return False, f"Tamaño de orden mayor al máximo ({self.max_order_size} {self.quote_currency})"
        if leverage > self.max_leverage:
            return False, f"Apalancamiento mayor al máximo permitido ({self.max_leverage}x)"
        return True, None
