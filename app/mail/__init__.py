from flask_mail import Mail
from app import app

mail = Mail(app)

from . import utils, tasks
