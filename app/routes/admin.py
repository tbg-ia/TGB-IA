from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from app.auth.decorators import admin_required
from app.models.user import User
from app.models.trading_bot import TradingBot, Trade
from app.models.system_config import SystemConfig
from app import db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    bots = TradingBot.query.all()
    trades = Trade.query.order_by(Trade.timestamp.desc()).limit(10).all()
    return render_template('admin/dashboard.html', bots=bots, trades=trades)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'subscription_type': user.subscription_type,
        'subscription_expires': user.subscription_expires.isoformat() if user.subscription_expires else None
    })

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/config')
@login_required
@admin_required
def config():
    configs = SystemConfig.query.order_by(SystemConfig.category, SystemConfig.key).all()
    return render_template('admin/config.html', configs=configs)

@admin_bp.route('/config/<int:config_id>')
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

@admin_bp.route('/config/save', methods=['POST'])
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
