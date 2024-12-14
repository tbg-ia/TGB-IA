from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.models.role import Role
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            if user.is_admin():
                return redirect(next_page or url_for('admin.dashboard'))
            return redirect(next_page or url_for('user.dashboard'))
        flash('Correo electrónico o contraseña inválidos')
    return render_template('public/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Verificar si ya existe el usuario
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken')
            return redirect(url_for('auth.register'))
            
        # Crear nuevo usuario
        user = User(email=email, username=username)
        user.set_password(password)
        
        # Asignar rol
        if username == 'bitxxo' and email == 'support@bitxxo.com':
            # Usuario administrador predefinido
            role = Role.query.filter_by(name='admin').first()
            if not role:
                flash('Error: Admin role not found')
                return redirect(url_for('auth.register'))
        else:
            # Usuario normal
            role = Role.query.filter_by(name='user').first()
            if not role:
                flash('Error: User role not found')
                return redirect(url_for('auth.register'))
        
        user.role_id = role.id
        db.session.add(user)
        
        try:
            db.session.commit()
            login_user(user)
            
            if user.is_admin():
                flash('Welcome Administrator!')
                return redirect(url_for('admin.dashboard'))
            else:
                flash('Registration successful!')
                return redirect(url_for('user.dashboard'))
                
        except Exception as e:
            db.session.rollback()
            flash('Error registering user. Please try again.')
            return redirect(url_for('auth.register'))
            
    return render_template('public/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
