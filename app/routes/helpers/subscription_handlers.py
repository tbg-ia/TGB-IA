import logging
from datetime import datetime
from app import db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.payment import Payment
import stripe

def handle_subscription_created(subscription_object):
    try:
        user_id = subscription_object.metadata.get('user_id')
        if not user_id:
            logging.error("No se recibió user_id en la metadata.")
            return

        user = User.query.get(user_id)
        if not user:
            logging.error(f"Usuario no encontrado: {user_id}")
            return

        subscription = Subscription(
            user_id=user.id,
            stripe_subscription_id=subscription_object.id,
            plan_type=subscription_object.metadata.get('plan_type', 'basic'),
            status='active',
            trial_end=(datetime.fromtimestamp(subscription_object.trial_end) if subscription_object.trial_end else None)
        )
        db.session.add(subscription)
        db.session.commit()
    except Exception as e:
        logging.error(f"Error en handle_subscription_created: {str(e)}")
        db.session.rollback()

def handle_subscription_updated(subscription_object):
    try:
        subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_object.id).first()
        if not subscription:
            logging.error(f"Suscripción no encontrada: {subscription_object.id}")
            return

        subscription.status = subscription_object.status
        subscription.plan_type = subscription_object.metadata.get('plan_type', subscription.plan_type)
        db.session.commit()

    except Exception as e:
        logging.error(f"Error en handle_subscription_updated: {str(e)}")
        db.session.rollback()

def handle_subscription_deleted(subscription_object):
    try:
        subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_object.id).first()
        if not subscription:
            logging.error(f"Suscripción no encontrada: {subscription_object.id}")
            return

        subscription.status = 'cancelled'
        subscription.end_date = datetime.fromtimestamp(subscription_object.canceled_at)
        subscription.user.subscription_type = None
        subscription.user.has_active_subscription = False
        db.session.commit()

    except Exception as e:
        logging.error(f"Error en handle_subscription_deleted: {str(e)}")
        db.session.rollback()

def handle_subscription_trial_will_end(subscription_object):
    try:
        subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_object.id).first()
        if not subscription:
            logging.error(f"Suscripción no encontrada: {subscription_object.id}")
            return
        # Notificar al usuario que el trial terminará pronto.
        db.session.commit()
    except Exception as e:
        logging.error(f"Error en handle_subscription_trial_will_end: {str(e)}")
        db.session.rollback()

def handle_subscription_update_applied(subscription_object):
    try:
        subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_object.id).first()
        if not subscription:
            logging.error(f"Suscripción no encontrada: {subscription_object.id}")
            return

        new_plan = subscription_object.items.data[0].price.product
        subscription.plan_type = new_plan
        subscription.user.subscription_type = new_plan
        db.session.commit()
    except Exception as e:
        logging.error(f"Error en handle_subscription_update_applied: {str(e)}")
        db.session.rollback()

def handle_subscription_update_expired(subscription_object):
    try:
        subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_object.id).first()
        if not subscription:
            logging.error(f"Suscripción no encontrada: {subscription_object.id}")
            return
        # Notificar expiración de la actualización pendiente
        db.session.commit()
    except Exception as e:
        logging.error(f"Error en handle_subscription_update_expired: {str(e)}")
        db.session.rollback()

def handle_invoice_paid(invoice):
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=invoice.subscription
        ).first()

        if not subscription:
            logging.error(f"Suscripción no encontrada: {invoice.subscription}")
            return

        invoice_obj = stripe.Invoice.retrieve(invoice.id)

        payment = Payment(
            subscription_id=subscription.id,
            amount=invoice.amount_paid / 100,
            status='success',
            payment_method='stripe',
            transaction_id=invoice.payment_intent,
            invoice_id=invoice.id,
            invoice_url=invoice.hosted_invoice_url,
            pdf_url=invoice_obj.invoice_pdf,
            description=f"Plan {subscription.plan_type.title()} - Pago mensual",
            is_trial=(subscription.trial_end and datetime.fromtimestamp(invoice.created) <= subscription.trial_end)
        )

        db.session.add(payment)
        db.session.commit()
    except Exception as e:
        logging.error(f"Error en handle_invoice_paid: {str(e)}")
        db.session.rollback()

def handle_invoice_payment_failed(invoice):
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=invoice.subscription
        ).first()

        if not subscription:
            logging.error(f"Suscripción no encontrada: {invoice.subscription}")
            return

        payment = Payment(
            subscription_id=subscription.id,
            amount=invoice.amount_due / 100,
            status='failed',
            payment_method='stripe',
            transaction_id=invoice.payment_intent
        )

        db.session.add(payment)

        if invoice.next_payment_attempt is None:
            subscription.status = 'inactive'
            subscription.user.subscription_type = 'basic'

        db.session.commit()
    except Exception as e:
        logging.error(f"Error en handle_invoice_payment_failed: {str(e)}")
        db.session.rollback()
