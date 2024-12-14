from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from .models import Payment, Subscription
from .services import SubscriptionService, PaymentService

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/checkout/<plan_type>')
@login_required
def checkout(plan_type):
    """Página de checkout para un plan específico"""
    return render_template('billing/checkout.html', plan_type=plan_type)

@billing_bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    """Procesar una nueva suscripción"""
    try:
        plan_type = request.form.get('plan_type')
        payment_method = request.form.get('payment_method')
        
        # Crear suscripción
        subscription = SubscriptionService.create_subscription(
            user_id=current_user.id,
            plan_type=plan_type
        )
        
        # Crear pago
        payment = PaymentService.create_payment(
            user_id=current_user.id,
            amount=subscription.price,
            payment_method=payment_method
        )
        
        # Procesar pago
        PaymentService.process_payment(payment.id)
        
        flash('Suscripción activada exitosamente')
        return redirect(url_for('user.billing'))
        
    except Exception as e:
        flash('Error al procesar la suscripción')
        return redirect(url_for('billing.checkout', plan_type=plan_type))

@billing_bp.route('/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancelar una suscripción activa"""
    try:
        subscription = Subscription.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).first()
        
        if subscription:
            SubscriptionService.cancel_subscription(subscription.id)
            flash('Suscripción cancelada exitosamente')
        else:
            flash('No se encontró una suscripción activa')
            
    except Exception as e:
        flash('Error al cancelar la suscripción')
        
    return redirect(url_for('user.billing'))
