from app import db
from datetime import datetime

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_type = db.Column(db.String(20), nullable=False)  # 'basic', 'pro', or 'enterprise'
    status = db.Column(db.String(20), nullable=False, default='active')  # active, cancelled, expired, inactive
    amount = db.Column(db.Float, nullable=False)
    stripe_subscription_id = db.Column(db.String(100), unique=True, nullable=True)
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    trial_end = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('subscriptions', lazy=True))
    payments = db.relationship('Payment', backref='subscription', lazy=True)

    def __repr__(self):
        return f'<Subscription {self.plan_type} for user {self.user_id}>'

# Payment model moved to app/models/payment.py
