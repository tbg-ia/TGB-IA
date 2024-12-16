from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.base_exchange import BaseExchange
from app.models.crypto_exchange import CryptoExchange
from app.models.forex_exchange import ForexExchange
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
        
        if not data:
            return jsonify({'success': False, 'error': 'No se proporcionaron datos'}), 400
            
        exchange_type = data.get('exchange_type')
        api_key = data.get('api_key')
        api_secret = data.get('api_secret')
        
        if not exchange_type or not api_key or not api_secret:
            return jsonify({
                'success': False, 
                'error': 'Se requieren exchange_type, api_key y api_secret'
            }), 400
        
        # Crear instancia según el tipo de exchange
        if exchange_type in ['binance', 'bingx']:
            exchange = CryptoExchange(
                name=exchange_type.upper(),
                exchange_type=exchange_type,
                api_key=api_key,
                user_id=current_user.id,
                is_active=True,
                trading_enabled=False  # Por seguridad, inicialmente deshabilitado
            )
        elif exchange_type == 'oanda':
            account_id = data.get('account_id')
            if not account_id:
                return jsonify({
                    'success': False,
                    'error': 'Se requiere account_id para OANDA'
                }), 400
                
            exchange = ForexExchange(
                name='OANDA',
                exchange_type='oanda',
                api_key=api_key,
                user_id=current_user.id,
                account_id=account_id,
                is_active=True,
                trading_enabled=False
            )
        else:
            return jsonify({
                'success': False,
                'error': f'Tipo de exchange no soportado: {exchange_type}'
            }), 400
        
        # Establecer y validar credenciales
        success, error = exchange.set_api_secret(api_secret)
        if not success:
            return jsonify({'success': False, 'error': error}), 400
            
        # Validar credenciales completas
        is_valid, error = exchange.validate_credentials()
        if not is_valid:
            return jsonify({'success': False, 'error': error}), 400
        
        try:
            db.session.add(exchange)
            db.session.commit()
            
            # Inicializar integración según el tipo
            if exchange_type in ['binance', 'bingx']:
                init_crypto(current_app)
            elif exchange_type == 'oanda':
                init_forex(current_app)
                
            exchange.update_connection_status('connected')
            db.session.commit()
            
            logger.info(f"Exchange {exchange_type} agregado exitosamente para usuario {current_user.id}")
            return jsonify({
                'success': True,
                'message': 'Exchange agregado exitosamente',
                'exchange': exchange.to_dict()
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
