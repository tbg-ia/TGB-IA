"""
Initialize the routes package.
This module serves as an entry point for all route blueprints.
"""
from flask import Blueprint

# Import all blueprints
from .auth import auth_bp
from .admin import admin_bp
from .user import user_bp
from .crypto import crypto_bp
from app.billing import billing_bp
from .subscription import subscription_bp

# List of all blueprints to be registered
all_blueprints = [
    auth_bp,
    admin_bp,
    user_bp,
    crypto_bp,
    billing_bp,
    subscription_bp
]
