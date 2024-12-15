import os
import logging
from flask_mail import Mail

logger = logging.getLogger(__name__)

class EmailConfig:
    def __init__(self):
        """Initialize email configuration."""
        self.mail = None
        logger.info("Email configuration initialized")
    
    def init_mail(self, app):
        """Initialize Flask-Mail with the current application context."""
        try:
            if not self.mail:
                self.mail = Mail()
            
            # Get configuration from environment
            app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
            app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
            app.config['MAIL_USE_TLS'] = True
            app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
            app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
            app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
            
            # Validate required settings
            required_settings = ['MAIL_SERVER', 'MAIL_USERNAME', 'MAIL_PASSWORD']
            missing_settings = [setting for setting in required_settings if not app.config.get(setting)]
            
            if missing_settings:
                raise ValueError(f"Missing required email settings: {', '.join(missing_settings)}")
            
            # Initialize mail with app
            self.mail.init_app(app)
            logger.info("Flask-Mail initialized successfully")
            return self.mail
            
        except Exception as e:
            logger.error(f"Error initializing Flask-Mail: {str(e)}")
            raise

# Create global instance
email_config = EmailConfig()
