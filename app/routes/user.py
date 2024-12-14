from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from app.models.trading_bot import TradingBot, Trade
from app import db

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    return render_template('public/user_dashboard.html')

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

@user_bp.route('/subscription')
@login_required
def subscription():
    return render_template('public/planes.html')
