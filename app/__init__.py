import os
from flask import Flask
from flask import render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from .extensions import db

from app.billing import billing_bp
from app.routes.subscription import subscription_bp
from app.routes.auth import auth_bp
from app.routes.user import user_bp
from app.routes.admin import admin_bp

all_blueprints = [
    billing_bp,
    subscription_bp,
    auth_bp,
    user_bp,
    admin_bp
]

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
    
    # Stripe Configuration
    app.config['STRIPE_PUBLIC_KEY'] = os.environ.get('STRIPE_PUBLIC_KEY')
    app.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY')
    app.config['STRIPE_WEBHOOK_SECRET'] = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
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
    migrate = Migrate(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'

    # Initialize exchange integrations
    from app.integrations.crypto.binance_client import init_binance
    from app.integrations.crypto.bingx_client import init_bingx
    from app.integrations.forex.oanda_client import init_oanda
    
    init_binance(app)
    init_bingx(app)
    init_oanda(app)
    
    # Initialize mail
    from app.mail import init_app as init_mail
    init_mail(app)

    # Register blueprints
    from app.routes import all_blueprints
    from app.api.exchanges import exchanges_bp as api_exchanges_bp
    from app.routes.exchanges import exchanges_bp
    from app.routes.oanda import oanda_bp

    # Register core blueprints first
    print("Registering blueprints...")
    for blueprint in all_blueprints:
        print(f"Registering blueprint: {blueprint.name}")
        app.register_blueprint(blueprint)
        
    # Register API blueprints
    app.register_blueprint(api_exchanges_bp)
    app.register_blueprint(exchanges_bp)
    app.register_blueprint(oanda_bp, url_prefix='/api/oanda')

    
    # Register index route
    @app.route('/')
    def index():
        return render_template('public/index.html')

    with app.app_context():
        # Import all models
        from app.models.role import Role
        from app.models.user import User
        from app.models.base_exchange import BaseExchange
        from app.models.crypto_exchange import CryptoExchange
        from app.models.forex_exchange import ForexExchange
        from app.models.exchanges.binance_exchange import BinanceExchange
        from app.models.exchanges.bingx_exchange import BingXExchange
        from app.models.exchanges.oanda_exchange import OandaExchange
        from app.models.trading_bot import TradingBot
        from app.models.trade import Trade
        from app.models.subscription import Subscription
        
        db.create_all()
        
        # Initialize roles
        Role.insert_roles()

    return app