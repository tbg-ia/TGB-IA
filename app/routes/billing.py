from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models.subscription import Subscription
from app.models.payment import Payment
from app import db

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')

@billing_bp.route('/')
@login_required
def index():
    """Página principal de facturación"""
    # Obtener historial de pagos del usuario
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).all()
    
    # Obtener suscripción activa
    subscription = Subscription.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).first()
    
    return render_template(
        'billing/index.html',
        payments=payments,
        subscription=subscription
    )

@billing_bp.route('/history')
@login_required
def payment_history():
    """Historial de pagos del usuario"""
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).all()
    return render_template('billing/history.html', payments=payments)
