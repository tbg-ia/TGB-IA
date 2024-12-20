"""
Initialize models package.
Import all models here to make them available to the application.
"""
from app.models.role import Role
from app.models.permission import Permission
from app.models.subscription_plan import SubscriptionPlan
from app.models.exchange_permission import ExchangePermission
from app.models.user import User
from app.models.subscription import Subscription
from app.models.payment import Payment
from app.models.base_exchange import BaseExchange
from app.models.exchange_credential import ExchangeCredential
from app.models.exchange_settings import ExchangeSettings
from app.models.crypto_exchange import CryptoExchange
from app.models.forex_exchange import ForexExchange
from app.models.exchanges.binance_exchange import BinanceExchange
from app.models.exchanges.bingx_exchange import BingXExchange
from app.models.exchanges.oanda_exchange import OandaExchange
from app.models.trading_bot import TradingBot
from app.models.trade import Trade

# Export all models
__all__ = [
    'Role',
    'Permission',
    'SubscriptionPlan',
    'ExchangePermission',
    'User',
    'Subscription',
    'Payment',
    'BaseExchange',
    'ExchangeCredential',
    'ExchangeSettings',
    'CryptoExchange',
    'ForexExchange',
    'BinanceExchange',
    'BingXExchange',
    'OandaExchange',
    'TradingBot',
    'Trade'
]
