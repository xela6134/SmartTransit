import stripe
from flask import Blueprint, jsonify, request, current_app, g
from flask_jwt_extended import jwt_required, get_jwt_identity
import mysql.connector
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
from custom_decorator import user_only
import stripe.error

load_dotenv()

# Constants & Setups

CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME')
}

# Stripe Configuration
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
stripe_publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY')
stripe_webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

payment_bp = Blueprint('payment', __name__)
logger = logging.getLogger(__name__)

def get_db_connection():
    if 'db' not in g:
        try:
            g.db = mysql.connector.connect(**CONFIG)
            logger.debug(">>> New DB Connection Established (Payment BP, id: %s)", id(g.db))
        except mysql.connector.Error as err:
            logger.error("Failed to connect to database: %s", err)
            raise ConnectionError(f"Failed to connect to database: {err}")
    else:
       logger.debug("--- Reusing DB Connection (Payment BP, id: %s)", id(g.db))
    return g.db


# Placeholder for price calculation
def calculate_ride_price(ride_duration):
    """
    Calculates the price for a given ride_id
    Stripe takes the price in the smallest currency unit i.e. cents
    """
    
    # Placeholder: minutes * 0.30
    return int(ride_duration * 11)

"""
    Get Stripe Publishable Key
    ---
    Provides the Stripe Publishable Key to the frontend.
    Returns:
    - 200 OK: { "publishableKey": <STRIPE_PUBLISHABLE_KEY> }
"""
@payment_bp.route('/payment/config', methods=['GET'])
@user_only()
def get_stripe_config():
    return jsonify({'publishableKey': stripe_publishable_key})

"""
    Create Payment Intent
    ---
    initiates a payment attempt for a ride - does not create booking.
    Request body (JSON):
    - ride_id: The ID of the ride for the booking.
    (User ID is obtained from JWT)

    Returns:
    - 200 OK: { "clientSecret": <client_secret_from_stripe> }
    - 400 Bad Request: Missing ride_id.
    - 401 Unauthorized: Not logged in.
    - 404 Not Found: Ride ID does not exist.
    - 409 Conflict: User has already successfully paid for this ride.
    - 500 Internal Server Error: Database or Stripe API error.
"""
@payment_bp.route('/payment/create-intent', methods=['POST'])
@user_only()
def create_payment_intent():
    data = request.get_json()
    ride_id = data.get('ride_id')
    user_id = get_jwt_identity()

    if not ride_id:
        return jsonify({'error': 'Missing ride_id'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Verify ride exists and retrieve its duration
        cursor.execute("SELECT ride_id, ride_duration FROM Rides WHERE ride_id = %s", (ride_id,))
        ride = cursor.fetchone()
        if not ride:
            return jsonify({'error': 'Ride not found'}), 404

        # Use the actual ride duration to calculate the amount
        ride_duration = ride['ride_duration']
        amount_cents = calculate_ride_price(ride_duration)
        currency = "aud"

        # 2. Check if already booked or paid
        cursor.execute("SELECT ride_id FROM Bookings WHERE ride_id = %s AND user_id = %s", (ride_id, user_id))
        existing_booking = cursor.fetchone()
        if existing_booking:
            return jsonify({'error': 'You have already booked and paid for this ride'}), 409

        # 3. Create Stripe Payment Intent
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                automatic_payment_methods={'enabled': True},
                metadata={
                    'ride_id': ride_id,
                    'user_id': user_id,
                }
            )
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating PaymentIntent: {e}")
            return jsonify({'error': 'Failed to create payment intent', 'details': str(e)}), 500

        # Return the client secret to PaymentScreen
        return jsonify({'clientSecret': payment_intent.client_secret}), 200

    except mysql.connector.Error as err:
        logger.error(f"Database error in create_payment_intent: {err}")
        if conn: conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        if conn: conn.rollback()
        return jsonify({'error': 'An unexpected error occurred'}), 500
    finally:
        if cursor: cursor.close()

"""
    Stripe Webhook Handler
    ---
    Listens for Stripe events. Creates Booking on successful payment
    Frontend does not need to call this route
"""
@payment_bp.route('/payment/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    event = None

    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_webhook_secret
        )
    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': 'Invalid signature'}), 400
    except Exception as e:
        return jsonify({'error': 'Webhook signature verification failed'}), 500
    
    # Handle the event type
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        ride_id = None
        user_id = None

        payment_intent = None
        if event.type.startswith('payment_intent'):
            payment_intent = event.data.object # Extract the PaymentIntent object
        
        if event.type == 'payment_intent.succeeded':
            if not payment_intent: 
                return jsonify({'error': 'Missing payment intent data'}), 400
            
            pi_id = payment_intent.id
            metadata = payment_intent.metadata
            
            ride_id = metadata.get('ride_id')
            user_id = metadata.get('user_id')
        
            if not ride_id or not user_id:
                return jsonify({'error': 'Missing metadata'}), 400

        cursor.execute(
            "SELECT ride_id FROM Bookings WHERE ride_id = %s AND user_id = %s",
            (ride_id, user_id)
        )
        existing_booking = cursor.fetchone()
        
        if not existing_booking:
            # Create the booking record NOW
            try:
                booking_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute(
                    """
                    INSERT INTO Bookings (ride_id, user_id, ride_date)
                    VALUES (%s, %s, %s)
                    """,
                    (ride_id, user_id, booking_time)
                )
                conn.commit()
                
            except mysql.connector.IntegrityError as ie:
                # Likely a race condition with concurrent webhook deliveries
                conn.rollback() # This could be problematic - tmp solution
            except mysql.connector.Error as db_err:
                conn.rollback()
                return jsonify({'error': 'Database error creating booking'}), 500
        else:
            logger.info(f"Webhook: Booking for ride {ride_id}, user {user_id} already exists.")
            
    except mysql.connector.Error as db_err:
        if conn: 
            conn.rollback()
        print(f"MySQL db error for Webhook: {db_err}")
        return jsonify({'error': 'Database error processing webhook'}), 500
    except Exception as e:
        if conn: conn.rollback()
        print(f"Exception 2 caught for Webhook: {e}")
        return jsonify({'error': 'Internal server error processing webhook'}), 500
    finally:
        if cursor: cursor.close()
    
    # Acknlowedge receipt to Stripe servers
    return jsonify({'received': True}), 200
