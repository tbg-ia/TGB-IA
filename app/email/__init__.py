"""
Initialize the email package.
Handles all email-related functionality.
"""
from flask_mail import Mail, Message

mail = Mail()

def init_mail(app):
    mail.init_app(app)
