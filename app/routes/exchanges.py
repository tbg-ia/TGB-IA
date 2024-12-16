from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app import db
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
    """Add a new exchange connection."""
    data = request.get_json()
    exchange_type = data.get('exchange_type')
    api_key = data.get('api_key')
    
    if not exchange_type or not api_key:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    try:
        if exchange_type == 'oanda':
            account_id = data.get('account_id')
            if not account_id:
                return jsonify({'success': False, 'error': 'OANDA Account ID is required'}), 400
                
            exchange = OandaExchange(
                user_id=current_user.id,
                api_key=api_key,
                account_id=account_id,
                name='OANDA',
                exchange_type='oanda',
                is_forex=True
            )
            
        elif exchange_type == 'binance':
            api_secret = data.get('api_secret')
            if not api_secret:
                return jsonify({'success': False, 'error': 'API Secret is required'}), 400
                
            exchange = BinanceExchange(
                user_id=current_user.id,
                api_key=api_key,
                name='Binance',
                exchange_type='binance'
            )
            exchange.set_api_secret(api_secret)
            
        elif exchange_type == 'bingx':
            api_secret = data.get('api_secret')
            if not api_secret:
                return jsonify({'success': False, 'error': 'API Secret is required'}), 400
                
            exchange = BingXExchange(
                user_id=current_user.id,
                api_key=api_key,
                name='BingX',
                exchange_type='bingx'
            )
            exchange.set_api_secret(api_secret)
            
        else:
            return jsonify({'success': False, 'error': 'Invalid exchange type'}), 400
        
        db.session.add(exchange)
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

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
