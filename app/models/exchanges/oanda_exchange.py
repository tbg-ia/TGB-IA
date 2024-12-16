from app import db
from app.models.forex_exchange import ForexExchange

class OandaExchange(ForexExchange):
    """Modelo específico para OANDA"""
    __mapper_args__ = {
        'polymorphic_identity': 'oanda'
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'OANDA'
        self.margin_rate = 0.02  # Margen específico de OANDA
        self.max_leverage = 30  # Leverage máximo de OANDA
        
    def validate_credentials(self):
        """Valida que las credenciales de OANDA estén completas y sean correctas"""
        if not self.api_key:
            return False, "API Key de OANDA es requerida"
        if not self.account_id:
            return False, "Account ID de OANDA es requerido"
        
        from app.integrations.forex.oanda_client import OandaClient
        client = OandaClient.get_instance()
        
        if client.init_client(self.api_key, self.account_id):
            return True, None
        else:
            return False, "No se pudo conectar con OANDA. Verifique sus credenciales."
