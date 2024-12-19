
from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class BaseExchange(db.Model):
    __tablename__ = 'exchanges'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    exchange_type = db.Column(db.String(20), nullable=False)
    api_key = db.Column(db.String(255))
    api_secret_hash = db.Column(db.String(255))
    account_id = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    trading_enabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    __mapper_args__ = {
        'polymorphic_identity': 'base',
        'polymorphic_on': exchange_type
    }

    def set_api_secret(self, secret):
        try:
            self.api_secret_hash = generate_password_hash(secret)
            return True, None
        except Exception as e:
            return False, str(e)
            
    def check_api_secret(self, secret):
        return check_password_hash(self.api_secret_hash, secret)
            
    def validate_credentials(self):
        """Método para validar credenciales con el exchange"""
        return True, None
