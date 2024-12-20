import os
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from flask_login import login_required, current_user
from app.models.base_exchange import BaseExchange
from app.models.trading_bot import TradingBot
from app.models.trade import Trade
from app.models.user import User
from app.models.system_config import SystemConfig
from app.integrations.crypto.bingx_client import BingXClient
from app.auth.decorators import admin_required
from app import db
from datetime import datetime

crypto_bp = Blueprint('crypto', __name__)

@crypto_bp.route('/terminal')
@login_required
def terminal():
    from app.models.base_exchange import BaseExchange
    
    # Obtener los exchanges activos del usuario (BingX y OANDA)
    user_exchanges = BaseExchange.query.filter(
        BaseExchange.user_id == current_user.id,
        BaseExchange.is_active == True,
        BaseExchange.exchange_type.in_(['bingx', 'oanda'])
    ).all()
    
    # Obtener el balance de cada exchange
    exchange_balances = {}
    for exchange in user_exchanges:
        try:
            if exchange.exchange_type == 'bingx':
                from app.integrations.crypto.bingx_client import BingXClient
                client = BingXClient.get_instance()
                balance = client.get_account_balance()
                exchange_balances[exchange.id] = {
                    'balance': float(balance.get('balance', 0)),
                    'currency': 'USDT'
                }
            elif exchange.exchange_type == 'oanda':
                from app.integrations.forex.oanda_client import OandaClient
                client = OandaClient.get_instance()
                account_info = client.get_account_info()
                exchange_balances[exchange.id] = {
                    'balance': float(account_info.get('balance', 0)),
                    'currency': 'USD'
                }
        except Exception as e:
            current_app.logger.error(f"Error getting balance for exchange {exchange.id}: {str(e)}")
            exchange_balances[exchange.id] = {
                'balance': 0.0,
                'currency': 'USD' if exchange.exchange_type == 'oanda' else 'USDT'
            }
    
    return render_template('public/terminal.html', 
                         exchanges=user_exchanges,
                         balances=exchange_balances)

@crypto_bp.route('/exchanges')
@login_required
def exchanges():
    # Aquí podríamos obtener la lista de exchanges configurados para el usuario
    exchanges = []  # TODO: Obtener exchanges de la base de datos
    return render_template('public/exchanges.html', exchanges=exchanges)

@crypto_bp.route('/signalbot', methods=['GET', 'POST'])
@login_required
def signalbot():
    bot = TradingBot.query.filter_by(user_id=current_user.id).first()
    if not bot:
        bot = TradingBot(user_id=current_user.id)
        db.session.add(bot)
        db.session.commit()
    
    exchange = BaseExchange.query.filter_by(user_id=current_user.id, is_active=True).first()
    account_balance = 0
    
    if exchange:
        try:
            if exchange.exchange_type == 'bingx':
                client = BingXClient.get_instance()
                balance = client.get_account_balance()
                account_balance = float(balance.get('balance', 0))
        except Exception as e:
            current_app.logger.error(f"Error getting balance: {str(e)}")
    
    return render_template('public/signal_bot.html', bot=bot, account_balance=account_balance)

@crypto_bp.route('/subscription/plans')
def plans():
    return redirect(url_for('subscription.planes'))

@crypto_bp.route('/user-dashboard')
@login_required
def user_dashboard():
    return render_template('public/user_dashboard.html')

@crypto_bp.route('/resources')
@login_required
def resources():
    return render_template('public/resources.html')

@crypto_bp.route('/exchange-connection')
@login_required
def exchange_connection():
    return render_template('public/exchange_connection.html')
@crypto_bp.route('/support')
@login_required
def support():
    return render_template('public/support.html')

@crypto_bp.route('/bot/<int:bot_id>/trades')
@login_required
def get_bot_trades(bot_id):
    trades = Trade.query.filter_by(bot_id=bot_id).order_by(Trade.timestamp.desc()).limit(50).all()
    return jsonify([{
        'type': trade.type,
        'price': trade.price,
        'amount': trade.amount,
        'timestamp': trade.timestamp.isoformat()
    } for trade in trades])

# Rutas administrativas
@crypto_bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@crypto_bp.route('/admin/users/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'subscription_type': user.subscription_type,
        'subscription_expires': user.subscription_expires.strftime('%Y-%m-%d') if user.subscription_expires else None
    })

