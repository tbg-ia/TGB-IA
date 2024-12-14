from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from . import billing_bp
from app.models.subscription import Subscription, Payment
from app import db

@billing_bp.route('/checkout')
@login_required
def checkout():
    return render_template('billing/checkout.html')

@billing_bp.route('/success')
@login_required
def payment_success():
    flash('Pago procesado exitosamente')
    return redirect(url_for('user.billing'))

@billing_bp.route('/cancel')
@login_required
def payment_cancel():
    flash('Pago cancelado')
    return redirect(url_for('user.billing'))

@billing_bp.route('/webhook', methods=['POST'])
def webhook():
    # Implementar lógica del webhook de pagos aquí
    return '', 200
