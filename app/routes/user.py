import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.subscription import Subscription, Payment
from app.models.trading_bot import TradingBot, Trade
from app import db

UPLOAD_FOLDER = 'app/static/uploads/profile_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Asegurarse de que el directorio de subidas existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/profile')
@login_required
def profile():
    return render_template('public/profile.html')

@user_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    try:
        current_user.first_name = request.form.get('first_name', '').strip() or None
        current_user.last_name = request.form.get('last_name', '').strip() or None
        
        db.session.commit()
        flash('Información actualizada correctamente')
        return redirect(url_for('user.profile'))
    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar la información')
        return redirect(url_for('user.profile'))

@user_bp.route('/upload-profile-image', methods=['POST'])
@login_required
def upload_profile_image():
    if 'profile_image' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})
    
    file = request.files['profile_image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"user_{current_user.id}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Guardar el archivo
        file.save(filepath)
        
        # Actualizar la URL de la imagen en el perfil del usuario
        image_url = url_for('static', filename=f'uploads/profile_images/{filename}')
        current_user.profile_image = image_url
        db.session.commit()
        
        return jsonify({
            'success': True,
            'image_url': image_url
        })
    
    return jsonify({'success': False, 'error': 'File type not allowed'})

@user_bp.route('/subscription')
@login_required
def subscription():
    return redirect(url_for('subscription.plans'))

@user_bp.route('/billing')
@login_required
def billing():
    try:
        # Obtener la suscripción actual
        current_subscription = Subscription.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).first()
        
        # Obtener el historial de pagos
        payments = Payment.query.join(Subscription).filter(
            Subscription.user_id == current_user.id
        ).order_by(Payment.created_at.desc()).all()
        
        # Obtener métodos de pago guardados (si se usa Stripe)
        payment_methods = []
        if current_user.stripe_customer_id:
            stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
            try:
                payment_methods = stripe.PaymentMethod.list(
                    customer=current_user.stripe_customer_id,
                    type='card'
                ).data
            except stripe.error.StripeError as e:
                logging.error(f"Error al obtener métodos de pago: {str(e)}")
        
        return render_template('public/billing.html',
                             current_subscription=current_subscription,
                             payments=payments,
                             payment_methods=payment_methods)
    except Exception as e:
        logging.error(f"Error en la página de facturación: {str(e)}")
        flash('Error al cargar la información de facturación', 'error')
        return redirect(url_for('user.profile'))

@user_bp.route('/cancel-subscription', methods=['POST'])
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


@user_bp.route('/account')
@login_required
def account():
    return render_template('public/account.html')

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

@user_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    return render_template('public/user_dashboard.html')

@user_bp.route('/upgrade_plan')
@login_required
def upgrade_plan():
    return redirect(url_for('subscription.plans'))