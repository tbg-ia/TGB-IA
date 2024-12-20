from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app import db
import os
from app.models.base_exchange import BaseExchange
from app.models.exchange_credential import ExchangeCredential
from app.models.exchange_settings import ExchangeSettings
from app.integrations.crypto import init_crypto
from app.integrations.forex import init_forex
import logging
from datetime import datetime

exchanges_bp = Blueprint('exchanges', __name__, url_prefix='/api/exchanges')
logger = logging.getLogger(__name__)

@exchanges_bp.route('/add', methods=['POST'])
@login_required
def add_exchange():
    """Agrega un nuevo exchange con sus credenciales"""
    try:
        data = request.get_json()
        logger.info(f"Procesando solicitud para agregar exchange: {data.get('exchange_type')}")
        
        if not data or not data.get('exchange_type'):
            return jsonify({'success': False, 'error': 'Exchange type is required'}), 400
            
        exchange_type = data.get('exchange_type')
        use_env_credentials = data.get('use_env_credentials', False)
        
        # Verificar si el exchange existe
        exchange = BaseExchange.query.filter_by(exchange_type=exchange_type).first()
        if not exchange:
            return jsonify({'success': False, 'error': 'Exchange not supported'}), 400
            
        # Manejar credenciales
        credentials = None
        if use_env_credentials:
            # Usar credenciales del ambiente
            env_key = f"{exchange_type.upper()}_API_KEY"
            env_secret = f"{exchange_type.upper()}_API_SECRET"
            env_account = f"{exchange_type.upper()}_ACCOUNT_ID"
            
            api_key = os.environ.get(env_key)
            api_secret = os.environ.get(env_secret)
            account_id = os.environ.get(env_account)
            
            if not api_key or not api_secret:
                return jsonify({
                    'success': False,
                    'error': f'Environment credentials not found for {exchange_type}'
                }), 400
        else:
            # Usar credenciales proporcionadas
            creds_data = data.get('credentials', {})
            api_key = creds_data.get('api_key')
            api_secret = creds_data.get('api_secret')
            account_id = creds_data.get('account_id')
            
            if exchange.requires_api_key and not api_key:
                return jsonify({'success': False, 'error': 'API key is required'}), 400
            if exchange.requires_api_secret and not api_secret:
                return jsonify({'success': False, 'error': 'API secret is required'}), 400
            if exchange.requires_account_id and not account_id:
                return jsonify({'success': False, 'error': 'Account ID is required'}), 400
        
        # Crear credenciales
        credentials = ExchangeCredential(
            user_id=current_user.id,
            exchange_id=exchange.id,
            api_key=api_key,
            account_id=account_id,
            is_active=True
        )
        
        # Establecer API secret
        if api_secret:
            success, error = credentials.set_api_secret(api_secret)
            if not success:
                return jsonify({'success': False, 'error': error}), 400
        
        # Crear configuración de trading
        trading_settings = data.get('trading_settings', {})
        settings = ExchangeSettings(
            user_id=current_user.id,
            exchange_id=exchange.id,
            trading_enabled=trading_settings.get('trading_enabled', False),
            max_positions=trading_settings.get('max_positions', 5),
            max_leverage=trading_settings.get('max_leverage', 20),
            min_order_size=trading_settings.get('min_order_size', 10.0),
            max_order_size=trading_settings.get('max_order_size', 1000.0)
        )
        
        # Establecer y validar credenciales
        success, error = exchange.set_api_secret(api_secret)
        if not success:
            return jsonify({'success': False, 'error': error}), 400
            
        # Validar credenciales completas
        is_valid, error = exchange.validate_credentials()
        if not is_valid:
            return jsonify({'success': False, 'error': error}), 400
        
        try:
            # Guardar todo en la base de datos
            db.session.add(credentials)
            db.session.add(settings)
            db.session.commit()
            
            # Inicializar integración según el tipo
            if exchange_type in ['binance', 'bingx']:
                init_crypto(current_app)
            elif exchange_type == 'oanda':
                init_forex(current_app)
            
            logger.info(f"Exchange {exchange_type} configurado exitosamente para usuario {current_user.id}")
            
            return jsonify({
                'success': True,
                'message': 'Exchange configured successfully',
                'exchange': {
                    'info': exchange.to_dict(),
                    'credentials': credentials.to_dict(include_secrets=False),
                    'settings': settings.to_dict()
                }
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al guardar exchange en base de datos: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Error al guardar en base de datos'
            }), 500
            
    except Exception as e:
        logger.error(f"Error al agregar exchange: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@exchanges_bp.route('/update', methods=['POST'])
@login_required
def update_exchange():
    try:
        data = request.get_json()
        exchange_id = data.get('exchange_id')
        
        if not exchange_id:
            return jsonify({'success': False, 'error': 'Exchange ID is required'}), 400
            
        exchange = BaseExchange.query.filter_by(id=exchange_id, user_id=current_user.id).first()
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
