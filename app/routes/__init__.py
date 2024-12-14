"""
Initialize the routes package.
This module serves as an entry point for all route blueprints.
"""
from flask import Blueprint

# Import all blueprints
from .auth import auth_bp
from .crypto import crypto_bp

# List of all blueprints to be registered
all_blueprints = [
    auth_bp,
    crypto_bp
]
