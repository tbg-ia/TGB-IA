from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.auth.decorators import admin_required
from app.models.user import User
from app.models.subscription import Subscription
from app.models.system_config import SystemConfig
from app.models.trading_bot import TradingBot
from app.models.trade import Trade
from app.models.subscription_plan import SubscriptionPlan
from app.models.exchange_permission import ExchangePermission
from app import db
import logging
import stripe
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    try:
        # Obtener estadísticas básicas
        total_users = User.query.count()
        active_bots = db.session.query(db.func.count(TradingBot.id))\
            .filter(TradingBot.active == True).scalar() or 0
        
        try:
            # Obtener trades recientes con manejo de errores
            recent_trades = Trade.query.order_by(Trade.created_at.desc()).limit(10).all()
        except Exception as e:
            logging.error(f"Error fetching recent trades: {str(e)}")
            recent_trades = []

        try:
            # Obtener estadísticas de suscripciones
            total_subscribers = User.query.filter(User.subscription_type != 'basic').count()
            monthly_revenue = db.session.query(
                db.func.sum(Subscription.amount)
            ).filter(Subscription.status == 'active').scalar() or 0
        except Exception as e:
            logging.error(f"Error fetching subscription stats: {str(e)}")
            total_subscribers = 0
            monthly_revenue = 0

        # Intentar obtener la configuración de Stripe
        stripe_configured = False
        try:
            stripe_key = SystemConfig.get_value('STRIPE_SECRET_KEY')
            if stripe_key:
                stripe.api_key = stripe_key
                stripe_configured = True
        except Exception as e:
            logging.error(f"Error configuring Stripe: {str(e)}")

        stats = {
            'total_users': total_users,
            'active_bots': active_bots,
            'total_subscribers': total_subscribers,
            'monthly_revenue': monthly_revenue,
            'stripe_configured': stripe_configured
        }
        
        # Obtener planes de suscripción
        subscription_plans = SubscriptionPlan.query.all()
        
        return render_template('admin/dashboard.html', 
                             stats=stats,
                             trades=recent_trades,
                             subscription_plans=subscription_plans)
    except Exception as e:
        logging.error(f"Error in admin dashboard: {str(e)}")
        flash('Error loading dashboard data', 'error')
        return redirect(url_for('admin.dashboard'))

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
        # Obtener todas las configuraciones del sistema
        configs = SystemConfig.query.order_by(SystemConfig.category).all()
        config_dict = {conf.key: conf.value for conf in configs}
        
        # Obtener estadísticas de suscripciones para la sección de planes
        subscription_stats = {
            'total_subscribers': User.query.filter(User.subscription_type != 'basic').count(),
            'monthly_revenue': db.session.query(
                db.func.sum(Subscription.amount)
            ).filter(Subscription.status == 'active').scalar() or 0,
            'most_popular_plan': db.session.query(
                User.subscription_type,
                db.func.count(User.id).label('count')
            ).group_by(User.subscription_type).order_by(db.text('count DESC')).first(),
            'retention_rate': 95.5  # Valor por defecto
        }
        
        # Obtener las credenciales de Stripe existentes
        stripe_config = {
            'STRIPE_PUBLIC_KEY': SystemConfig.get_value('STRIPE_PUBLIC_KEY', ''),
            'STRIPE_SECRET_KEY': SystemConfig.get_value('STRIPE_SECRET_KEY', ''),
            'STRIPE_WEBHOOK_SECRET': SystemConfig.get_value('STRIPE_WEBHOOK_SECRET', '')
        }
        config_dict.update(stripe_config)
        
        return render_template('admin/settings/index.html',
                             config=config_dict,
                             subscription_stats=subscription_stats)
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
        # Validar campos requeridos de Stripe
        required_stripe_fields = ['stripe_public_key', 'stripe_secret_key', 'stripe_webhook_secret']
        for field in required_stripe_fields:
            if not request.form.get(field):
                flash(f'El campo {field.replace("stripe_", "").replace("_", " ").title()} es requerido', 'error')
                return redirect(url_for('admin.settings'))

        # Configuración de Stripe
        stripe_config = {
            'STRIPE_PUBLIC_KEY': request.form.get('stripe_public_key'),
            'STRIPE_SECRET_KEY': request.form.get('stripe_secret_key'),
            'STRIPE_WEBHOOK_SECRET': request.form.get('stripe_webhook_secret')
        }
        
        # Guardar configuración de Stripe
        for key, value in stripe_config.items():
            try:
                SystemConfig.set_value(
                    key=key,
                    value=value,
                    category='payment',
                    description=f'Stripe API Configuration - {key}',
                    user_id=current_user.id
                )
            except Exception as config_error:
                logging.error(f"Error saving Stripe config {key}: {str(config_error)}")
                flash(f'Error al guardar la configuración de Stripe: {key}', 'error')
                return redirect(url_for('admin.settings'))
        
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
        
        flash('Configuración de API y Stripe actualizada exitosamente', 'success')
        return redirect(url_for('admin.settings'))
    except Exception as e:
        logging.error(f"Error saving API settings: {str(e)}")
        flash('Error al guardar la configuración de API', 'error')
        return redirect(url_for('admin.settings'))

