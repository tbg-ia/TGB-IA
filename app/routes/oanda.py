
from flask import Blueprint, request, jsonify
import requests
import json
import logging
import os
from dotenv import load_dotenv
from flask_login import login_required, current_user
from app.integrations.forex.oanda_client import OandaClient

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

@oanda_bp.route('/account/info', methods=['GET'])
@login_required
def get_account_info():
    """Obtener información de la cuenta"""
    client = OandaClient.get_instance()
    info = client.get_account_info()
    if info:
        return jsonify(info)
    return jsonify({'error': 'No se pudo obtener la información de la cuenta'}), 400

@oanda_bp.route('/market/price/<instrument>', methods=['GET'])
@login_required
def get_market_price(instrument):
    """Obtener precio actual del instrumento"""
    client = OandaClient.get_instance()
    price = client.get_price(instrument)
    if price:
        return jsonify({'price': price})
    return jsonify({'error': 'No se pudo obtener el precio'}), 400

@oanda_bp.route('/orders', methods=['GET', 'POST'])
@login_required
def handle_orders():
    """Manejar órdenes de trading"""
    client = OandaClient.get_instance()
    
    if request.method == 'GET':
        orders = client.get_open_orders()
        return jsonify(orders)
        
    # POST - Nueva orden
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se proporcionaron datos'}), 400
        
    symbol = data.get('symbol')
    side = data.get('side')
    units = data.get('units')
    price = data.get('price', None)
    
    if not all([symbol, side, units]):
        return jsonify({'error': 'Faltan campos requeridos'}), 400
        
    result = client.place_order(
        symbol=symbol,
        side=side,
        units=units,
        price=price
    )
    
    if result:
        return jsonify(result)
    return jsonify({'error': 'No se pudo colocar la orden'}), 400
