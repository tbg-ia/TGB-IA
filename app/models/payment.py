"""
Payment model for tracking subscription payments.
"""
from datetime import datetime
from app import db
from app.models.subscription import Subscription

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    transaction_id = db.Column(db.String(255))
    invoice_id = db.Column(db.String(255))
    invoice_url = db.Column(db.String(500))
    pdf_url = db.Column(db.String(500))
    description = db.Column(db.String(500))
    is_trial = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con la suscripción
    subscription = db.relationship('Subscription', 
                                 backref=db.backref('payments', 
                                                  lazy=True,
                                                  cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<Payment {self.id} - Amount: ${self.amount} - Status: {self.status}>'