@admin_bp.route('/settings/email/save', methods=['POST'])
@login_required
@admin_required
def save_email_settings():
    try:
        # Validar campos requeridos
        required_fields = ['mail_server', 'mail_port', 'mail_username', 'mail_default_sender']
        for field in required_fields:
            if not request.form.get(field):
                flash(f'El campo {field.replace("mail_", "").replace("_", " ").title()} es requerido', 'error')
                return redirect(url_for('admin.settings'))

        # Procesar la configuración
        email_config = {
            'MAIL_SERVER': request.form.get('mail_server').strip(),
            'MAIL_PORT': int(request.form.get('mail_port')),
            'MAIL_USERNAME': request.form.get('mail_username').strip(),
            'MAIL_DEFAULT_SENDER': request.form.get('mail_default_sender').strip(),
            'MAIL_USE_TLS': request.form.get('mail_use_tls') == 'on'
        }

        # Actualizar contraseña solo si se proporciona una nueva
        if request.form.get('mail_password'):
            email_config['MAIL_PASSWORD'] = request.form.get('mail_password').strip()
        
        # Guardar cada configuración
        for key, value in email_config.items():
            try:
                SystemConfig.set_value(
                    key=key,
                    value=str(value),
                    category='email',
                    description=f'Email Configuration - {key}',
                    user_id=current_user.id
                )
            except Exception as config_error:
                logging.error(f"Error saving {key}: {str(config_error)}")
                flash(f'Error al guardar {key}', 'error')
                return redirect(url_for('admin.settings'))

        # Actualizar la configuración de email en la aplicación
        try:
            from app.mail.smtp_settings import email_config as EmailConfig #Renamed to avoid import conflict
            mail = EmailConfig.init_app(current_app)
            
            # Probar la conexión
            with current_app.app_context():
                mail.connect()
                
            flash('Configuración de email actualizada y verificada exitosamente', 'success')
            return redirect(url_for('admin.settings'))
        except Exception as email_init_error:
            logging.error(f"Error initializing email config: {str(email_init_error)}")
            flash(f'Error al inicializar la configuración de email: {str(email_init_error)}', 'error')
            return redirect(url_for('admin.settings'))
            
    except ValueError as ve:
        logging.error(f"Validation error in email settings: {str(ve)}")
        flash('Error de validación en los datos ingresados', 'error')
        return redirect(url_for('admin.settings'))
    except Exception as e:
        logging.error(f"Error saving email settings: {str(e)}")
        flash('Error al guardar la configuración de email', 'error')
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
def manage_subscription_plans():
    """Ruta para gestionar planes de suscripción (solo administradores)"""
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
            ).group_by(User.subscription_type).order_by(db.text('count DESC')).first(),
            'retention_rate': 95.5  # TODO: Implementar cálculo real
        }
        
        # Obtener planes de la base de datos
        subscription_plans = SubscriptionPlan.query.all()
        for plan in subscription_plans:
            # Obtener el número de suscriptores para cada plan
            plan.subscriber_count = User.query.filter_by(subscription_type=plan.name.lower()).count()
        
        return render_template('admin/subscription/plans.html', 
                             subscription_plans=subscription_plans,
                             stats=stats)
    except Exception as e:
        logging.error(f"Error loading subscription plans: {str(e)}")
        flash('Error al cargar los planes de suscripción', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/subscription/plans/<int:plan_id>')
@login_required
@admin_required
def get_plan(plan_id):
    try:
        plan = SubscriptionPlan.query.get_or_404(plan_id)
        exchange_limits = plan.get_exchange_limits()
        
        return jsonify({
            'name': plan.name,
            'description': plan.description,
            'price': plan.price/100,
            'interval': plan.interval,
            'active_signals': exchange_limits['active_signals'],
            'apis_per_exchange': exchange_limits['apis_per_exchange'],
            'has_manual_trading': plan.has_manual_trading,
            'has_automated_trading': plan.has_automated_trading,
            'has_advanced_trading': plan.has_advanced_trading,
            'has_basic_analysis': plan.has_basic_analysis,
            'has_advanced_analysis': plan.has_advanced_analysis,
            'has_custom_dashboard': plan.has_custom_dashboard,
            'max_bots': plan.max_bots,
            'has_custom_bots': plan.has_custom_bots,
            'has_unlimited_bots': plan.has_unlimited_bots,
            'has_api_access': plan.has_api_access,
            'has_custom_apis': plan.has_custom_apis,
            'support_level': plan.support_level,
            'trial_days': plan.trial_days,
            'cancellation_type': plan.cancellation_type
        })
    except Exception as e:
        logging.error(f"Error fetching plan {plan_id}: {str(e)}")
        return jsonify({'error': 'Plan not found'}), 404

@admin_bp.route('/subscription/plans/<int:plan_id>/update', methods=['POST'])
@login_required
@admin_required
def update_plan(plan_id):
    try:
        logging.info(f"Actualizando plan {plan_id} con datos: {request.form}")
        plan = SubscriptionPlan.query.get_or_404(plan_id)
        
        # Validar campos requeridos
        required_fields = {
            'name': "El nombre del plan es requerido",
            'price': "El precio es requerido",
            'interval': "El intervalo es requerido"
        }
        
        for field, message in required_fields.items():
            if not request.form.get(field):
                raise ValueError(message)
        
        # Actualizar datos básicos del plan
        plan.name = request.form.get('name')
        plan.description = request.form.get('description')
        
        # Procesar precio
        try:
            price_value = request.form.get('price', '0').replace(',', '.')
            plan.price = int(float(price_value) * 100)  # Convertir a centavos
        except ValueError:
            raise ValueError("El precio debe ser un número válido")
            
        plan.interval = request.form.get('interval')
        
        # Procesar características booleanas
        boolean_fields = [
            'has_manual_trading', 'has_automated_trading', 'has_advanced_trading',
            'has_basic_analysis', 'has_advanced_analysis', 'has_custom_dashboard',
            'has_custom_bots', 'has_unlimited_bots', 'has_api_access', 'has_custom_apis'
        ]
        
        for field in boolean_fields:
            setattr(plan, field, request.form.get(field) == 'on')
        
        # Procesar campos numéricos
        numeric_fields = {
            'max_bots': ('El número máximo de bots debe ser un número entero', int),
            'trial_days': ('Los días de prueba deben ser un número entero', int),
            'active_signals': ('Las señales activas deben ser un número entero', int),
            'apis_per_exchange': ('Las APIs por exchange deben ser un número entero', int)
        }
        
        for field, (error_msg, convert_func) in numeric_fields.items():
            try:
                value = request.form.get(field, '0')
                if value.strip():
                    setattr(plan, field, convert_func(value))
            except ValueError:
                raise ValueError(error_msg)
        
        # Configurar soporte y cancelación
        plan.support_level = request.form.get('support_level', 'email')
        plan.cancellation_type = request.form.get('cancellation_type', 'anytime')
        
        # Actualizar o crear permisos de exchange
        exchange_permission = plan.exchange_permission
        if not exchange_permission:
            exchange_permission = ExchangePermission(subscription_plan_id=plan.id)
            db.session.add(exchange_permission)
        
        try:
            exchange_permission.active_signals = int(request.form.get('active_signals', 1))
            exchange_permission.apis_per_exchange = int(request.form.get('apis_per_exchange', 1))
        except ValueError:
            raise ValueError("Los valores de señales activas y APIs por exchange deben ser números enteros")
        
        db.session.commit()
        logging.info(f"Plan {plan_id} actualizado exitosamente")
        
        return jsonify({
            'success': True,
            'message': 'Plan actualizado exitosamente'
        })
        
    except ValueError as e:
        db.session.rollback()
        logging.error(f"Error de validación al actualizar plan {plan_id}: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error al actualizar plan {plan_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/subscription/plans/save', methods=['POST'])
@login_required
@admin_required
def save_plan():
    try:
        # Obtener la clave de Stripe de la configuración del sistema
        stripe_key = SystemConfig.get_value('STRIPE_SECRET_KEY')
        if not stripe_key:
            raise ValueError("Stripe API key not configured")
        
        stripe.api_key = stripe_key
        
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        interval = request.form.get('interval')
        features = request.form.get('features')
        
        if not all([name, price, interval]):
            raise ValueError("Missing required fields")
        
        try:
            # Crear el producto en Stripe
            product = stripe.Product.create(
                name=name,
                description=description,
                metadata={'features': features}
            )
            
            # Crear el precio en Stripe
            stripe_price = stripe.Price.create(
                product=product.id,
                unit_amount=int(price * 100),  # Convertir a centavos
                currency='usd',
                recurring={'interval': interval}
            )
            
            # Guardar en la base de datos local
            plan = SubscriptionPlan(
                name=name,
                description=description,
                price=int(price * 100),
                interval=interval,
                features=features,
                stripe_product_id=product.id,
                stripe_price_id=stripe_price.id
            )
            
            db.session.add(plan)
            db.session.commit()
            
            flash('Plan creado exitosamente', 'success')
            return jsonify({'success': True})
            
        except stripe.error.StripeError as e:
            db.session.rollback()
            logging.error(f"Stripe API error: {str(e)}")
            return jsonify({'error': f"Error with Stripe: {str(e)}"}), 500
            
    except ValueError as e:
        logging.error(f"Validation error: {str(e)}")
        return jsonify({'error': str(e)}), 400
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error saving plan: {str(e)}")
        return jsonify({'error': "An unexpected error occurred"}), 500

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

@admin_bp.route('/settings/test-email', methods=['POST'])
@login_required
@admin_required
def test_email():
    """Envía un email de prueba para verificar la configuración SMTP."""
    test_email = request.form.get('test_email')
    if not test_email:
        flash('Por favor, ingrese una dirección de email válida', 'error')
        return redirect(url_for('admin.settings'))
    
    try:
        logging.info("=== Iniciando prueba de email SMTP ===")
        
        # Importar después de las validaciones para evitar problemas de importación
        from flask_mail import Message
        from app.mail.smtp_settings import email_config
        
        # Inicializar Mail
        try:
            mail = email_config.init_mail(current_app)
            logging.info("Cliente de correo inicializado correctamente")
        except ValueError as ve:
            error_msg = f'Error de configuración SMTP: {str(ve)}'
            logging.error(error_msg)
            flash(error_msg, 'error')
            return redirect(url_for('admin.settings'))
        except Exception as e:
            error_msg = f'Error al inicializar cliente SMTP: {str(e)}'
            logging.error(error_msg)
            flash(error_msg, 'error')
            return redirect(url_for('admin.settings'))
        
        # Crear mensaje
        try:
            msg = Message(
                subject='Test de Configuración SMTP',
                sender=os.environ.get('MAIL_DEFAULT_SENDER'),
                recipients=[test_email]
            )
            
            msg.body = 'Este es un email de prueba para verificar la configuración SMTP.'
            msg.html = '''
                <h3>Test de Configuración SMTP</h3>
                <p>Este es un email de prueba para verificar la configuración SMTP.</p>
                <p>Si estás recibiendo este mensaje, la configuración de email está funcionando correctamente.</p>
            '''
            logging.info("Mensaje creado correctamente")
            
        except Exception as e:
            error_msg = f'Error al crear el mensaje: {str(e)}'
            logging.error(error_msg)
            flash(error_msg, 'error')
            return redirect(url_for('admin.settings'))
        
        # Enviar email
        try:
            with current_app.app_context():
                with mail.connect() as conn:
                    conn.send(msg)
            logging.info(f"Email de prueba enviado exitosamente a {test_email}")
            flash('Email de prueba enviado exitosamente', 'success')
            
        except Exception as e:
            error_msg = f'Error al enviar el email: {str(e)}'
            logging.error(error_msg)
            flash(error_msg, 'error')
            return redirect(url_for('admin.settings'))
            
    except Exception as e:
        error_msg = f"Error general: {str(e)}"
        logging.error(error_msg)
        flash(error_msg, 'error')
        
    return redirect(url_for('admin.settings'))