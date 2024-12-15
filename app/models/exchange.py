from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Exchange(db.Model):
    __tablename__ = 'exchange'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    exchange_type = db.Column(db.String(20), nullable=False)  # 'binance', 'bingx', 'oanda'
    api_key = db.Column(db.String(200))
    api_secret_hash = db.Column(db.String(256))
    account_id = db.Column(db.String(100))  # Para OANDA
    is_active = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    last_error = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __init__(self, **kwargs):
        self.api_secret = kwargs.pop('api_secret', None)
        super(Exchange, self).__init__(**kwargs)
        if self.api_secret:
            self.set_api_secret(self.api_secret)
    
    def set_api_secret(self, api_secret):
        self.api_secret_hash = generate_password_hash(api_secret)
    
    def check_api_secret(self, api_secret):
        return check_password_hash(self.api_secret_hash, api_secret)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'exchange_type': self.exchange_type,
            'is_active': self.is_active,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'last_error': self.last_error
        }
