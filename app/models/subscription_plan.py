from app import db
from datetime import datetime

class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, nullable=False)  # Price in cents
    interval = db.Column(db.String(20), nullable=False)  # 'month' or 'year'
    stripe_price_id = db.Column(db.String(100), unique=True)
    stripe_product_id = db.Column(db.String(100), unique=True)
    features = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'interval': self.interval,
            'features': self.features.split('\n') if self.features else [],
            'is_active': self.is_active,
            'stripe_price_id': self.stripe_price_id,
            'stripe_product_id': self.stripe_product_id
        }
