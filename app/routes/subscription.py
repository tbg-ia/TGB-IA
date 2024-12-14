from flask import Blueprint, render_template, jsonify, request, current_app, url_for
from flask_login import login_required, current_user
import stripe
from datetime import datetime, timedelta
from app.models.subscription import Subscription, Payment
from app.models.user import User
from app import db

subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/planes')
def plans():
    """Muestra los planes de suscripción disponibles"""
    return render_template('subscription/plans.html')

@subscription_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Crea una sesión de checkout de Stripe"""
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    
    plan_id = request.form.get('plan_id')
    plan_data = {
        'basic_monthly': {
            'price': 999,  # $9.99
            'name': 'Plan Básico',
            'trial_days': 14
        },
        'pro_monthly': {
            'price': 2999,  # $29.99
            'name': 'Plan Pro',
            'trial_days': 14
        },
        'enterprise_monthly': {
            'price': 9999,  # $99.99
            'name': 'Plan Enterprise',
            'trial_days': 14
        }
    }
    
    plan = plan_data.get(plan_id)
    if not plan:
        return jsonify({'error': 'Plan inválido'}), 400
    
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': plan['name'],
                    },
                    'unit_amount': plan['price'],
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('subscription.payment_success', _external=True),
            cancel_url=url_for('subscription.payment_cancel', _external=True),
        )
        
        return jsonify({'sessionId': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 403

@subscription_bp.route('/payment/success')
@login_required
def payment_success():
    """Maneja el éxito del pago"""
    return render_template('subscription/payment_success.html')

@subscription_bp.route('/payment/cancel')
@login_required
def payment_cancel():
    """Maneja la cancelación del pago"""
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
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)
    
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
