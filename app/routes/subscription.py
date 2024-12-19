import os
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request, url_for, redirect, flash, current_app
from flask_login import login_required, current_user
import stripe
from app import db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.payment import Payment
from app.models.subscription_plan import SubscriptionPlan
from app.routes.helpers.subscription_handlers import (
    handle_subscription_created, handle_subscription_updated, handle_subscription_deleted,
    handle_invoice_paid, handle_invoice_payment_failed, handle_subscription_trial_will_end,
    handle_subscription_update_applied, handle_subscription_update_expired
)

subscription_bp = Blueprint('subscription', __name__, url_prefix='/subscription')

def get_plan_details(plan_id):
    try:
        plan = SubscriptionPlan.query.get(plan_id)
        if not plan:
            return None
        return {
            'stripe_price_id': plan.stripe_price_id,
            'name': plan.name,
            'price': plan.price
        }
    except Exception as e:
        logging.error(f"Error retrieving plan details: {str(e)}")
        return None

@subscription_bp.before_app_request
def init_stripe():
    if not hasattr(stripe, 'api_key') or not stripe.api_key:
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY', os.environ.get('STRIPE_SECRET_KEY'))

@subscription_bp.route('/planes')
@login_required
def planes():
    """Ruta para mostrar los planes de suscripción a usuarios regulares"""
    try:
        subscription_plans = SubscriptionPlan.query.filter_by(is_active=True).all()
        current_subscription = Subscription.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).first()

        return render_template('subscription/plans.html', 
                             subscription_plans=subscription_plans,
                             current_user=current_user,
                             current_subscription=current_subscription)
    except Exception as e:
        logging.error(f"Error al cargar los planes de suscripción: {str(e)}")
        flash('Error al cargar los planes de suscripción. Por favor intenta nuevamente.', 'error')
        return redirect(url_for('user.dashboard'))

@subscription_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:
        plan_id = request.form.get('plan_id')
        if not plan_id:
            flash('Plan no especificado', 'error')
            return redirect(url_for('subscription.planes'))

        plan = get_plan_details(plan_id)
        if not plan:
            flash('Plan no encontrado', 'error')
            return redirect(url_for('subscription.planes'))

        existing_subscription = Subscription.query.filter_by(user_id=current_user.id, status='active').first()

        stripe_price_id = plan.get('stripe_price_id')
        if not stripe_price_id:
            logging.error(f"Plan {plan_id} missing stripe_price_id")
            try:
                # Create product if it doesn't exist
                product = stripe.Product.create(
                    name=plan['name'],
                    description=SubscriptionPlan.query.get(plan_id).description
                )
                # Create price for the product
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=plan['price'],
                    currency='usd',
                    recurring={'interval': 'month'}
                )
                # Update plan with Stripe IDs
                subscription_plan = SubscriptionPlan.query.get(plan_id)
                subscription_plan.stripe_product_id = product.id
                subscription_plan.stripe_price_id = price.id
                db.session.commit()
                stripe_price_id = price.id
            except Exception as e:
                logging.error(f"Error creating Stripe product/price: {str(e)}")
                flash('Error: Plan no configurado correctamente', 'error')
                return redirect(url_for('subscription.planes'))

        checkout_params = {
            'payment_method_types': ['card'],
            'line_items': [{
                'price': stripe_price_id,
                'quantity': 1
            }],
            'mode': 'subscription',
            'success_url': url_for('subscription.payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            'cancel_url': url_for('subscription.payment_cancel', _external=True),
            'customer_email': current_user.email if not current_user.stripe_customer_id else None,
            'client_reference_id': str(current_user.id),
            'metadata': {
                'user_id': current_user.id,
                'plan_id': plan_id,
                'plan_name': plan['name']
            },
            'allow_promotion_codes': True,
            'billing_address_collection': 'required',
            'subscription_data': {
                'trial_period_days': 7,
                'metadata': {
                    'plan_type': plan['name'].lower()
                }
            }
        }

        if current_user.stripe_customer_id:
            checkout_params['customer'] = current_user.stripe_customer_id

        if current_user.subscription:
            checkout_params['subscription_data']['transfer_data'] = {
                'destination': current_user.subscription.stripe_subscription_id,
                'amount_percent': 100
            }

        checkout_session = stripe.checkout.Session.create(**checkout_params)

        try:
            subscription = Subscription(
                user_id=current_user.id,
                plan_type=plan['name'].lower(),
                status='pending',
                stripe_subscription_id=None,
                amount=plan.get('price', 0),
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(subscription)
            db.session.commit()

            return redirect(checkout_session.url, code=303)

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error saving subscription: {str(e)}")
            flash('Error al procesar la suscripción', 'error')
            return redirect(url_for('subscription.planes'))

    except stripe.error.StripeError as e:
        logging.error(f"Stripe error: {str(e)}")
        flash('Error al procesar el pago. Por favor, intente nuevamente.', 'error')
        return redirect(url_for('subscription.planes'))

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        flash('Ha ocurrido un error inesperado. Por favor, intente nuevamente.', 'error')
        return redirect(url_for('subscription.planes'))

@subscription_bp.route('/payment/success')
@login_required
def payment_success():
    flash('¡Gracias por tu suscripción! Tu plan ha sido activado.', 'success')
    return redirect(url_for('user.dashboard'))

@subscription_bp.route('/payment/cancel')
@login_required
def payment_cancel():
    flash('El proceso de pago fue cancelado.', 'info')
    return redirect(url_for('subscription.planes'))

@subscription_bp.route('/webhook', methods=['POST'])
def subscription_webhook():
    try:
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')

        webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET', os.environ.get('STRIPE_WEBHOOK_SECRET'))
        if not webhook_secret:
            logging.error("STRIPE_WEBHOOK_SECRET no configurado")
            return jsonify({'error': 'No se ha configurado el Webhook Secret de Stripe.'}), 500

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            logging.error(f"Invalid payload: {str(e)}")
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError as e:
            logging.error(f"Invalid signature: {str(e)}")
            return jsonify({'error': 'Invalid signature'}), 400

        event_handlers = {
            'customer.subscription.created': handle_subscription_created,
            'customer.subscription.updated': handle_subscription_updated,
            'customer.subscription.deleted': handle_subscription_deleted,
            'invoice.paid': handle_invoice_paid,
            'invoice.payment_failed': handle_invoice_payment_failed,
            'customer.subscription.trial_will_end': handle_subscription_trial_will_end,
            'customer.subscription.pending_update_applied': handle_subscription_update_applied,
            'customer.subscription.pending_update_expired': handle_subscription_update_expired
        }

        logging.info(f"Webhook event received: {event['type']}")

        handler = event_handlers.get(event['type'])
        if handler:
            try:
                handler(event['data']['object'])
                return jsonify({'success': True}), 200
            except Exception as e:
                logging.error(f"Error processing webhook {event['type']}: {str(e)}")
                return jsonify({'error': str(e)}), 500
        else:
            logging.warning(f"Unhandled webhook event type: {event['type']}")
            return jsonify({'message': 'Unhandled event type'}), 200

    except Exception as e:
        logging.error(f"Error procesando webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500
