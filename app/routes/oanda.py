
from flask import Blueprint, request, jsonify
import requests
import json
import logging
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

# Crear Blueprint
oanda_bp = Blueprint('oanda', __name__)

# Configuración de OANDA API
API_URL = "https://api-fxtrade.oanda.com/v3"
API_KEY = os.getenv("OANDA_API_KEY")
ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")

# Configuración de Trailing Stop
TRAILING_STOP_PIPS = int(os.getenv("TRAILING_STOP_PIPS", 20))

@oanda_bp.before_request
def validate_config():
    if not API_KEY or not ACCOUNT_ID:
        return jsonify({
            'error': 'Las variables de entorno OANDA_API_KEY y OANDA_ACCOUNT_ID deben estar configuradas.'
        }), 400
