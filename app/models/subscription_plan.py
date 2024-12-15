from app import db
from datetime import datetime
from app.models.permission import Permission

# Tabla intermedia para la relación muchos a muchos entre planes y permisos
plan_permissions = db.Table('plan_permissions',
    db.Column('plan_id', db.Integer, db.ForeignKey('subscription_plans.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, nullable=False)  # Price in cents
    interval = db.Column(db.String(20), nullable=False, default='month')
    stripe_price_id = db.Column(db.String(100), unique=True)
    stripe_product_id = db.Column(db.String(100), unique=True)
    
    # Características básicas
    has_manual_trading = db.Column(db.Boolean, default=True)
    has_automated_trading = db.Column(db.Boolean, default=False)
    has_advanced_trading = db.Column(db.Boolean, default=False)
    has_basic_analysis = db.Column(db.Boolean, default=True)
    has_advanced_analysis = db.Column(db.Boolean, default=False)
    has_custom_dashboard = db.Column(db.Boolean, default=True)
    
    # Características de bots y API
    max_bots = db.Column(db.Integer, default=1)
    has_custom_bots = db.Column(db.Boolean, default=False)
    has_unlimited_bots = db.Column(db.Boolean, default=False)
    has_api_access = db.Column(db.Boolean, default=False)
    has_custom_apis = db.Column(db.Boolean, default=False)
    
    # Soporte
    support_level = db.Column(db.String(20), default='email')  # email, priority, dedicated
    
    # Sistema
    is_active = db.Column(db.Boolean, default=True)
    trial_days = db.Column(db.Integer, default=14)
    cancellation_type = db.Column(db.String(20), default='anytime')  # anytime, end_of_period
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación muchos a muchos con Permission
    permissions = db.relationship('Permission',
                                secondary='plan_permissions',
                                back_populates='subscription_plans')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'interval': self.interval,
            'features': self.features.split('\n') if self.features else [],
            'max_bots': self.max_bots,
            'max_trades_per_day': self.max_trades_per_day,
            'has_advanced_indicators': self.has_advanced_indicators,
            'has_api_access': self.has_api_access,
            'is_active': self.is_active,
            'stripe_price_id': self.stripe_price_id,
            'stripe_product_id': self.stripe_product_id,
            'permissions': [p.to_dict() for p in self.permissions]
        }

    def has_permission(self, permission_code):
        """Verifica si el plan tiene un permiso específico por su código"""
        return any(p.code == permission_code for p in self.permissions)
