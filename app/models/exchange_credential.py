from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class ExchangeCredential(db.Model):
    """Modelo para almacenar credenciales de exchanges por usuario"""
    __tablename__ = 'exchange_credentials'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exchange_id = db.Column(db.Integer, db.ForeignKey('exchanges.id'), nullable=False)
    api_key = db.Column(db.String(255))
    api_secret_hash = db.Column(db.String(255))
    account_id = db.Column(db.String(100))  # Para exchanges como OANDA
    is_active = db.Column(db.Boolean, default=True)
    last_used = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    last_error = db.Column(db.String(500))
    
    def set_api_secret(self, secret):
        """Almacena el API secret de forma segura"""
        try:
            self.api_secret_hash = generate_password_hash(secret)
            return True, None
        except Exception as e:
            return False, str(e)
            
    def verify_api_secret(self, secret):
        """Verifica si el API secret proporcionado coincide con el almacenado"""
        try:
            return check_password_hash(self.api_secret_hash, secret)
        except Exception:
            return False
            
    def to_dict(self, include_secrets=False):
        data = {
            'id': self.id,
            'exchange_id': self.exchange_id,
            'is_active': self.is_active,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat()
        }
        
        if include_secrets:
            data.update({
                'api_key': self.api_key,
                'account_id': self.account_id
            })
            
        return data
