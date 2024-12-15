import os
import logging
from flask_mail import Mail

logger = logging.getLogger(__name__)

class EmailConfig:
    def __init__(self):
        """Initialize email configuration from environment variables."""
        self.config = {
            'MAIL_SERVER': os.environ.get('MAIL_SERVER', 'us2.smtp.mailhostbox.com'),
            'MAIL_PORT': int(os.environ.get('MAIL_PORT', 587)),
            'MAIL_USE_TLS': True,
            'MAIL_USERNAME': os.environ.get('MAIL_USERNAME', 'support@bitxxo.com'),
            'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD', ''),
            'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER', 'support@bitxxo.com')
        }
        self.mail = None
        logger.info("Email configuration initialized")
    
    def init_mail(self, app):
        """Initialize Flask-Mail with the current application context."""
        try:
            if not self.mail:
                self.mail = Mail()
            
            # Update app config
            app.config.update(self.config)
            
            # Initialize mail with app
            self.mail.init_app(app)
            logger.info("Flask-Mail initialized successfully")
            return self.mail
        except Exception as e:
            logger.error(f"Error initializing Flask-Mail: {str(e)}")
            raise

# Create global instance
email_config = EmailConfig()
