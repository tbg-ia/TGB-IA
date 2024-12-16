from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logger = logging.getLogger(__name__)

class BaseExchange(db.Model):
    """Modelo base para todos los exchanges"""
    __tablename__ = 'base_exchanges'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    exchange_type = db.Column(db.String(20), nullable=False)
    api_key = db.Column(db.String(200))
    api_secret_hash = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=False)
    is_testnet = db.Column(db.Boolean, default=False)
    trading_enabled = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    last_error = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    connection_status = db.Column(db.String(20), default='disconnected')  # disconnected, connected, error
    last_connection_check = db.Column(db.DateTime)
    api_permissions = db.Column(db.JSON, default=dict)  # Almacena los permisos de la API
    
    __mapper_args__ = {
        'polymorphic_identity': 'base',
        'polymorphic_on': exchange_type
    }
    
    def set_api_secret(self, api_secret):
        """Almacena el API secret de forma segura"""
        try:
            if not api_secret:
                raise ValueError("API Secret no puede estar vacío")
            self.api_secret_hash = generate_password_hash(api_secret)
            self.last_updated = datetime.utcnow()
            return True, None
        except Exception as e:
            logger.error(f"Error al configurar API secret: {str(e)}")
            return False, str(e)
    
    def check_api_secret(self, api_secret):
        """Verifica el API secret"""
        try:
            if not self.api_secret_hash:
                return False
            return check_password_hash(self.api_secret_hash, api_secret)
        except Exception as e:
            logger.error(f"Error al verificar API secret: {str(e)}")
            return False
            
    def validate_credentials(self):
        """Valida que las credenciales estén completas"""
        if not self.api_key:
            return False, "API Key es requerida"
        if not self.api_secret_hash:
            return False, "API Secret es requerido"
        return True, None
        
    def update_connection_status(self, status, error=None):
        """Actualiza el estado de conexión"""
        self.connection_status = status
        self.last_connection_check = datetime.utcnow()
        if error:
            self.last_error = str(error)
        
    def to_dict(self):
        """Convierte el exchange a diccionario para API/JSON"""
        return {
            'id': self.id,
            'name': self.name,
            'exchange_type': self.exchange_type,
            'is_active': self.is_active,
            'is_testnet': self.is_testnet,
            'trading_enabled': self.trading_enabled,
            'connection_status': self.connection_status,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'last_error': self.last_error,
            'api_permissions': self.api_permissions
        }
