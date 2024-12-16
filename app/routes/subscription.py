"""
Subscription management routes and webhook handlers for Stripe integration.
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, url_for, redirect, flash, current_app
from flask_login import login_required, current_user
import stripe
from app import db
from app.models.subscription import Subscription
from app.models.payment import Payment
from app.models.user import User
from app.models.subscription_plan import SubscriptionPlan # Added import for SubscriptionPlan
import os # Added import for os


subscription_bp = Blueprint('subscription', __name__)

def get_plan_details(plan_id):
    """Retrieves plan details from the database based on plan_id."""
    try:
        plan = SubscriptionPlan.query.get(plan_id)
        if plan:
            return {
                'stripe_price_id': plan.stripe_price_id, #Assumed this exists in the model
                'name': plan.name
            }
        return None
    except Exception as e:
        logging.error(f"Error retrieving plan details: {str(e)}")
        return None


@subscription_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create a new checkout session for subscription"""
    try:
        plan_id = request.form.get('plan_id')
        if not plan_id:
            flash('Plan no especificado', 'error')
            return redirect(url_for('subscription.plans'))

        # Obtener detalles del plan
        plan = get_plan_details(plan_id)
        if not plan:
            flash('Plan no encontrado', 'error')
            return redirect(url_for('subscription.plans'))

        # Configurar los parámetros de checkout
        checkout_params = {
            'customer': current_user.stripe_customer_id,
            'customer_email': None if current_user.stripe_customer_id else current_user.email,
            'payment_method_types': ['card'],
            'line_items': [{
                'price': plan['stripe_price_id'],  # Usar el price ID predefinido de Stripe
                'quantity': 1
            }],
            'mode': 'subscription',
            'success_url': url_for('subscription.payment_success', _external=True),
            'cancel_url': url_for('subscription.payment_cancel', _external=True),
            'metadata': {
                'user_id': current_user.id,
                'plan_id': plan_id,
                'plan_name': plan['name']
            },
            'subscription_data': {
                'trial_period_days': 7,  # Período de prueba gratuito de 7 días
                'metadata': {
                    'plan_type': plan_id.split('_')[0]  # basic, pro, o enterprise
                }
            },
            'allow_promotion_codes': True,
            'billing_address_collection': 'required',
            'client_reference_id': str(current_user.id)
        }
        
        # Si es un upgrade, configurar el prorate
        if current_user.subscription:
            checkout_params['subscription_data']['transfer_data'] = {
                'destination': current_user.subscription.stripe_subscription_id,
                'amount_percent': 100
            }

        # Crear sesión de checkout y redireccionar
        try:
            checkout_session = stripe.checkout.Session.create(**checkout_params)
            return redirect(checkout_session.url)
        except Exception as e:
            logging.error(f"Error creating checkout session: {str(e)}")
            flash('Error al crear la sesión de checkout', 'error')
            return redirect(url_for('subscription.plans'))
        
    except stripe.error.StripeError as e:
        flash(f'Error al procesar el pago: {str(e)}', 'error')
        return redirect(url_for('subscription.plans'))
    except Exception as e:
        logging.error(f"Error inesperado: {str(e)}")
        flash('Error inesperado', 'error')
        return redirect(url_for('subscription.plans'))

@subscription_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhooks"""
    try:
        event = None
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, current_app.config['STRIPE_WEBHOOK_SECRET']
            )
        except ValueError as e:
            logging.error(f"Invalid payload: {str(e)}")
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError as e:
            logging.error(f"Invalid signature: {str(e)}")
            return jsonify({'error': 'Invalid signature'}), 400

        # Definir manejadores de eventos
        event_handlers = {
            'customer.subscription.created': handle_subscription_created,
            'customer.subscription.updated': handle_subscription_updated,
            'customer.subscription.deleted': handle_subscription_deleted,
            'invoice.paid': handle_invoice_paid,
            'invoice.payment_failed': handle_invoice_payment_failed,
            'customer.subscription.trial_will_end': handle_subscription_trial_will_end,
            'customer.subscription.pending_update_applied': handle_subscription_update_applied,
            'customer.subscription.pending_update_expired': handle_subscription_update_expired
        }

        # Registrar el tipo de evento
        current_app.logger.info(f"Webhook event received: {event['type']}")

        # Procesar el evento
        handler = event_handlers.get(event['type'])
        if handler:
            try:
                handler(event['data']['object'])
                return jsonify({'success': True}), 200
            except Exception as e:
                current_app.logger.error(f"Error processing webhook {event['type']}: {str(e)}")
                return jsonify({'error': str(e)}), 500
        else:
            current_app.logger.warning(f"Unhandled webhook event type: {event['type']}")
            return jsonify({'message': 'Unhandled event type'}), 200

    except Exception as e:
        logging.error(f"Error procesando webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

def handle_subscription_created(subscription_object):
    """Maneja la creación de una nueva suscripción"""
    try:
        # Crear nueva suscripción en la base de datos
        user = User.query.get(subscription_object.metadata.get('user_id'))
        if not user:
            logging.error(f"Usuario no encontrado: {subscription_object.metadata.get('user_id')}")
            return

        subscription = Subscription(
            user_id=user.id,
            stripe_subscription_id=subscription_object.id,
            plan_type=subscription_object.metadata.get('plan_type', 'basic'),
            status='active',
            trial_end=datetime.fromtimestamp(subscription_object.trial_end) if subscription_object.trial_end else None
        )

        db.session.add(subscription)
        db.session.commit()

    except Exception as e:
        logging.error(f"Error en handle_subscription_created: {str(e)}")
        db.session.rollback()

def handle_subscription_updated(subscription_object):
    """Maneja la actualización de una suscripción existente"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_object.id
        ).first()

        if not subscription:
            logging.error(f"Suscripción no encontrada: {subscription_object.id}")
            return

        # Actualizar estado y tipo de plan
        subscription.status = subscription_object.status
        subscription.plan_type = subscription_object.metadata.get('plan_type', subscription.plan_type)
        
        db.session.commit()

    except Exception as e:
        logging.error(f"Error en handle_subscription_updated: {str(e)}")
        db.session.rollback()

