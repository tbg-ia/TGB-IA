from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.base_exchange import BaseExchange
from app.models.forex_exchange import ForexExchange
from app.integrations.forex.oanda_client import OandaClient

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
