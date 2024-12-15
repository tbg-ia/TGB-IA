import os
import logging
from flask import Blueprint, render_template, jsonify, request, current_app, url_for, flash, redirect
from flask_login import login_required, current_user
import stripe
from datetime import datetime, timedelta
from sqlalchemy import case
from app.models.subscription import Subscription, Payment
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app import db

# Configuración de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/planes')
def plans():
    """Muestra los planes de suscripción disponibles"""
    try:
        logging.info("Accediendo a la página de planes")
        # Obtener los planes de la base de datos
        subscription_plans = SubscriptionPlan.query.order_by(
            case(
                (SubscriptionPlan.name == 'Básico', 1),
                (SubscriptionPlan.name == 'Pro', 2),
                (SubscriptionPlan.name == 'Enterprise', 3)
            )
        ).all()
        logging.info(f"Planes encontrados: {len(subscription_plans)}")
        return render_template('subscription/plans.html', plans=subscription_plans)
    except Exception as e:
        logging.error(f"Error al cargar la página de planes: {str(e)}")
        flash('Error al cargar los planes de suscripción', 'error')
        return redirect(url_for('index'))

@subscription_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Crea una sesión de checkout de Stripe"""
    try:
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        plan_id = request.form.get('plan_id')
        # Verificar que el plan seleccionado es de nivel superior al actual
        current_plan_level = {'basic': 0, 'pro': 1, 'enterprise': 2}
        user_plan_level = current_plan_level.get(current_user.subscription_type, -1)
        selected_plan_level = current_plan_level.get(plan_id.split('_')[0], -1)
        
        if selected_plan_level <= user_plan_level:
            flash('Ya tienes acceso a este plan o uno superior', 'warning')
            return redirect(url_for('subscription.plans'))
        
        plan_data = {
            'basic_monthly': {
                'price': 99,  # $0.99
                'name': 'Plan Básico Mensual',
                'description': 'Trading manual y análisis de mercado básico',
                'stripe_price_id': os.environ.get('STRIPE_BASIC_PRICE_ID')
            },
            'pro_monthly': {
                'price': 2999,  # $29.99
                'name': 'Plan Pro Mensual',
                'description': 'Trading automatizado, análisis avanzado y soporte 24/7',
                'stripe_price_id': os.environ.get('STRIPE_PRO_PRICE_ID')
            },
            'enterprise_monthly': {
                'price': 9999,  # $99.99
                'name': 'Plan Enterprise Mensual',
                'description': 'Trading automatizado avanzado y APIs personalizadas',
                'stripe_price_id': os.environ.get('STRIPE_ENTERPRISE_PRICE_ID')
            }
        }
        
        plan = plan_data.get(plan_id)
        if not plan:
            flash('Plan inválido seleccionado', 'error')
            return redirect(url_for('subscription.plans'))
            
        # Si el usuario ya tiene una suscripción activa, crear un upgrade
        current_subscription = Subscription.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).first()
        
        checkout_params = {
            'customer': current_user.stripe_customer_id if current_user.stripe_customer_id else None,
            'customer_email': None if current_user.stripe_customer_id else current_user.email,
            'payment_method_types': ['card'],
            'line_items': [{
                'price_data': {
                    'currency': 'usd',
                    'recurring': {
                        'interval': 'month'
                    },
                    'product_data': {
                        'name': plan['name'],
                        'description': plan['description']
                    },
                    'unit_amount': plan['price']
                },
                'quantity': 1
            }],
            'mode': 'subscription',
            'success_url': url_for('subscription.payment_success', _external=True),
            'cancel_url': url_for('subscription.payment_cancel', _external=True),
            'metadata': {
                'user_id': current_user.id,
                'plan_id': plan_id
            }
        }
        
        # Si es un upgrade, configurar el prorate
        if current_subscription and current_subscription.stripe_subscription_id:
            checkout_params['subscription_data'] = {
                'trial_period_days': None,  # No trial en upgrades
                'transfer_data': {
                    'destination': current_subscription.stripe_subscription_id,
                    'amount_percent': 100
                }
            }
        else:
            checkout_params['subscription_data'] = {
                'trial_period_days': 7  # Trial solo para nuevas suscripciones
            }
        
        # Crear sesión de checkout
        checkout_session = stripe.checkout.Session.create(**checkout_params)
        
        return redirect(checkout_session.url)
        
    except stripe.error.StripeError as e:
        flash(f'Error al procesar el pago: {str(e)}', 'error')
        return redirect(url_for('subscription.plans'))
    except Exception as e:
        flash('Error inesperado al procesar la solicitud', 'error')
        return redirect(url_for('subscription.plans'))

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

@subscription_bp.route('/webhook', methods=['POST'])
def webhook():
    """Maneja los webhooks de Stripe"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, current_app.config['STRIPE_WEBHOOK_SECRET']
        )
    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Manejar diferentes tipos de eventos
    event_handlers = {
        'checkout.session.completed': handle_checkout_completed,
        'customer.subscription.created': handle_subscription_created,
        'customer.subscription.updated': handle_subscription_updated,
        'customer.subscription.deleted': handle_subscription_deleted,
        'invoice.paid': handle_invoice_paid,
        'invoice.payment_failed': handle_invoice_payment_failed
    }
    
    handler = event_handlers.get(event['type'])
    if handler:
        try:
            handler(event['data']['object'])
        except Exception as e:
            logging.error(f"Error processing {event['type']}: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
def handle_checkout_completed(session):
    """Procesa una sesión de checkout completada exitosamente"""
    try:
        user_id = session.metadata.get('user_id')
        plan_id = session.metadata.get('plan_id')
        
        user = User.query.get(user_id)
        if not user:
            logging.error(f"Usuario no encontrado: {user_id}")
            return
        
        # Determinar el tipo de plan basado en el plan_id
        plan_type = plan_id.split('_')[0]  # basic, pro, enterprise
        
        # Crear nueva suscripción
        subscription = Subscription(
            user_id=user.id,
            plan_type=plan_type,
            status='active',
            stripe_subscription_id=session.subscription,
            amount=session.amount_total / 100,
            start_date=datetime.utcnow(),
            # El período de prueba es de 7 días
            end_date=datetime.utcnow() + timedelta(days=37)  # 30 días + 7 días de prueba
        )
        
        # Actualizar el tipo de suscripción del usuario
        user.subscription_type = plan_type
        
        db.session.add(subscription)
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error en handle_checkout_completed: {str(e)}")
        db.session.rollback()

def handle_subscription_created(subscription_object):
    """Maneja la creación de una nueva suscripción"""
    try:
        # Obtener el customer ID y buscar el usuario correspondiente
        customer_id = subscription_object.customer
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if not user:
            logging.error(f"Usuario no encontrado para customer_id: {customer_id}")
            return
            
        # Actualizar la suscripción con el ID de Stripe
        subscription = Subscription.query.filter_by(user_id=user.id, status='active').first()
        if subscription:
            subscription.stripe_subscription_id = subscription_object.id
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
            
        # Actualizar estado y fechas
        subscription.status = subscription_object.status
        subscription.end_date = datetime.fromtimestamp(subscription_object.current_period_end)
        
        # Si el plan cambió, actualizar el tipo de plan
        if subscription_object.items.data:
            new_plan = subscription_object.items.data[0].price.product
            subscription.plan_type = new_plan
            subscription.user.subscription_type = new_plan
            
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error en handle_subscription_updated: {str(e)}")
        db.session.rollback()

def handle_subscription_deleted(subscription_object):
    """Maneja la cancelación de una suscripción"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_object.id
        ).first()
        
        if not subscription:
            logging.error(f"Suscripción no encontrada: {subscription_object.id}")
            return
            
        # Marcar la suscripción como cancelada
        subscription.status = 'cancelled'
        subscription.end_date = datetime.fromtimestamp(subscription_object.canceled_at)
        
        # Revertir al plan básico
        subscription.user.subscription_type = 'basic'
        
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error en handle_subscription_deleted: {str(e)}")
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
            
        # Registrar el intento fallido de pago
        payment = Payment(
            subscription_id=subscription.id,
            amount=invoice.amount_due / 100,
            status='failed',
            payment_method='stripe',
            transaction_id=invoice.payment_intent
        )
        
        db.session.add(payment)
        
        # Si es el último intento fallido, marcar la suscripción como inactiva
        if invoice.next_payment_attempt is None:
            subscription.status = 'inactive'
            subscription.user.subscription_type = 'basic'
        
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error en handle_invoice_payment_failed: {str(e)}")
        db.session.rollback()
    return jsonify({'success': True})

def handle_successful_payment(session):
    """Procesa un pago exitoso"""
    user = User.query.filter_by(email=session.customer_email).first()
    if not user:
        return
    
    # Crear nueva suscripción
    subscription = Subscription(
        user_id=user.id,
        plan_type='pro' if session.amount_total >= 2999 else 'basic',
        status='active',
        amount=session.amount_total / 100,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30)
    )
    
    # Registrar el pago
    payment = Payment(
        subscription_id=subscription.id,
        amount=session.amount_total / 100,
        status='success',
        payment_method='stripe',
        transaction_id=session.payment_intent
    )
    
    db.session.add(subscription)
    db.session.add(payment)
    db.session.commit()
