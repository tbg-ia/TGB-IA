from app import db
from datetime import datetime

class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(200))
    category = db.Column(db.String(50), nullable=False)  # 'trading', 'system', 'notification'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<SystemConfig {self.key}={self.value}>'

    @staticmethod
    def get_value(key, default=None):
        config = SystemConfig.query.filter_by(key=key).first()
        return config.value if config else default

    @staticmethod
    def set_value(key, value, category, description=None, user_id=None):
        config = SystemConfig.query.filter_by(key=key).first()
        if config:
            config.value = value
            config.updated_at = datetime.utcnow()
            if user_id:
                config.updated_by = user_id
        else:
            config = SystemConfig(
                key=key,
                value=value,
                category=category,
                description=description,
                updated_by=user_id
            )
            db.session.add(config)
        db.session.commit()
        return config
