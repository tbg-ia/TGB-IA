import os
import os
from flask import Flask
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    }
    
    # Email configuration
    app.config.update(
        MAIL_SERVER=os.environ.get('MAIL_SERVER'),
        MAIL_PORT=int(os.environ.get('MAIL_PORT', 587)),
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
        MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER')
    )

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Initialize mail
    from app.mail import init_app as init_mail
    init_mail(app)

    # Register blueprints
    from app.routes import all_blueprints
    from app.api.exchanges import exchanges_bp as api_exchanges_bp
    from app.routes.exchanges import exchanges_bp
    
    for blueprint in all_blueprints:
        app.register_blueprint(blueprint)
    app.register_blueprint(api_exchanges_bp)
    app.register_blueprint(exchanges_bp)
    
    # Register index route
    @app.route('/')
    def index():
        return render_template('public/index.html')

    with app.app_context():
        # Import models
        from app.models.role import Role
        from app.models.exchange import Exchange  # Import Exchange model
        
        db.create_all()
        
        # Initialize roles
        Role.insert_roles()

    return app
