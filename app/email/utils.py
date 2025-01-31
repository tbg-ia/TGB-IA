from flask import current_app, render_template
from threading import Thread
from . import mail
from flask_mail import Message

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    
    Thread(target=send_async_email,
           args=(current_app._get_current_object(), msg)).start()
