from flask import Blueprint, render_template, jsonify, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app.auth.decorators import admin_required
from app.models.trading_bot import TradingBot, Trade
from app.models.user import User
from app.models.system_config import SystemConfig
from app import db
from datetime import datetime

crypto_bp = Blueprint('crypto', __name__)

@crypto_bp.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    bots = TradingBot.query.all()
    trades = Trade.query.order_by(Trade.timestamp.desc()).limit(10).all()
    return render_template('admin/dashboard.html', bots=bots, trades=trades)

@crypto_bp.route('/user-dashboard')
@login_required
def user_dashboard():
    return render_template('public/user_dashboard.html')

@crypto_bp.route('/planes')
def planes():
    return render_template('public/planes.html')

@crypto_bp.route('/bot/<int:bot_id>/trades')
@login_required
def get_bot_trades(bot_id):
    trades = Trade.query.filter_by(bot_id=bot_id).order_by(Trade.timestamp.desc()).limit(50).all()
    return jsonify([{
        'type': trade.type,
        'price': trade.price,
        'amount': trade.amount,
        'timestamp': trade.timestamp.isoformat()
    } for trade in trades])

# Rutas administrativas
@crypto_bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@crypto_bp.route('/admin/users/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'subscription_type': user.subscription_type,
        'subscription_expires': user.subscription_expires.strftime('%Y-%m-%d') if user.subscription_expires else None
    })

@crypto_bp.route('/admin/users/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    user.subscription_type = request.form.get('subscription_type')
    expires_str = request.form.get('subscription_expires')
    if expires_str:
        user.subscription_expires = datetime.strptime(expires_str, '%Y-%m-%d')
    db.session.commit()
    return jsonify({'success': True})

@crypto_bp.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({'success': True})

@crypto_bp.route('/admin/config')
@login_required
@admin_required
def admin_config():
    configs = SystemConfig.query.order_by(SystemConfig.category, SystemConfig.key).all()
    return render_template('admin/config.html', configs=configs)

@crypto_bp.route('/admin/config/<int:config_id>')
@login_required
@admin_required
def get_config(config_id):
    config = SystemConfig.query.get_or_404(config_id)
    return jsonify({
        'key': config.key,
        'value': config.value,
        'category': config.category,
        'description': config.description
    })

@crypto_bp.route('/admin/config/save', methods=['POST'])
@login_required
@admin_required
def save_config():
    key = request.form.get('key')
    value = request.form.get('value')
    category = request.form.get('category')
    description = request.form.get('description')
    
    config = SystemConfig.set_value(
        key=key,
        value=value,
        category=category,
        description=description,
        user_id=current_user.id
    )
    
    return jsonify({'success': True})