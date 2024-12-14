from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from app.auth.decorators import admin_required
from app.models.user import User
from app.models.trading_bot import TradingBot, Trade
from app.models.system_config import SystemConfig
from app import db
import logging

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    try:
        total_users = User.query.count()
        active_bots = TradingBot.query.filter_by(active=True).count()
        recent_trades = Trade.query.order_by(Trade.timestamp.desc()).limit(10).all()
        
        return render_template('admin/dashboard.html', 
                             stats={'total_users': total_users, 
                                   'active_bots': active_bots},
                             trades=recent_trades)
    except Exception as e:
        logging.error(f"Error in admin dashboard: {str(e)}")
        flash('Error loading dashboard data', 'error')
        return redirect(url_for('index'))

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    try:
        users = User.query.all()
        return render_template('admin/users.html', users=users)
    except Exception as e:
        logging.error(f"Error fetching users: {str(e)}")
        flash('Error loading user data', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        return jsonify({
            'subscription_type': user.subscription_type,
            'subscription_expires': user.subscription_expires.isoformat() if user.subscription_expires else None,
            'role': user.get_role_name()
        })
    except Exception as e:
        logging.error(f"Error fetching user {user_id}: {str(e)}")
        return jsonify({'error': 'User not found'}), 404

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    try:
        user = User.query.get_or_404(user_id)
        if user.is_admin():
            return jsonify({'error': 'Cannot deactivate admin users'}), 400
        user.is_active = not user.is_active
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error toggling user status {user_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update user status'}), 500

@admin_bp.route('/config')
@login_required
@admin_required
def config():
    try:
        configs = SystemConfig.query.order_by(SystemConfig.category, SystemConfig.key).all()
        return render_template('admin/config.html', configs=configs)
    except Exception as e:
        logging.error(f"Error fetching configs: {str(e)}")
        flash('Error loading configuration data', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/config/<int:config_id>')
@login_required
@admin_required
def get_config(config_id):
    try:
        config = SystemConfig.query.get_or_404(config_id)
        return jsonify({
            'key': config.key,
            'value': config.value,
            'category': config.category,
            'description': config.description
        })
    except Exception as e:
        logging.error(f"Error fetching config {config_id}: {str(e)}")
        return jsonify({'error': 'Configuration not found'}), 404

@admin_bp.route('/config/save', methods=['POST'])
@login_required
@admin_required
def save_config():
    try:
        key = request.form.get('key')
        value = request.form.get('value')
        category = request.form.get('category')
        description = request.form.get('description')
        
        if not all([key, value, category]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        config = SystemConfig.set_value(
            key=key,
            value=value,
            category=category,
            description=description,
            user_id=current_user.id
        )
        
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error saving config: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to save configuration'}), 500