def handle_subscription_deleted(subscription_object):
    """Maneja la eliminación/cancelación de una suscripción"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_object.id
        ).first()

        if not subscription:
            logging.error(f"Suscripción no encontrada: {subscription_object.id}")
            return

        subscription.status = 'cancelled'
        subscription.end_date = datetime.fromtimestamp(subscription_object.canceled_at)
        
        # Revocar accesos
        subscription.user.subscription_type = None
        subscription.user.has_active_subscription = False
        
        db.session.commit()

    except Exception as e:
        logging.error(f"Error en handle_subscription_deleted: {str(e)}")
        db.session.rollback()

def handle_subscription_trial_will_end(subscription_object):
    """Maneja la notificación de que el período de prueba está por terminar"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_object.id
        ).first()
        
        if not subscription:
            logging.error(f"Suscripción no encontrada: {subscription_object.id}")
            return
            
        # Notificar al usuario
        from app.email.utils import send_trial_ending_email
        send_trial_ending_email(subscription.user)
        
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error en handle_subscription_trial_will_end: {str(e)}")
        db.session.rollback()

def handle_subscription_update_applied(subscription_object):
    """Maneja la aplicación de una actualización pendiente de suscripción"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_object.id
        ).first()
        
        if not subscription:
            logging.error(f"Suscripción no encontrada: {subscription_object.id}")
            return
            
        # Actualizar el plan
        new_plan = subscription_object.items.data[0].price.product
        subscription.plan_type = new_plan
        subscription.user.subscription_type = new_plan
        
        # Notificar al usuario
        from app.email.utils import send_plan_update_success_email
        send_plan_update_success_email(subscription.user, new_plan)
        
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error en handle_subscription_update_applied: {str(e)}")
        db.session.rollback()

def handle_subscription_update_expired(subscription_object):
    """Maneja la expiración de una actualización pendiente de suscripción"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_object.id
        ).first()
        
        if not subscription:
            logging.error(f"Suscripción no encontrada: {subscription_object.id}")
            return
            
        # Notificar al usuario
        from app.email.utils import send_plan_update_expired_email
        send_plan_update_expired_email(subscription.user)
        
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error en handle_subscription_update_expired: {str(e)}")
        db.session.rollback()

def handle_invoice_paid(invoice):
    """Maneja el pago exitoso de una factura"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=invoice.subscription
        ).first()
        
        if not subscription:
            logging.error(f"Suscripción no encontrada: {invoice.subscription}")
            return
            
        # Obtener la URL del PDF de la factura
        invoice_obj = stripe.Invoice.retrieve(invoice.id)
        
        # Registrar el pago
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
            is_trial=subscription.trial_end and datetime.fromtimestamp(invoice.created) <= subscription.trial_end
        )
        
        db.session.add(payment)
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error en handle_invoice_paid: {str(e)}")
        db.session.rollback()

def handle_invoice_payment_failed(invoice):
    """Maneja el fallo en el pago de una factura"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=invoice.subscription
        ).first()
        
        if not subscription:
            logging.error(f"Suscripción no encontrada: {invoice.subscription}")
            return
            
        # Registrar el intento fallido
        payment = Payment(
            subscription_id=subscription.id,
            amount=invoice.amount_due / 100,
            status='failed',
            payment_method='stripe',
            transaction_id=invoice.payment_intent
        )
        
        db.session.add(payment)
        
        # Si es el último intento, marcar como inactiva
        if invoice.next_payment_attempt is None:
            subscription.status = 'inactive'
            subscription.user.subscription_type = 'basic'
        
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error en handle_invoice_payment_failed: {str(e)}")
        db.session.rollback()



@subscription_bp.route('/payment/success')
@login_required
def payment_success():
    """Maneja el éxito del pago"""
    flash('¡Gracias por tu suscripción! Tu plan ha sido activado.', 'success')
    return redirect(url_for('user.dashboard'))

@subscription_bp.route('/payment/cancel')
@login_required
def payment_cancel():
    """Maneja la cancelación del pago"""
    flash('El proceso de pago fue cancelado.', 'info')
    return redirect(url_for('subscription.plans'))

# The rest of the original file's content related to plans and other routes should be integrated here.  This is omitted due to lack of information in the provided edit and to avoid introducing unintended changes.  A complete integration would require the full original file contents.