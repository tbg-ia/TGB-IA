import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask import current_app
from flask_login import login_required, current_user
import stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
from app.models.user import User
from app.models.subscription import Subscription, Payment
from app import db

subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/plans')
def plans():
    return render_template('subscription/plans.html')

@subscription_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Crea una sesión de checkout de Stripe"""
    try:
        plan_id = request.form.get('plan_id')
        if not plan_id:
            flash('Plan no especificado')
            return redirect(url_for('subscription.plans'))
        
        # Configurar los precios según el plan
        prices = {
            'basic_monthly': {
                'amount': 999,  # $9.99
                'name': 'Plan Básico',
                'trial_days': 7
            },
            'pro_monthly': {
                'amount': 2999,  # $29.99
                'name': 'Plan Pro',
                'trial_days': 7
            },
            'enterprise_monthly': {
                'amount': 9999,  # $99.99
                'name': 'Plan Enterprise',
                'trial_days': 7
            }
        }
        
        if plan_id not in prices:
            flash('Plan inválido')
            return redirect(url_for('subscription.plans'))
        
        plan_info = prices[plan_id]
        
        # Crear sesión de checkout
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': plan_info['name'],
                    },
                    'unit_amount': plan_info['amount'],
                    'recurring': {
                        'interval': 'month'
                    }
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('billing.payment_success', _external=True),
            cancel_url=url_for('billing.payment_cancel', _external=True),
            trial_period_days=plan_info['trial_days']
        )
        
        return redirect(checkout_session.url)
    except Exception as e:
        current_app.logger.error(f"Error al crear sesión de checkout: {str(e)}")
        flash('Error al procesar el pago')
        return redirect(url_for('subscription.plans'))

@subscription_bp.route('/subscription/webhook', methods=['POST'])
def webhook():
    """Maneja los webhooks de Stripe"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    
    if not webhook_secret:
        current_app.logger.error('Missing STRIPE_WEBHOOK_SECRET')
        return jsonify({'error': 'Webhook secret not configured'}), 500
        
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': 'Invalid signature'}), 400
    
    try:
        # Manejar diferentes tipos de eventos
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            handle_successful_payment(session)
            current_app.logger.info(f"Processed checkout.session.completed for session {session.id}")
            
        elif event['type'] == 'customer.subscription.created':
            subscription = event['data']['object']
            handle_subscription_created(subscription)
            current_app.logger.info(f"Processed subscription creation {subscription.id}")
            
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            handle_subscription_update(subscription)
            current_app.logger.info(f"Processed subscription update {subscription.id}")
            
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            handle_subscription_cancellation(subscription)
            current_app.logger.info(f"Processed subscription cancellation {subscription.id}")
            
        elif event['type'] == 'invoice.paid':
            invoice = event['data']['object']
            handle_invoice_paid(invoice)
            current_app.logger.info(f"Processed successful invoice payment {invoice.id}")
            
        elif event['type'] == 'invoice.payment_failed':
            invoice = event['data']['object']
            handle_invoice_payment_failed(invoice)
            current_app.logger.info(f"Processed failed invoice payment {invoice.id}")
            
        return jsonify({'success': True})
        
    except Exception as e:
        current_app.logger.error(f"Error processing webhook event: {str(e)}")
        return jsonify({'error': str(e)}), 500

def handle_subscription_update(stripe_subscription):
    """Maneja la actualización de una suscripción"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=stripe_subscription['id']
        ).first()
        
        if subscription:
            subscription.status = stripe_subscription['status']
            if stripe_subscription['status'] == 'active':
                subscription.end_date = datetime.fromtimestamp(stripe_subscription['current_period_end'])
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating subscription: {str(e)}")

def handle_subscription_created(stripe_subscription):
    """Maneja la creación de una nueva suscripción"""
    try:
        user = User.query.filter_by(stripe_customer_id=stripe_subscription['customer']).first()
        if not user:
            current_app.logger.error(f"User not found for customer: {stripe_subscription['customer']}")
            return
        
        subscription = Subscription(
            user_id=user.id,
            plan_type='pro' if stripe_subscription['plan']['amount'] >= 2999 else 'basic',
            status=stripe_subscription['status'],
            amount=stripe_subscription['plan']['amount'] / 100,
            start_date=datetime.fromtimestamp(stripe_subscription['current_period_start']),
            end_date=datetime.fromtimestamp(stripe_subscription['current_period_end']),
            stripe_subscription_id=stripe_subscription['id']
        )
        
        db.session.add(subscription)
        db.session.commit()
        current_app.logger.info(f"Created subscription for user: {user.email}")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating subscription: {str(e)}")

def handle_invoice_paid(invoice):
    """Maneja el pago exitoso de una factura"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=invoice['subscription']
        ).first()
        
        if subscription:
            payment = Payment(
                subscription_id=subscription.id,
                amount=invoice['amount_paid'] / 100,
                status='success',
                payment_method='stripe',
                transaction_id=invoice['payment_intent']
            )
            db.session.add(payment)
            db.session.commit()
            current_app.logger.info(f"Recorded successful payment for subscription: {subscription.id}")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing invoice payment: {str(e)}")

def handle_invoice_payment_failed(invoice):
    """Maneja el fallo en el pago de una factura"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=invoice['subscription']
        ).first()
        
        if subscription:
            payment = Payment(
                subscription_id=subscription.id,
                amount=invoice['amount_due'] / 100,
                status='failed',
                payment_method='stripe',
                transaction_id=invoice['payment_intent']
            )
            db.session.add(payment)
            
            # Actualizar estado de la suscripción
            subscription.status = 'past_due'
            
            db.session.commit()
            current_app.logger.info(f"Recorded failed payment for subscription: {subscription.id}")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing failed invoice: {str(e)}")

def handle_subscription_cancellation(stripe_subscription):
    """Maneja la cancelación de una suscripción"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=stripe_subscription['id']
        ).first()
        
        if subscription:
            subscription.status = 'cancelled'
            subscription.end_date = datetime.fromtimestamp(stripe_subscription['current_period_end'])
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error cancelling subscription: {str(e)}")

def handle_successful_payment(session):
    """Procesa un pago exitoso"""
    try:
        user = User.query.filter_by(email=session.customer_email).first()
        if not user:
            current_app.logger.error(f"User not found for email: {session.customer_email}")
            return
        
        # Obtener detalles de la suscripción de Stripe
        stripe_subscription = stripe.Subscription.retrieve(session.subscription)
        
        # Crear nueva suscripción
        subscription = Subscription(
            user_id=user.id,
            plan_type='pro' if session.amount_total >= 2999 else 'basic',
            status='active',
            amount=session.amount_total / 100,
            start_date=datetime.fromtimestamp(stripe_subscription.current_period_start),
            end_date=datetime.fromtimestamp(stripe_subscription.current_period_end),
            stripe_subscription_id=stripe_subscription.id
        )
        
        # Registrar el pago
        payment = Payment(
            subscription_id=subscription.id,
            amount=session.amount_total / 100,
            status='success',
            payment_method='stripe',
            transaction_id=session.payment_intent
        )
        
        # Actualizar el tipo de suscripción del usuario
        user.subscription_type = subscription.plan_type
        
        db.session.add(subscription)
        db.session.add(payment)
        db.session.commit()
        
        current_app.logger.info(f"Successfully processed payment for user: {user.email}")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing payment: {str(e)}")
