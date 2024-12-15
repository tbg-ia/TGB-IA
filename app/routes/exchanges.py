from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.exchange import Exchange

exchanges_bp = Blueprint('exchanges_routes', __name__)

@exchanges_bp.route('/exchanges')
@login_required
def list_exchanges():
    """Display the exchanges page with connected APIs."""
    exchanges = Exchange.query.filter_by(user_id=current_user.id).all()
    return render_template('public/exchanges.html', exchanges=exchanges)
