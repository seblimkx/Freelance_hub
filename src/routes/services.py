"""Service and payment-related routes"""
from flask import Blueprint, render_template, request, session, redirect
import os
import stripe
from dotenv import load_dotenv
from src.models import Profile
from src.utils.database import get_db_connection

# Load environment variables
load_dotenv()

service_bp = Blueprint('service', __name__)

# Initialize Stripe with API key from environment
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

@service_bp.route("/service/<int:service_id>")
def service_detail(service_id):
    db = get_db_connection()
    cursor = db.cursor()
    service = cursor.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()
    cursor.close()
    db.close()
    
    if not service:
        return "Service not found", 404

    service_data = {
        "id": service["id"], 
        "title": service["title"], 
        "description": service["description"], 
        "price": service["price"],
        "image_url": service["image_url"] if service["image_url"] else "/static/default_image.png"
    }
    user_profile = Profile(session["username"], session["profile_type"], None, 
                          session["user_id"], resume=session.get("resume", ""))
    
    return render_template("service_detail.html", service=service_data, profile=user_profile)

@service_bp.route('/create-checkout-session/<int:service_id>', methods=['POST'])
def create_checkout_session(service_id):
    db = get_db_connection()
    cursor = db.cursor()
    service = cursor.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()
    cursor.close()
    db.close()
    
    if not service:
        return "Service not found", 404
    
    YOUR_DOMAIN = 'http://127.0.0.1:5000'

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'myr',
                        'product_data': {
                            'name': service['title'],
                        },
                        'unit_amount': int(service['price'] * 100),
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success',
            cancel_url=YOUR_DOMAIN + '/cancel',
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return str(e)

@service_bp.route('/success')
def success():
    return render_template('success.html')

@service_bp.route('/cancel')
def cancel():
    service_id = request.args.get('service_id', None)
    return render_template('cancel.html', service_id=service_id)
