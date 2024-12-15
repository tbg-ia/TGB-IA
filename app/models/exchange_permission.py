from app import db
from datetime import datetime

class ExchangePermission(db.Model):
    """Modelo para gestionar los permisos específicos de exchange por plan de suscripción"""
    __tablename__ = 'exchange_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    subscription_plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id', ondelete='CASCADE'), unique=True)
    active_signals = db.Column(db.Integer, nullable=False, default=1)
    apis_per_exchange = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con el plan de suscripción
    subscription_plan = db.relationship(
        'SubscriptionPlan',
        backref=db.backref(
            'exchange_permission',
            uselist=False,
            cascade='all, delete-orphan',
            single_parent=True
        ),
        single_parent=True
    )
    
    def __repr__(self):
        return f'<ExchangePermission plan_id={self.subscription_plan_id}>'
        
    def to_dict(self):
        return {
            'active_signals': self.active_signals,
            'apis_per_exchange': self.apis_per_exchange
        }

    @staticmethod
    def get_default_limits():
        """Retorna los límites por defecto para planes sin permisos específicos"""
        return {
            'active_signals': 1,
            'apis_per_exchange': 1
        }
