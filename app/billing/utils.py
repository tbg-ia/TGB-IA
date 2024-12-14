from datetime import datetime
from typing import Optional

def calculate_prorated_amount(original_amount: float, days_used: int, total_days: int = 30) -> float:
    """Calculate prorated amount based on days used"""
    return (original_amount / total_days) * days_used

def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format currency amount with symbol"""
    currency_symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£'
    }
    symbol = currency_symbols.get(currency, '')
    return f'{symbol}{amount:.2f}'

def get_subscription_period(start_date: datetime, end_date: datetime) -> tuple[str, int]:
    """Get subscription period type and duration"""
    delta = end_date - start_date
    days = delta.days
    
    if days >= 365:
        return 'yearly', days // 365
    elif days >= 30:
        return 'monthly', days // 30
    else:
        return 'daily', days
