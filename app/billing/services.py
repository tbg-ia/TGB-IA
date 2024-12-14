from datetime import datetime, timedelta
from app import db
from .models import Payment, Subscription
from app.models.user import User

class SubscriptionService:
    @staticmethod
    def create_subscription(user_id: int, plan_type: str, duration_months: int = 1) -> Subscription:
        """Create a new subscription for a user"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Define plan prices
        plan_prices = {
            'basic': 0,
            'pro': 29.99,
            'enterprise': 99.99
        }
        
        subscription = Subscription(
            user_id=user_id,
            plan_type=plan_type,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30 * duration_months),
            price=plan_prices.get(plan_type, 0),
            status='active'
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        return subscription

    @staticmethod
    def cancel_subscription(subscription_id: int) -> bool:
        """Cancel an active subscription"""
        subscription = Subscription.query.get(subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")
        
        subscription.status = 'cancelled'
        db.session.commit()
        return True

class PaymentService:
    @staticmethod
    def create_payment(user_id: int, amount: float, payment_method: str) -> Payment:
        """Create a new payment record"""
        payment = Payment(
            user_id=user_id,
            amount=amount,
            payment_method=payment_method,
            status='pending'
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return payment

    @staticmethod
    def process_payment(payment_id: int) -> bool:
        """Process a pending payment"""
        payment = Payment.query.get(payment_id)
        if not payment:
            raise ValueError("Payment not found")
        
        # TODO: Implement payment gateway integration
        payment.status = 'completed'
        db.session.commit()
        return True
