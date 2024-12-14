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

@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    try:
        configs = SystemConfig.query.order_by(SystemConfig.category).all()
        config_dict = {conf.key: conf.value for conf in configs}
        return render_template('admin/settings.html', config=config_dict)
    except Exception as e:
        logging.error(f"Error loading settings: {str(e)}")
        flash('Error loading system settings', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/settings/save', methods=['POST'])
@login_required
@admin_required
def save_settings():
    try:
        platform_name = request.form.get('platform_name')
        contact_email = request.form.get('contact_email')
        
        SystemConfig.set_value('PLATFORM_NAME', platform_name, 'system', 'Platform Name', current_user.id)
        SystemConfig.set_value('CONTACT_EMAIL', contact_email, 'system', 'Contact Email', current_user.id)
        
        flash('Configuración general actualizada exitosamente')
        return redirect(url_for('admin.settings'))
    except Exception as e:
        logging.error(f"Error saving settings: {str(e)}")
        flash('Error al guardar la configuración')
        return redirect(url_for('admin.settings'))

@admin_bp.route('/settings/trading/save', methods=['POST'])
@login_required
@admin_required
def save_trading_settings():
    try:
        for key in ['daily_trade_limit', 'max_trade_size', 'default_stop_loss']:
            value = request.form.get(key)
            if value:
                SystemConfig.set_value(
                    key.upper(),
                    value,
                    'trading',
                    f'Trading {key.replace("_", " ").title()}',
                    current_user.id
                )
        
        flash('Configuración de trading actualizada exitosamente')
        return redirect(url_for('admin.settings'))
    except Exception as e:
        logging.error(f"Error saving trading settings: {str(e)}")
        flash('Error al guardar la configuración de trading')
        return redirect(url_for('admin.settings'))

@admin_bp.route('/settings/api/save', methods=['POST'])
@login_required
@admin_required
def save_api_settings():
    try:
        # Configuración de API general
        for key in ['api_rate_limit', 'cache_timeout']:
            value = request.form.get(key)
            if value:
                SystemConfig.set_value(
                    key.upper(),
                    value,
                    'api',
                    f'API {key.replace("_", " ").title()}',
                    current_user.id
                )
        
        # Configuración de Stripe
        stripe_config = {
            'STRIPE_PUBLIC_KEY': request.form.get('stripe_public_key'),
            'STRIPE_SECRET_KEY': request.form.get('stripe_secret_key'),
            'STRIPE_WEBHOOK_SECRET': request.form.get('stripe_webhook_secret')
        }
        
        for key, value in stripe_config.items():
            if value:  # Solo actualizar si se proporcionó un valor
                SystemConfig.set_value(
                    key=key,
                    value=value,
                    category='payment',
                    description=f'Stripe API Configuration - {key}',
                    user_id=current_user.id
                )
        
        flash('Configuración de API actualizada exitosamente')
        return redirect(url_for('admin.settings'))
    except Exception as e:
        logging.error(f"Error saving API settings: {str(e)}")
        flash('Error al guardar la configuración de API')
        return redirect(url_for('admin.settings'))

@admin_bp.route('/settings/email/save', methods=['POST'])
@login_required
@admin_required
def save_email_settings():
    try:
        email_config = {
            'MAIL_SERVER': request.form.get('mail_server'),
            'MAIL_PORT': request.form.get('mail_port'),
            'MAIL_USERNAME': request.form.get('mail_username'),
            'MAIL_PASSWORD': request.form.get('mail_password'),
            'MAIL_DEFAULT_SENDER': request.form.get('mail_default_sender'),
            'MAIL_USE_TLS': request.form.get('mail_use_tls') == 'on'
        }
        
        for key, value in email_config.items():
            if value is not None:  # Solo actualizar si se proporcionó un valor
                SystemConfig.set_value(
                    key=key,
                    value=str(value),
                    category='email',
                    description=f'Email Configuration - {key}',
                    user_id=current_user.id
                )
        
        from app.mail.smtp_settings import EmailConfig
        EmailConfig.init_app(current_app)
        
        flash('Configuración de email actualizada exitosamente')
        return redirect(url_for('admin.settings'))
    except Exception as e:
        logging.error(f"Error saving email settings: {str(e)}")
        flash('Error al guardar la configuración de email')
        return redirect(url_for('admin.settings'))
@admin_bp.route('/settings/notification/save', methods=['POST'])
@login_required
@admin_required
def save_notification_settings():
    try:
        email_notifications = request.form.get('email_notifications') == 'on'
        trade_notifications = request.form.get('trade_notifications') == 'on'
        summary_frequency = request.form.get('summary_frequency')
        
        SystemConfig.set_value('EMAIL_NOTIFICATIONS', str(email_notifications), 'notification', 'Enable Email Notifications', current_user.id)
        SystemConfig.set_value('TRADE_NOTIFICATIONS', str(trade_notifications), 'notification', 'Enable Trade Notifications', current_user.id)
        if summary_frequency:
            SystemConfig.set_value('SUMMARY_FREQUENCY', summary_frequency, 'notification', 'Summary Email Frequency (hours)', current_user.id)
        
        flash('Configuración de notificaciones actualizada exitosamente')
        return redirect(url_for('admin.settings'))
    except Exception as e:
        logging.error(f"Error saving notification settings: {str(e)}")
        flash('Error al guardar la configuración de notificaciones')
        return redirect(url_for('admin.settings'))

@admin_bp.route('/subscription/plans')
@login_required
@admin_required
def subscription_plans():
    try:
        # Obtener estadísticas de suscripciones
        stats = {
            'total_subscribers': User.query.filter(User.subscription_type != 'basic').count(),
            'monthly_revenue': db.session.query(
                db.func.sum(Subscription.amount)
            ).filter(Subscription.status == 'active').scalar() or 0,
            'most_popular_plan': db.session.query(
                User.subscription_type,
                db.func.count(User.id).label('count')
            ).group_by(User.subscription_type).order_by(db.text('count DESC')).first()[0],
            'retention_rate': 95.5  # TODO: Implementar cálculo real
        }
        
        # Obtener planes activos
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        prices = stripe.Price.list(active=True, expand=['data.product'])
        plans = []
        
        for price in prices.data:
            plan = {
                'stripe_price_id': price.id,
                'name': price.product.name,
                'description': price.product.description,
                'price': price.unit_amount,
                'interval': price.recurring.interval,
                'subscriber_count': User.query.filter_by(subscription_type=price.product.name.lower()).count(),
                'is_active': price.active
            }
            plans.append(plan)
        
        return render_template('admin/subscription_plans.html', 
                             plans=plans,
                             stats=stats)
    except Exception as e:
        logging.error(f"Error loading subscription plans: {str(e)}")
        flash('Error al cargar los planes de suscripción', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/subscription/plans/<price_id>')
@login_required
@admin_required
def get_plan(price_id):
    try:
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        price = stripe.Price.retrieve(price_id, expand=['product'])
        
        return jsonify({
            'name': price.product.name,
            'description': price.product.description,
            'price': price.unit_amount/100,
            'interval': price.recurring.interval,
            'features': price.product.metadata.get('features', '').split('\n')
        })
    except Exception as e:
        logging.error(f"Error fetching plan {price_id}: {str(e)}")
        return jsonify({'error': 'Plan not found'}), 404

@admin_bp.route('/subscription/plans/save', methods=['POST'])
@login_required
@admin_required
def save_plan():
    try:
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        interval = request.form.get('interval')
        features = request.form.get('features')
        
        # Crear o actualizar el producto en Stripe
        product = stripe.Product.create(
            name=name,
            description=description,
            metadata={'features': features}
        )
        
        # Crear el precio para el producto
        stripe.Price.create(
            product=product.id,
            unit_amount=int(price * 100),  # Convertir a centavos
            currency='usd',
            recurring={'interval': interval}
        )
        
        flash('Plan creado exitosamente', 'success')
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error saving plan: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/subscription/plans/<price_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_plan(price_id):
    try:
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        price = stripe.Price.retrieve(price_id)
        
        # Activar/desactivar el precio en Stripe
        stripe.Price.modify(
            price_id,
            active=not price.active
        )
        
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error toggling plan {price_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/subscription/plans/<price_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_plan(price_id):
    try:
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        
        # Desactivar el precio en Stripe (no se pueden eliminar precios)
        stripe.Price.modify(
            price_id,
            active=False
        )
        
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error deleting plan {price_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500