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
    interval = db.Column(db.String(20), nullable=False)  # 'month' or 'year'
    stripe_price_id = db.Column(db.String(100), unique=True)
    stripe_product_id = db.Column(db.String(100), unique=True)
    features = db.Column(db.Text)
    max_bots = db.Column(db.Integer, default=1)  # Número máximo de bots permitidos
    max_trades_per_day = db.Column(db.Integer, default=10)  # Límite de trades por día
    has_advanced_indicators = db.Column(db.Boolean, default=False)  # Acceso a indicadores avanzados
    has_api_access = db.Column(db.Boolean, default=False)  # Acceso a API
    is_active = db.Column(db.Boolean, default=True)
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
