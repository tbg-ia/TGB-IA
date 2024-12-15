from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.exchange import Exchange
from app.integrations.crypto import init_crypto
from app.integrations.forex import init_forex
import logging

exchanges_bp = Blueprint('exchanges', __name__, url_prefix='/api/exchanges')
logger = logging.getLogger(__name__)

@exchanges_bp.route('/add', methods=['POST'])
@login_required
def add_exchange():
    try:
        data = request.get_json()
        exchange_type = data.get('exchange_type')
        
        if not exchange_type:
            return jsonify({'success': False, 'error': 'Exchange type is required'}), 400
            
        # Crear nuevo exchange
        exchange = Exchange(
            name=exchange_type.upper(),
            exchange_type=exchange_type,
            api_key=data.get('api_key'),
            user_id=current_user.id,
            is_active=True
        )
        
        # Manejar credenciales específicas de OANDA
        if exchange_type == 'oanda':
            exchange.account_id = data.get('oanda_account_id')
            if not exchange.account_id:
                return jsonify({'success': False, 'error': 'OANDA Account ID is required'}), 400
        
        # Establecer API secret
        api_secret = data.get('api_secret')
        if api_secret:
            exchange.set_api_secret(api_secret)
        
        db.session.add(exchange)
        db.session.commit()
        
        # Inicializar integración según el tipo de exchange
        if exchange_type in ['binance', 'bingx']:
            init_crypto(current_app)
        elif exchange_type == 'oanda':
            init_forex(current_app)
        
        return jsonify({
            'success': True,
            'message': 'Exchange added successfully',
            'exchange': exchange.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error adding exchange: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@exchanges_bp.route('/update', methods=['POST'])
@login_required
def update_exchange():
    try:
        data = request.get_json()
        exchange_id = data.get('exchange_id')
        
        if not exchange_id:
            return jsonify({'success': False, 'error': 'Exchange ID is required'}), 400
            
        exchange = Exchange.query.filter_by(id=exchange_id, user_id=current_user.id).first()
        if not exchange:
            return jsonify({'success': False, 'error': 'Exchange not found'}), 404
        
        # Actualizar campos
        if 'api_key' in data and data['api_key']:
            exchange.api_key = data['api_key']
        
        if 'api_secret' in data and data['api_secret']:
            exchange.set_api_secret(data['api_secret'])
            
        if 'is_active' in data:
            exchange.is_active = data['is_active']
        
        exchange.last_updated = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Exchange updated successfully',
            'exchange': exchange.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating exchange: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
