import os

class Config:
    BINANCE_API_KEY = os.environ.get('BINANCE_API_KEY', '')
    BINANCE_API_SECRET = os.environ.get('BINANCE_API_SECRET', '')
    
    # Subscription plans
    SUBSCRIPTION_PLANS = {
        'basic': {
            'name': 'Trader Starter',
            'price': 9.99,
            'features': ['Manual Trading', 'Market Analysis']
        },
        'pro': {
            'name': 'Trader Pro',
            'price': 29.99,
            'features': ['Automated Trading', 'Advanced Analytics', 'Priority Support']
        }
    }
