from app.extensions import db
from datetime import datetime

class Role(db.Model):
    __tablename__ = 'role'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.name}>'

    @staticmethod
    def insert_roles():
        roles = {
            'user': 'Regular user with basic access',
            'admin': 'Administrator with full access'
        }
        for role_name, description in roles.items():
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(name=role_name, description=description)
                db.session.add(role)
        db.session.commit()