@crypto_bp.route('/admin/users/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    user.subscription_type = request.form.get('subscription_type')
    expires_str = request.form.get('subscription_expires')
    if expires_str:
        user.subscription_expires = datetime.strptime(expires_str, '%Y-%m-%d')
    db.session.commit()
    return jsonify({'success': True})

@crypto_bp.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({'success': True})

@crypto_bp.route('/admin/config')
@login_required
@admin_required
def admin_config():
    configs = SystemConfig.query.order_by(SystemConfig.category, SystemConfig.key).all()
    return render_template('admin/config.html', configs=configs)

@crypto_bp.route('/api/trading/place-order', methods=['POST'])
@login_required
def place_order():
    data = request.get_json()
    exchange_id = data.get('exchange_id')
    symbol = data.get('symbol')
    side = data.get('side')
    amount = data.get('amount')
    price = data.get('price')
    order_type = data.get('type', 'MARKET')
    
    if not all([exchange_id, symbol, side, amount]):
        return jsonify({'success': False, 'error': 'Faltan parámetros requeridos'}), 400
        
    exchange = BaseExchange.query.get(exchange_id)
    if not exchange or exchange.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Exchange no encontrado'}), 404
        
    try:
        if exchange.exchange_type == 'bingx':
            from app.integrations.crypto.bingx_client import BingXClient
            client = BingXClient.get_instance()
            order = client.place_order(symbol=symbol, side=side, quantity=amount, price=price, order_type=order_type)
        elif exchange.exchange_type == 'oanda':
            from app.integrations.forex.oanda_client import OandaClient
            client = OandaClient.get_instance()
            order = client.place_order(symbol=symbol, side=side, units=amount, price=price)
            
        if order:
            return jsonify({'success': True, 'order': order})
        return jsonify({'success': False, 'error': 'Error al ejecutar la orden'}), 400
        
    except Exception as e:
        current_app.logger.error(f"Error placing order: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@crypto_bp.route('/api/trading/orderbook')
@login_required
def get_orderbook():
    exchange_id = request.args.get('exchange_id')
    symbol = request.args.get('symbol')
    
    if not exchange_id or not symbol:
        return jsonify({'success': False, 'error': 'Faltan parámetros requeridos'}), 400
        
    exchange = BaseExchange.query.get(exchange_id)
    if not exchange or exchange.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Exchange no encontrado'}), 404
        
    try:
        orderbook = {'asks': [], 'bids': []}
        
        if exchange.exchange_type == 'bingx':
            from app.integrations.crypto.bingx_client import BingXClient
            client = BingXClient.get_instance()
            depth = client.get_orderbook(symbol)
            if depth:
                orderbook['asks'] = depth.get('asks', [])[:10]
                orderbook['bids'] = depth.get('bids', [])[:10]
        elif exchange.exchange_type == 'oanda':
            from app.integrations.forex.oanda_client import OandaClient
            client = OandaClient.get_instance()
            book = client.get_orderbook(symbol)
            if book:
                orderbook['asks'] = [[p, s] for p, s in book.get('asks', [])][:10]
                orderbook['bids'] = [[p, s] for p, s in book.get('bids', [])][:10]
                
        return jsonify(orderbook)
        
    except Exception as e:
        current_app.logger.error(f"Error getting orderbook: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@crypto_bp.route('/api/trading/open-orders')
@login_required
def get_open_orders():
    exchange_id = request.args.get('exchange_id')
    
    if not exchange_id:
        return jsonify({'success': False, 'error': 'Falta ID del exchange'}), 400
        
    exchange = BaseExchange.query.get(exchange_id)
    if not exchange or exchange.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Exchange no encontrado'}), 404
        
    try:
        orders = []
        
        if exchange.exchange_type == 'bingx':
            from app.integrations.crypto.bingx_client import BingXClient
            client = BingXClient.get_instance()
            orders = client.get_open_orders()
        elif exchange.exchange_type == 'oanda':
            from app.integrations.forex.oanda_client import OandaClient
            client = OandaClient.get_instance()
            orders = client.get_open_orders()
            
        return jsonify({'orders': orders})
        
    except Exception as e:
        current_app.logger.error(f"Error getting open orders: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400
@crypto_bp.route('/admin/config/<int:config_id>')
@login_required
@admin_required
def get_config(config_id):
    config = SystemConfig.query.get_or_404(config_id)
    return jsonify({
        'key': config.key,
        'value': config.value,
        'category': config.category,
        'description': config.description
    })

@crypto_bp.route('/admin/config/save', methods=['POST'])
@login_required
@admin_required
def save_config():
    key = request.form.get('key')
    value = request.form.get('value')
    category = request.form.get('category')
    description = request.form.get('description')
    
@crypto_bp.route('/signalbot/save', methods=['POST'])
@login_required
def save_bot_config():
    bot = TradingBot.query.filter_by(user_id=current_user.id).first()
    if not bot:
        bot = TradingBot(user_id=current_user.id)
        db.session.add(bot)
    
    bot.name = request.form.get('name')
    bot.strategy = request.form.get('strategy')
    bot.trading_pair = request.form.get('trading_pair')
    bot.interval = request.form.get('interval')
    bot.max_position = float(request.form.get('max_position', 0))
    bot.leverage = int(request.form.get('leverage', 1))
    bot.margin_type = request.form.get('margin_type')
    bot.stop_loss = float(request.form.get('stop_loss', 0))
    bot.take_profit = float(request.form.get('take_profit', 0))
    bot.active = 'active' in request.form
    
    db.session.commit()
    flash('Configuración del bot guardada correctamente', 'success')
    return redirect(url_for('crypto.signalbot'))
    
    config = SystemConfig.set_value(
        key=key,
        value=value,
        category=category,
        description=description,
        user_id=current_user.id
    )
    
    return jsonify({'success': True})