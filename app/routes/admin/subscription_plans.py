from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app import db
from app.decorators import admin_required
import stripe
import os

admin_subscription_bp = Blueprint('admin_subscription', __name__, url_prefix='/admin/subscription')

@admin_subscription_bp.route('/plans')
@login_required
@admin_required
def plans():
    """Lista todos los planes de suscripción"""
    plans = SubscriptionPlan.query.order_by(SubscriptionPlan.price).all()
    return render_template('subscription/admin/plans.html', plans=plans)

@admin_subscription_bp.route('/plans/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_plan():
    """Crear un nuevo plan de suscripción"""
    if request.method == 'POST':
        try:
            # Crear precio en Stripe
            stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
            stripe_price = stripe.Price.create(
                unit_amount=int(float(request.form['price']) * 100),
                currency='usd',
                recurring={'interval': 'month'},
                product_data={
                    'name': request.form['name'],
                    'description': request.form['description']
                }
            )

            # Crear plan en la base de datos
            plan = SubscriptionPlan(
                name=request.form['name'],
                type=request.form['type'],
                price=float(request.form['price']),
                description=request.form['description'],
                features=request.form.getlist('features[]'),
                stripe_price_id=stripe_price.id,
                trial_days=int(request.form.get('trial_days', 7))
            )
            db.session.add(plan)
            db.session.commit()
            
            flash('Plan creado exitosamente', 'success')
            return redirect(url_for('admin_subscription.plans'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el plan: {str(e)}', 'error')
    
    return render_template('admin/subscription/plan_form.html')

@admin_subscription_bp.route('/plans/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_plan(plan_id):
    """Editar un plan de suscripción existente"""
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    if request.method == 'POST':
        try:
            # Actualizar precio en Stripe si el precio cambió
            if float(request.form['price']) != plan.price:
                stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
                stripe_price = stripe.Price.create(
                    unit_amount=int(float(request.form['price']) * 100),
                    currency='usd',
                    recurring={'interval': 'month'},
                    product_data={
                        'name': request.form['name'],
                        'description': request.form['description']
                    }
                )
                plan.stripe_price_id = stripe_price.id
            
            # Actualizar plan en la base de datos
            plan.name = request.form['name']
            plan.type = request.form['type']
            plan.price = float(request.form['price'])
            plan.description = request.form['description']
            plan.features = request.form.getlist('features[]')
            plan.trial_days = int(request.form.get('trial_days', 7))
            
            db.session.commit()
            flash('Plan actualizado exitosamente', 'success')
            return redirect(url_for('admin_subscription.plans'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el plan: {str(e)}', 'error')
    
    return render_template('admin/subscription/plan_form.html', plan=plan)

@admin_subscription_bp.route('/plans/<int:plan_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_plan(plan_id):
    """Activar/desactivar un plan de suscripción"""
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    try:
        plan.is_active = not plan.is_active
        db.session.commit()
        status = 'activado' if plan.is_active else 'desactivado'
        flash(f'Plan {status} exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar el estado del plan: {str(e)}', 'error')
    
    return redirect(url_for('admin_subscription.plans'))
