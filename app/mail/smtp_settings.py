import os
import logging
from . import mail

logger = logging.getLogger(__name__)

class EmailConfig:
    def __init__(self):
        """Initialize email configuration."""
        logger.info("Email configuration initialized")
    
    def init_mail(self, app):
        """Initialize Flask-Mail with the current application context."""
        try:
            
            # Configuración directa desde variables de entorno
            config = {
                'MAIL_SERVER': os.environ.get('MAIL_SERVER'),
                'MAIL_PORT': int(os.environ.get('MAIL_PORT', 587)),
                'MAIL_USE_TLS': True,
                'MAIL_USERNAME': os.environ.get('MAIL_USERNAME'),
                'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD'),
                'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER'),
                'MAIL_USE_SSL': False,
                'MAIL_MAX_EMAILS': None,
                'MAIL_ASCII_ATTACHMENTS': False
            }
            
            # Validar configuración requerida
            required = ['MAIL_SERVER', 'MAIL_USERNAME', 'MAIL_PASSWORD']
            missing = [key for key in required if not config.get(key)]
            if missing:
                raise ValueError(f"Faltan configuraciones requeridas: {', '.join(missing)}")
            
            # Actualizar configuración de la aplicación
            app.config.update(config)
            
            # Inicializar Mail con la aplicación
            mail.init_app(app)
            
            # Verificar conexión
            with mail.connect() as conn:
                logger.info(f"Conexión SMTP establecida con {config['MAIL_SERVER']}:{config['MAIL_PORT']}")
            
            return mail
            
        except Exception as e:
            logger.error(f"Error initializing Flask-Mail: {str(e)}")
            raise

# Create global instance
email_config = EmailConfig()