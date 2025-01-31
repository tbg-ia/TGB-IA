from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models.base_exchange import BaseExchange
from app.models.forex_exchange import ForexExchange
from app.models.trading_bot import TradingBot
from app.integrations.forex.oanda_client import OandaClient
from app import db
import logging

logger = logging.getLogger(__name__)
terminal_bp = Blueprint('terminal', __name__)

@terminal_bp.route('/terminal')
@login_required
def trading_terminal():
    """Trading terminal view"""
    # Get user's exchanges
    exchanges = BaseExchange.query.filter_by(user_id=current_user.id).all()
    
    # Get balances for each exchange
    balances = {}
    for exchange in exchanges:
        if isinstance(exchange, ForexExchange):
            client = OandaClient.get_instance()
            if client:
                account_info = client.get_account_info()
                if account_info:
                    balances[exchange.id] = account_info.get('balance', 0.0)
        else:
            balances[exchange.id] = 0.0  # Para otros tipos de exchange
            
    return render_template('public/terminal.html', 
                         exchanges=exchanges,
                         balances=balances)

@terminal_bp.route('/terminal/forex')
@login_required
def forex_terminal():
    """Forex trading terminal view"""
    return render_template('public/forex_terminal.html')

@terminal_bp.route('/terminal/bot')
@login_required
def forex_bot():
    """Forex bot configuration view"""
    # Get active forex exchange
    exchange = ForexExchange.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()
    
    # Get or create bot config for current user
    bot = TradingBot.query.filter_by(user_id=current_user.id).first()
    if not bot and exchange:
        bot = TradingBot(
            user_id=current_user.id,
            exchange_id=exchange.id,
            name="Forex Bot",
            strategy="trend_following"
        )
        db.session.add(bot)
        db.session.commit()
    
    return render_template('terminal/signal_bot.html', bot=bot or TradingBot())

@terminal_bp.route('/terminal/forex/bot/save', methods=['POST'])
@login_required
def save_forex_bot_config():
    """Save forex bot configuration"""
    return jsonify({'success': True})

@terminal_bp.route('/terminal/crypto')
@login_required
def crypto_terminal():
    """Crypto trading terminal view"""
    return render_template('public/crypto_terminal.html')
    """Forex trading terminal view"""
    return render_template('public/forex_terminal.html')
    
    balances = {}
    for exchange in forex_exchanges:
        client = OandaClient.get_instance()
        if client:
            account_info = client.get_account_info()
            if account_info:
                balances[exchange.id] = account_info.get('balance', 0.0)
    # Get user's forex exchanges
    forex_exchanges = ForexExchange.query.filter_by(user_id=current_user.id).all()
    
    # Get balances for forex exchanges
    balances = {}
    for exchange in forex_exchanges:
        client = OandaClient.get_instance()
        if client:
            account_info = client.get_account_info()
            if account_info:
                balances[exchange.id] = account_info.get('balance', 0.0)
    
    return render_template('public/forex_terminal.html',
                         exchanges=forex_exchanges,
                         balances=balances)

@terminal_bp.route('/api/forex/balance')
@login_required
def get_forex_balance():
    """Get forex account balance"""
    client = OandaClient.get_instance()
    if client:
        account_info = client.get_account_info()
        if account_info:
            return jsonify({
                'success': True,
                'balance': account_info.get('balance', 0.0),
                'currency': account_info.get('currency', 'USD')
            })
    return jsonify({'success': False, 'error': 'No se pudo obtener el balance'})

@terminal_bp.route('/api/forex/positions')
@login_required
def get_forex_positions():
    """Get active forex positions"""
    client = OandaClient.get_instance()
    if client:
        return jsonify({
            'success': True,
            'positions': []  # Implementar obtención de posiciones
        })
    return jsonify({'success': False, 'error': 'No se pudo obtener las posiciones'})

@terminal_bp.route('/api/forex/order', methods=['POST'])
@login_required
def place_forex_order():
    """Place a forex order"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No se proporcionaron datos'})
        
    client = OandaClient.get_instance()
    if not client:
        return jsonify({'success': False, 'error': 'Cliente OANDA no inicializado'})
        
    try:
        result = client.place_order(
            symbol=data.get('symbol'),
            side=data.get('side'),
            units=int(data.get('units')),
            price=None  # Market order
        )
        
        if result:
            return jsonify({'success': True, 'order': result})
        return jsonify({'success': False, 'error': 'Error al colocar la orden'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
    client = OandaClient.get_instance()
    if not client:
        return jsonify({'success': False, 'error': 'Cliente OANDA no inicializado'})
        
    try:
        # Place the order using OANDA client
        result = client.place_order(
            symbol=data.get('instrument'),
            side=data.get('side'),
            units=data.get('units'),
            price=data.get('price')
        )
        
        if result:
            return jsonify({'success': True, 'order': result})
        return jsonify({'success': False, 'error': 'Error al colocar la orden'})
        
    except Exception as e:
        logger.error(f"Error placing forex order: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@terminal_bp.route('/api/forex/position/<position_id>/close', methods=['POST'])
@login_required
def close_forex_position(position_id):
    """Close a forex position"""
    client = OandaClient.get_instance()
    if client:
        # Implementar cierre de posición
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'No se pudo cerrar la posición'})