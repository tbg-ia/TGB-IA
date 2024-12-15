from app.mail.utils import send_trade_notification
from app.models.user import User
from app.models.trade import Trade
from datetime import datetime, timedelta

def send_daily_summary():
    """
    Envía un resumen diario de las operaciones a los usuarios
    """
    yesterday = datetime.utcnow() - timedelta(days=1)
    users = User.query.filter_by(subscription_type='pro').all()
    
    for user in users:
        trades = Trade.query.filter(
            Trade.user_id == user.id,
            Trade.created_at >= yesterday
        ).all()
        
        if trades:
            send_trade_notification(user, trades)

def process_email_queue():
    """
    Procesa la cola de correos pendientes
    """
    # Implementar lógica de cola de correos si es necesario
    pass
