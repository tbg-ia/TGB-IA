import os

class EmailConfig:
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@bitxxo.com')
    
    @staticmethod
    def init_app(app):
        app.config.update(
            MAIL_SERVER=EmailConfig.MAIL_SERVER,
            MAIL_PORT=EmailConfig.MAIL_PORT,
            MAIL_USE_TLS=EmailConfig.MAIL_USE_TLS,
            MAIL_USERNAME=EmailConfig.MAIL_USERNAME,
            MAIL_PASSWORD=EmailConfig.MAIL_PASSWORD,
            MAIL_DEFAULT_SENDER=EmailConfig.MAIL_DEFAULT_SENDER
        )
