from flask import render_template, current_app
from flask_mail import Message
from app.mail import mail
from threading import Thread

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, template, **kwargs):
    """
    Envía un correo electrónico usando una plantilla HTML
    """
    msg = Message(subject, recipients=recipients)
    msg.html = render_template(f'mail/{template}', **kwargs)
    
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

def send_welcome_email(user):
    """
    Envía el correo de bienvenida a un nuevo usuario
    """
    send_email(
        'Bienvenido a Crypto Trading Platform',
        [user.email],
        'welcome.html',
        user=user
    )

def send_reset_password_email(user, token):
    """
    Envía el correo para restablecer la contraseña
    """
    send_email(
        'Restablecer Contraseña',
        [user.email],
        'reset_password.html',
        user=user,
        token=token
    )

def send_trade_notification(user, trade):
    """
    Envía una notificación sobre una operación de trading
    """
    send_email(
        'Notificación de Trading',
        [user.email],
        'notification.html',
        user=user,
        trade=trade
    )
