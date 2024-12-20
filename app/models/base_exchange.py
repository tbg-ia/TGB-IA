
from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash
import logging

logger = logging.getLogger(__name__)

class BaseExchange(db.Model):
    """Modelo base para exchanges de trading"""
    __tablename__ = 'exchanges'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exchange_type = db.Column(db.String(50), nullable=False)  # 'binance', 'bingx', 'oanda'
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    is_enabled = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    requires_api_key = db.Column(db.Boolean, default=True)
    requires_api_secret = db.Column(db.Boolean, default=True)
    requires_account_id = db.Column(db.Boolean, default=False)
    supported_features = db.Column(db.JSON)
    account_id = db.Column(db.String(100))
    is_testnet = db.Column(db.Boolean, default=False)
    is_forex = db.Column(db.Boolean, default=False)
    trading_fee = db.Column(db.Float, default=0.0)
    last_error = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    credentials = db.relationship('ExchangeCredential', backref='exchange', lazy=True,
                                cascade='all, delete-orphan')
    settings = db.relationship('ExchangeSettings', backref='exchange', lazy=True,
                             cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Exchange {self.name}>'
        
    def to_dict(self):
        try:
            settings = self.settings[0] if self.settings else None
            return {
                'id': self.id,
                'name': self.name,
                'exchange_type': self.exchange_type,
                'description': self.description,
                'is_enabled': self.is_enabled,
                'is_active': self.is_active,
                'supported_features': self.supported_features,
                'account_id': self.account_id,
                'is_testnet': self.is_testnet,
                'trading_fee': self.trading_fee,
                'last_error': self.last_error,
                'last_updated': self.last_updated.isoformat() if self.last_updated else None,
                'settings': settings.to_dict() if settings else None
            }
        except Exception as e:
            logger.error(f"Error in to_dict: {str(e)}")
            return {
                'id': self.id,
                'name': self.name,
                'exchange_type': self.exchange_type,
                'is_active': self.is_active
            }

    # Columna discriminadora para herencia
    type = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'base',
        'polymorphic_on': type
    }

    def set_api_secret(self, secret):
        """Almacena el API secret de forma segura"""
        try:
            if not hasattr(self, 'credentials') or not self.credentials:
                return False, "No credentials found"
            credential = self.credentials[0]
            success, error = credential.set_api_secret(secret)
            return success, error
        except Exception as e:
            return False, str(e)
            
    def validate_credentials(self):
        """Valida las credenciales con el exchange"""
        try:
            if not self.credentials:
                return False, "No credentials configured"
            credential = self.credentials[0]
            if not credential.is_active:
                return False, "Credentials are not active"
            return True, None
        except Exception as e:
            return False, str(e)

    def validate_trading_params(self, order_size, leverage=1):
        """Valida los parámetros básicos de trading"""
        try:
            if not self.settings:
                return False, "No trading settings configured"
            settings = self.settings[0]
            if not settings.trading_enabled:
                return False, "Trading is not enabled"
            if order_size < settings.min_order_size:
                return False, f"Order size below minimum ({settings.min_order_size})"
            if order_size > settings.max_order_size:
                return False, f"Order size above maximum ({settings.max_order_size})"
            if leverage > settings.max_leverage:
                return False, f"Leverage above maximum ({settings.max_leverage}x)"
            return True, None
        except Exception as e:
            return False, str(e)
