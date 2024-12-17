"""
Subscription management routes and webhook handlers for Stripe integration.
"""
import os
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request, url_for, redirect, flash, current_app
from flask_login import login_required, current_user
import stripe
from app import db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.payment import Payment
from app.models.subscription_plan import SubscriptionPlan

# Initialize blueprint with prefix
subscription_bp = Blueprint('subscription', __name__, url_prefix='/subscription')

def get_plan_details(plan_id):
    """Retrieves plan details from the database based on plan_id."""
    try:
        plan = SubscriptionPlan.query.get(plan_id)
        if plan:
            return {
                'stripe_price_id': plan.stripe_price_id,
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
            return redirect(url_for('subscription.planes'))

        # Obtener detalles del plan
        plan = get_plan_details(plan_id)
        if not plan:
            flash('Plan no encontrado', 'error')
            return redirect(url_for('subscription.planes'))

        # Verificar si el usuario ya tiene una suscripción activa
        existing_subscription = Subscription.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).first()

        # Configurar Stripe con la clave secreta
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

        # Configurar los parámetros de checkout
        # Verify stripe_price_id exists
        if not plan.get('stripe_price_id'):
            flash('Error: Plan no configurado correctamente', 'error')
            return redirect(url_for('subscription.planes'))
            
        checkout_params = {
            'payment_method_types': ['card'],
            'line_items': [{
                'price': plan['stripe_price_id'],
                'quantity': 1,
                'adjustable_quantity': {
                    'enabled': False
                }
            }],
            'mode': 'subscription',
            'success_url': url_for('subscription.payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            'cancel_url': url_for('subscription.payment_cancel', _external=True),
            'customer_email': current_user.email if not current_user.stripe_customer_id else None,
            'client_reference_id': str(current_user.id),
            'metadata': {
                'user_id': current_user.id,
                'plan_id': plan_id,
                'plan_name': plan['name']
            },
            'allow_promotion_codes': True,
            'billing_address_collection': 'required',
            'subscription_data': {
                'trial_period_days': 7,
                'metadata': {
                    'plan_type': plan['name'].lower()
                }
            }
        }

        # Si el usuario ya tiene un customer_id en Stripe, usarlo
        if current_user.stripe_customer_id:
            checkout_params['customer'] = current_user.stripe_customer_id
        
        # Si es un upgrade, configurar el prorate
        if current_user.subscription:
            checkout_params['subscription_data']['transfer_data'] = {
                'destination': current_user.subscription.stripe_subscription_id,
                'amount_percent': 100
            }

        # Crear sesión de checkout y redireccionar
        checkout_session = stripe.checkout.Session.create(**checkout_params)
        
        # Guardar la sesión de checkout en la base de datos
        try:
            subscription = Subscription(
                user_id=current_user.id,
                plan_type=plan['name'].lower(),
                status='pending',
                stripe_subscription_id=None,
                amount=plan.get('price', 0),
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(subscription)
            db.session.commit()
            
            return redirect(checkout_session.url, code=303)
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error saving subscription: {str(e)}")
            flash('Error al procesar la suscripción', 'error')
            return redirect(url_for('subscription.planes'))
            
    except stripe.error.StripeError as e:
        logging.error(f"Stripe error: {str(e)}")
        flash('Error al procesar el pago. Por favor, intente nuevamente.', 'error')
        return redirect(url_for('subscription.planes'))
        
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        flash('Ha ocurrido un error inesperado. Por favor, intente nuevamente.', 'error')
        return redirect(url_for('subscription.planes'))

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
            
        new_plan = subscription_object.items.data[0].price.product
        subscription.plan_type = new_plan
        subscription.user.subscription_type = new_plan
        
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
    return redirect(url_for('subscription.planes'))

@subscription_bp.route('/planes')
@login_required
def planes():
    """Muestra los planes de suscripción disponibles."""
    if not current_user.is_authenticated:
        flash('Por favor inicia sesión para ver los planes disponibles.', 'info')
        return redirect(url_for('auth.login'))

    logging.info(f"Accediendo a la página de planes. Usuario: {current_user.email}")
    try:
        subscription_plans = SubscriptionPlan.query.filter_by(is_active=True).all()
        logging.info(f"Planes encontrados: {len(subscription_plans)}")
        
        # Get current user's subscription if any
        current_subscription = Subscription.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).first()
        
        return render_template('subscription/plans.html', 
                             subscription_plans=subscription_plans,
                             current_user=current_user,
                             current_subscription=current_subscription)
    except Exception as e:
        logging.error(f"Error al cargar los planes de suscripción: {str(e)}")
        flash('Error al cargar los planes de suscripción. Por favor intenta nuevamente.', 'error')
        return redirect(url_for('user.dashboard'))
