from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.base_exchange import BaseExchange
from app.models.exchanges.binance_exchange import BinanceExchange
from app.models.exchanges.bingx_exchange import BingXExchange
from app.models.exchanges.oanda_exchange import OandaExchange
from app import db

exchanges_bp = Blueprint('exchanges_routes', __name__)

@exchanges_bp.route('/exchanges')
@login_required
def list_exchanges():
    """Display the exchanges page with connected APIs."""
    exchanges = BaseExchange.query.filter_by(user_id=current_user.id).all()
    return render_template('public/exchanges.html', exchanges=exchanges)

@exchanges_bp.route('/exchanges/add', methods=['POST'])
@login_required
def add_exchange():
    """Add a new exchange connection."""
    exchange_type = request.form.get('exchange_type')
    api_key = request.form.get('api_key')
    api_secret = request.form.get('api_secret')
    
    if not all([exchange_type, api_key, api_secret]):
        flash('Please fill in all fields', 'error')
        return redirect(url_for('exchanges_routes.list_exchanges'))
    
    try:
        if exchange_type == 'binance':
            exchange = BinanceExchange(
                user_id=current_user.id,
                api_key=api_key
            )
        elif exchange_type == 'bingx':
            exchange = BingXExchange(
                user_id=current_user.id,
                api_key=api_key
            )
        elif exchange_type == 'oanda':
            account_id = request.form.get('account_id')
            if not account_id:
                flash('Account ID is required for OANDA', 'error')
                return redirect(url_for('exchanges_routes.list_exchanges'))
                
            exchange = OandaExchange(
                user_id=current_user.id,
                api_key=api_key,
                account_id=account_id
            )
        else:
            flash('Invalid exchange type', 'error')
            return redirect(url_for('exchanges_routes.list_exchanges'))
        
        exchange.set_api_secret(api_secret)
        db.session.add(exchange)
        db.session.commit()
        flash('Exchange added successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding exchange: {str(e)}', 'error')
        
    return redirect(url_for('exchanges_routes.list_exchanges'))
