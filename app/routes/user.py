from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash
from app.models.trading_bot import TradingBot, Trade
from app import db

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    return render_template('public/user_dashboard.html')

@user_bp.route('/account')
@login_required
def account():
    return render_template('public/account.html')

@user_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    try:
        # Por ahora solo permitimos actualizar información básica
        flash('Información actualizada correctamente')
        return redirect(url_for('user.account'))
    except Exception as e:
        flash('Error al actualizar la información')
        return redirect(url_for('user.account'))

@user_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not all([current_password, new_password, confirm_password]):
        flash('Todos los campos son requeridos')
        return redirect(url_for('user.account'))

    if new_password != confirm_password:
        flash('Las contraseñas nuevas no coinciden')
        return redirect(url_for('user.account'))

    if not check_password_hash(current_user.password_hash, current_password):
        flash('Contraseña actual incorrecta')
        return redirect(url_for('user.account'))

    try:
        current_user.set_password(new_password)
        db.session.commit()
        flash('Contraseña actualizada correctamente')
    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar la contraseña')

    return redirect(url_for('user.account'))

@user_bp.route('/bot/<int:bot_id>/trades')
@login_required
def get_bot_trades(bot_id):
    # Verify the bot belongs to the current user
    bot = TradingBot.query.filter_by(id=bot_id, user_id=current_user.id).first_or_404()
    trades = Trade.query.filter_by(bot_id=bot_id).order_by(Trade.timestamp.desc()).limit(50).all()
    return jsonify([{
        'type': trade.type,
        'price': trade.price,
        'amount': trade.amount,
        'timestamp': trade.timestamp.isoformat()
    } for trade in trades])

@user_bp.route('/subscription')
@login_required
def subscription():
    return render_template('public/planes.html')


@user_bp.route('/billing')
@login_required
def billing():
    current_subscription = Subscription.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).order_by(Subscription.created_at.desc()).first()
    
    payments = Payment.query.join(Subscription).filter(
        Subscription.user_id == current_user.id
    ).order_by(Payment.created_at.desc()).all()
    
    return render_template('public/billing.html', 
                         current_subscription=current_subscription,
                         payments=payments)

@user_bp.route('/upgrade_plan')
@login_required
def upgrade_plan():
    return redirect(url_for('user.subscription'))

@user_bp.route('/cancel_subscription', methods=['POST'])
@login_required
def cancel_subscription():
    try:
        subscription = Subscription.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).first()
        
        if subscription:
            subscription.status = 'cancelled'
            current_user.subscription_type = 'basic'
            db.session.commit()
            flash('Tu suscripción ha sido cancelada exitosamente')
        else:
            flash('No se encontró una suscripción activa')
            
    except Exception as e:
        db.session.rollback()
        flash('Error al cancelar la suscripción')
        
    return redirect(url_for('user.billing'))