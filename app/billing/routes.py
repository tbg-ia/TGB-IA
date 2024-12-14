import os
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from . import billing_bp
from app.models.subscription import Subscription, Payment
from app import db
import stripe

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

@billing_bp.route('/invoice')
@login_required
def invoice():
    try:
        # Obtener suscripción activa
        subscription = Subscription.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).first()
        
        # Obtener método de pago si existe
        payment_method = None
        if current_user.stripe_customer_id:
            try:
                payment_methods = stripe.PaymentMethod.list(
                    customer=current_user.stripe_customer_id,
                    type='card'
                )
                if payment_methods.data:
                    payment_method = payment_methods.data[0]
            except stripe.error.StripeError as e:
                flash('Error al obtener método de pago', 'error')
        
        # Obtener facturas
        invoices = Payment.query.join(Subscription).filter(
            Subscription.user_id == current_user.id
        ).order_by(Payment.created_at.desc()).all()
        
        return render_template('billing/invoice.html',
                             subscription=subscription,
                             payment_method=payment_method,
                             invoices=invoices,
                             now=datetime.utcnow(),
                             stripe_public_key=os.environ.get('STRIPE_PUBLIC_KEY'))
                             
    except Exception as e:
        flash('Error al cargar la información de facturación', 'error')
        return redirect(url_for('user.dashboard'))

@billing_bp.route('/update-payment-method', methods=['POST'])
@login_required
def update_payment_method():
    try:
        payment_method_id = request.json.get('payment_method_id')
        
        # Actualizar método de pago en Stripe
        if current_user.stripe_customer_id:
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=current_user.stripe_customer_id,
            )
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@billing_bp.route('/update-address', methods=['POST'])
@login_required
def update_address():
    try:
        # Implementar actualización de dirección
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@billing_bp.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ.get('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError as e:
        return '', 400
    except stripe.error.SignatureVerificationError as e:
        return '', 400

    if event.type == 'payment_method.attached':
        payment_method = event.data.object
        print(f'PaymentMethod was attached to a Customer: {payment_method.id}')

    return '', 200
