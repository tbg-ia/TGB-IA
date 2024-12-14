from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models.trading_bot import TradingBot, Trade

crypto_bp = Blueprint('crypto', __name__)

@crypto_bp.route('/dashboard')
@login_required
def dashboard():
    bots = TradingBot.query.filter_by(user_id=current_user.id).all()
    return render_template('admin/dashboard.html', bots=bots)

@crypto_bp.route('/bot/create', methods=['POST'])
@login_required
def create_bot():
    # Bot creation logic
    pass

@crypto_bp.route('/bot/<int:bot_id>/trades')
@login_required
def bot_trades(bot_id):
    trades = Trade.query.filter_by(bot_id=bot_id).order_by(Trade.timestamp.desc()).limit(100)
    return jsonify([{
        'type': trade.type,
        'price': trade.price,
        'amount': trade.amount,
        'timestamp': trade.timestamp
    } for trade in trades])
