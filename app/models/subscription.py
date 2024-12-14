from app import db
from datetime import datetime

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
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

    def __repr__(self):
        return f'<Subscription {self.plan_type} for user {self.user_id}>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # success, failed, pending
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    subscription = db.relationship('Subscription', backref=db.backref('payments', lazy=True))
