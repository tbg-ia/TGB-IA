import logging
from datetime import datetime, timedelta
from app import db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.payment import Payment

def handle_subscription_created(subscription_object):
    """Handle when a new subscription is created"""
    try:
        user_id = int(subscription_object.metadata.get('user_id'))
        user = User.query.get(user_id)
        if not user:
            logging.error(f"User {user_id} not found for subscription {subscription_object.id}")
            return

        # Create or update subscription
        subscription = Subscription.query.filter_by(
            user_id=user_id,
            stripe_subscription_id=subscription_object.id
        ).first() or Subscription(
            user_id=user_id,
            stripe_subscription_id=subscription_object.id
        )

        subscription.status = subscription_object.status
        subscription.plan_type = subscription_object.metadata.get('plan_type', 'basic')
        subscription.start_date = datetime.fromtimestamp(subscription_object.current_period_start)
        subscription.end_date = datetime.fromtimestamp(subscription_object.current_period_end)
        subscription.amount = subscription_object.items.data[0].price.unit_amount

        user.subscription_type = subscription.plan_type
        
        db.session.add(subscription)
        db.session.commit()
        
        logging.info(f"Subscription created for user {user_id}")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error handling subscription creation: {str(e)}")

def handle_subscription_updated(subscription_object):
    """Handle when a subscription is updated"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_object.id
        ).first()
        
        if not subscription:
            logging.error(f"Subscription {subscription_object.id} not found")
            return
            
        subscription.status = subscription_object.status
        subscription.end_date = datetime.fromtimestamp(subscription_object.current_period_end)
        subscription.amount = subscription_object.items.data[0].price.unit_amount
        
        db.session.commit()
        logging.info(f"Subscription {subscription_object.id} updated")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error handling subscription update: {str(e)}")

def handle_subscription_deleted(subscription_object):
    """Handle when a subscription is cancelled/deleted"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_object.id
        ).first()
        
        if subscription:
            subscription.status = 'cancelled'
            subscription.user.subscription_type = 'basic'
            db.session.commit()
            logging.info(f"Subscription {subscription_object.id} marked as cancelled")
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error handling subscription deletion: {str(e)}")

def handle_invoice_paid(invoice_object):
    """Handle when an invoice is paid"""
    try:
        subscription_id = invoice_object.subscription
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if not subscription:
            logging.error(f"Subscription {subscription_id} not found for invoice {invoice_object.id}")
            return
            
        # Register payment
        payment = Payment(
            user_id=subscription.user_id,
            subscription_id=subscription.id,
            amount=invoice_object.amount_paid,
            status='completed',
            payment_method='stripe',
            stripe_payment_id=invoice_object.payment_intent
        )
        
        db.session.add(payment)
        db.session.commit()
        logging.info(f"Payment recorded for invoice {invoice_object.id}")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error handling invoice payment: {str(e)}")

def handle_invoice_payment_failed(invoice_object):
    """Handle when an invoice payment fails"""
    try:
        subscription_id = invoice_object.subscription
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription:
            # Register failed payment
            payment = Payment(
                user_id=subscription.user_id,
                subscription_id=subscription.id,
                amount=invoice_object.amount_due,
                status='failed',
                payment_method='stripe',
                stripe_payment_id=invoice_object.payment_intent
            )
            
            db.session.add(payment)
            db.session.commit()
            logging.info(f"Failed payment recorded for invoice {invoice_object.id}")
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error handling failed invoice payment: {str(e)}")

def handle_subscription_trial_will_end(subscription_object):
    """Handle when a subscription trial is about to end"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_object.id
        ).first()
        
        if subscription:
            # Could implement notification logic here
            logging.info(f"Trial ending soon for subscription {subscription_object.id}")
            
    except Exception as e:
        logging.error(f"Error handling trial end notification: {str(e)}")

def handle_subscription_update_applied(subscription_object):
    """Handle when a subscription update is applied"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_object.id
        ).first()
        
        if subscription:
            subscription.status = subscription_object.status
            subscription.end_date = datetime.fromtimestamp(subscription_object.current_period_end)
            db.session.commit()
            logging.info(f"Update applied to subscription {subscription_object.id}")
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error handling subscription update application: {str(e)}")

def handle_subscription_update_expired(subscription_object):
    """Handle when a subscription update expires"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_object.id
        ).first()
        
        if subscription:
            # Could implement notification logic here
            logging.info(f"Update expired for subscription {subscription_object.id}")
            
    except Exception as e:
        logging.error(f"Error handling subscription update expiration: {str(e)}")
