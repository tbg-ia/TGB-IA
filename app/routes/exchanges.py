from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
import os
from dotenv import load_dotenv

load_dotenv()
from flask_login import login_required, current_user
from app import db
import logging

logger = logging.getLogger(__name__)
from app.models.base_exchange import BaseExchange
from app.models.exchanges.binance_exchange import BinanceExchange
from app.models.exchanges.bingx_exchange import BingXExchange
from app.models.exchanges.oanda_exchange import OandaExchange

exchanges_bp = Blueprint('exchanges_routes', __name__)

@exchanges_bp.route('/exchanges')
@login_required
def list_exchanges():
    """List all exchanges for the current user."""
    exchanges = BaseExchange.query.filter_by(user_id=current_user.id).all()
    return render_template('public/exchanges.html', exchanges=exchanges)

@exchanges_bp.route('/api/exchanges/add', methods=['POST'])
@login_required
def add_exchange():
    try:
        data = request.get_json()
        logger.info(f"Recibiendo solicitud para agregar exchange: {data.get('exchange_type')}")
        
        # Validar datos requeridos
        required_fields = ['exchange_type', 'api_key', 'api_secret']
        if data.get('exchange_type') == 'oanda':
            required_fields.append('account_id')
            
        if not all(data.get(field) for field in required_fields):
            return jsonify({'success': False, 'error': 'Faltan campos requeridos'})
            
        # Crear instancia según tipo de exchange
        if data['exchange_type'] == 'oanda':
            from app.models.exchanges.oanda_exchange import OandaExchange
            exchange = OandaExchange(
                name='OANDA',
                exchange_type='oanda',
                api_key=data['api_key'],
                account_id=data['account_id'],
                user_id=current_user.id
            )
        elif data['exchange_type'] in ['binance', 'bingx']:
            from app.models.crypto_exchange import CryptoExchange
            exchange = CryptoExchange(
                name=data['exchange_type'].upper(),
                exchange_type=data['exchange_type'],
                api_key=data['api_key'],
                user_id=current_user.id
            )
        else:
            return jsonify({
                'success': False,
                'error': f'Tipo de exchange no soportado: {data["exchange_type"]}'
            }), 400
        
        # Encriptar y guardar API secret
        success, error = exchange.set_api_secret(data['api_secret'])
        if not success:
            return jsonify({'success': False, 'error': error})
            
        # Guardar en base de datos
        db.session.add(exchange)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Exchange agregado correctamente'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@exchanges_bp.route('/exchanges/delete/<int:exchange_id>', methods=['POST'])
@login_required
def delete_exchange(exchange_id):
    """Delete an exchange connection."""
    exchange = BaseExchange.query.filter_by(id=exchange_id, user_id=current_user.id).first()
    
    if not exchange:
        return jsonify({'success': False, 'error': 'Exchange not found'}), 404
        
    try:
        db.session.delete(exchange)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@exchanges_bp.route('/api/exchanges/update', methods=['POST'])
@login_required
def update_exchange():
    """Update exchange configuration."""
    data = request.get_json()
    exchange_id = data.get('exchange_id')
    
    if not exchange_id:
        return jsonify({'success': False, 'error': 'Exchange ID is required'}), 400
        
    exchange = BaseExchange.query.filter_by(id=exchange_id, user_id=current_user.id).first()
    
    if not exchange:
        return jsonify({'success': False, 'error': 'Exchange not found'}), 404
        
    try:
        # Update basic settings
        exchange.trading_enabled = data.get('trading_enabled', exchange.trading_enabled)
        exchange.max_positions = data.get('max_positions', exchange.max_positions)
        exchange.max_leverage = data.get('max_leverage', exchange.max_leverage)
        exchange.min_order_size = data.get('min_order_size', exchange.min_order_size)
        exchange.max_order_size = data.get('max_order_size', exchange.max_order_size)
        
        # Update API credentials if provided
        new_api_key = data.get('api_key')
        new_api_secret = data.get('api_secret')
        new_account_id = data.get('account_id')
        
        if new_api_key:
            exchange.api_key = new_api_key
        if new_api_secret:
            exchange.set_api_secret(new_api_secret)
        if new_account_id and hasattr(exchange, 'account_id'):
            exchange.account_id = new_account_id
            
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500