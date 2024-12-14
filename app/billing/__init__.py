from flask import Blueprint

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')

from . import routes  # noqa

# Initialize the blueprint
__all__ = ['billing_bp']
