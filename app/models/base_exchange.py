
from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash

class BaseExchange(db.Model):
    """Modelo base para exchanges de trading"""
    __tablename__ = 'exchanges'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))  # Discriminador para herencia
    name = db.Column(db.String(50), nullable=False)
    exchange_type = db.Column(db.String(20), nullable=False)  # 'bingx' o 'oanda'
    api_key = db.Column(db.String(255))
    api_secret_hash = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    trading_enabled = db.Column(db.Boolean, default=False)
    max_positions = db.Column(db.Integer, default=5)
    max_leverage = db.Column(db.Integer, default=20)
    quote_currency = db.Column(db.String(10), default='USDT')
    min_order_size = db.Column(db.Float, default=10.0)
    max_order_size = db.Column(db.Float, default=1000.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    last_error = db.Column(db.String(500))

    __mapper_args__ = {
        'polymorphic_identity': 'base',
        'polymorphic_on': type
    }

    def set_api_secret(self, secret):
        """Almacena el API secret de forma segura"""
        try:
            self.api_secret_hash = generate_password_hash(secret)
            return True, None
        except Exception as e:
            return False, str(e)
            
    def validate_credentials(self):
        """Valida las credenciales con el exchange"""
        raise NotImplementedError

    def validate_trading_params(self, order_size, leverage=1):
        """Valida los parámetros básicos de trading"""
        if not self.trading_enabled:
            return False, "Trading no está habilitado"
        if order_size < self.min_order_size:
            return False, f"Tamaño menor al mínimo ({self.min_order_size})"
        if order_size > self.max_order_size:
            return False, f"Tamaño mayor al máximo ({self.max_order_size})"
        if leverage > self.max_leverage:
            return False, f"Apalancamiento mayor al permitido ({self.max_leverage}x)"
        return True, None
