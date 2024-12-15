"""
Initialize the email package.
"""
from flask_mail import Mail

mail = Mail()

def init_app(app):
    """Initialize mail extension with app."""
    mail.init_app(app)

from . import utils, tasks
