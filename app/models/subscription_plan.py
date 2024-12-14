from app import db
from datetime import datetime

class SubscriptionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'basic', 'pro', 'enterprise'
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    features = db.Column(db.JSON)
    stripe_price_id = db.Column(db.String(100), unique=True)
    is_active = db.Column(db.Boolean, default=True)
    trial_days = db.Column(db.Integer, default=7)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<SubscriptionPlan {self.name}>'

    @staticmethod
    def get_active_plans():
        return SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.price).all()
