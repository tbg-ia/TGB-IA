from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

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
    
    __mapper_args__ = {
        'polymorphic_identity': 'base',
        'polymorphic_on': exchange_type
    }
    
    def set_api_secret(self, api_secret):
        """Almacena el API secret de forma segura"""
        self.api_secret_hash = generate_password_hash(api_secret)
    
    def check_api_secret(self, api_secret):
        """Verifica el API secret"""
        return check_password_hash(self.api_secret_hash, api_secret)
