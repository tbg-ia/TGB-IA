import os
from flask_mail import Mail

class EmailConfig:
    _instance = None
    mail = Mail()
    
    def __init__(self):
        self.MAIL_SERVER = os.environ.get('MAIL_SERVER', 'us2.smtp.mailhostbox.com')
        self.MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
        self.MAIL_USE_TLS = True
        self.MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'support@bitxxo.com')
        self.MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
        self.MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'support@bitxxo.com')
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def init_app(cls, app):
        config = cls.get_instance()
        app.config.update(
            MAIL_SERVER=config.MAIL_SERVER,
            MAIL_PORT=config.MAIL_PORT,
            MAIL_USE_TLS=config.MAIL_USE_TLS,
            MAIL_USERNAME=config.MAIL_USERNAME,
            MAIL_PASSWORD=config.MAIL_PASSWORD,
            MAIL_DEFAULT_SENDER=config.MAIL_DEFAULT_SENDER
        )
        cls.mail.init_app(app)
        return cls.mail
