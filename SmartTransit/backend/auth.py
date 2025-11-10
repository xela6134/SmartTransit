from flask import Blueprint, jsonify, request, g
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt, get_jwt_identity
from datetime import datetime, timedelta
import mysql.connector
from dotenv import load_dotenv
import os, re
from datetime import timedelta, datetime
import logging
import phonenumbers
import boto3.session
import boto3
from custom_decorator import admin_user_only
import random

load_dotenv()

# Constants & Setups

CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME')
}

logger = logging.getLogger(__name__)

# JWT configuration
jwt_secret_key = os.getenv('JWT_SECRET_KEY')
jwt_access_expires = timedelta(minutes=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 15)))

# Email and Password regex
EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
PASSWORD_REGEX = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*?&]{8,}$'  # At least 8 characters, 1 letter, 1 number

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

def get_db_connection():
    if 'db' not in g:
        try:
            # Store the connection object itself on g.db
            g.db = mysql.connector.connect(**CONFIG)
            logger.debug(">>> New DB Connection Established (id: %s)", id(g.db))
        except mysql.connector.Error as err:
            raise ConnectionError(f"Failed to connect to database: {err}")
    else:
       logger.debug("--- Reusing DB Connection (id: %s)", id(g.db))
    return g.db

def close_db_connection(e=None):
    db = g.pop('db', None) # Get db connection from g, removing it
    if db is not None:
        try:
            db.close()
        except mysql.connector.Error as err:
            raise ConnectionError(f"Error closing database connection: {err}")

"""
    --- JWT Blocklist Check ---
    Callback function for Flask-JWT-Extended to check if a JWT has been revoked.
"""
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT jti FROM RevokedTokens WHERE jti = %s", (jti,))
        revoked_token = cursor.fetchone()
        is_revoked = revoked_token is not None
        return is_revoked # Return True if token is found in the blocklist (revoked)
    except mysql.connector.Error as err:
        return True # Fail-safe for if DB check fails, assume token is revoked
    finally:
        if cursor: cursor.close()

""" 
    --- Register blocklist loader ---
    Registers the JWT blocklist loader with the JWTManager instance.
"""
def register_jwt_blocklist_loader(jwt_manager_instance):
    @jwt_manager_instance.token_in_blocklist_loader
    def check_if_token_revoked_callback(jwt_header, jwt_payload):
        return check_if_token_revoked(jwt_header, jwt_payload)

"""
    Register a new user
    ---
    Creates a new user account with email, password, and additional details.
    Request body (JSON):
    - email (str): user's email address (must be unique)
    - password (str): plain text password (will be hashed)
    - name (str): user's full name
    - age (int, optional): user's age
    - phone_number (str, optional): user's phone number
    - disability (int, optional): disability status (0 or 1)
    - location (decimal, optional): user's location as a decimal number

    Returns:
    - 201 Created: User registered successfully
    - 400 Bad Request: Missing required fields, invalid inputs
    - 409 Conflict: Email already registered
    - 500 Internal Server Error: Database error
"""
@auth_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()

    # Unpack values
    email = (data.get('email') or '').strip()
    password = (data.get('password') or '').strip()
    name = (data.get('name') or '').strip()
    age = data.get('age')
    phone_number = (data.get('phone_number') or '').strip() if data.get('phone_number') else None
    disability = data.get('disability')
    location = data.get('location')
    
    # Validate required fields
    if not all([email, password, name]):
        return jsonify({'error': 'Missing required fields (email, password, name)'}), 400
    if not re.match(EMAIL_REGEX, email):
        return jsonify({'error': 'Invalid email format!'}), 400
    if not re.match(PASSWORD_REGEX, password):
        return jsonify({'error': 'Password must be at least 8 characters long and contain at least one letter and one number!'}), 400
    phoneNumberParse = phonenumbers.parse(phone_number)
    phoneNumberFormatted = phonenumbers.format_number(phoneNumberParse, phonenumbers.PhoneNumberFormat.E164)

    # Convert and validate optional fields if provided
    if age is not None:
        try:
            age = int(age)
        except ValueError:
            return jsonify({'error': 'Age must be an integer'}), 400

    if disability is not None:
        try:
            disability = int(disability)
        except ValueError:
            return jsonify({'error': 'Disability must be an integer (0 or 1)'}), 400

    if location is not None:
        try:
            location = float(location)
        except ValueError:
            return jsonify({'error': 'Location must be a decimal number'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the email is already registered
        cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Email already registered!'}), 409

        # Insert new user including optional fields
        cursor.execute(
            "INSERT INTO Users (name, email, password_hash, age, phone_number, disability, location) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (name, email, hashed_password, age, phoneNumberFormatted, disability, location)
        )
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 201

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

"""
    Authenticate user and generate access token
    ---
    Validates user credentials and returns a JWT for authorisation
    Request body (JSON):
    - email (str): registered email address
    - password (str): account password
    
    Returns:
    - 200 OK: { access_token: JWT }
    - 400 Bad Request: Missing credentials
    - 401 Unauthorized: Invalid credentials
    - 500 Internal Server Error: Database error
"""
@auth_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = (data.get('email') or '').strip()
    password = (data.get('password') or '').strip()

    if not all([email, password]):
        return jsonify({'error': 'Missing email or password'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if user exists
        cursor.execute("""
            SELECT user_id, password_hash 
            FROM Users 
            WHERE email = %s
        """, (email,))
        user = cursor.fetchone()

        if not user or not bcrypt.check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Credentials are valid, create JWT
        access_token = None
        if user["user_id"] == 1:
            access_token = create_access_token(
                identity=str(user['user_id']),
                expires_delta=jwt_access_expires,
                additional_claims={"is_admin": True, "is_driver": False}
            )
        else:
            access_token = create_access_token(
                identity=str(user['user_id']),
                expires_delta=jwt_access_expires,
                additional_claims={"is_admin": False, "is_driver": False}
            )
        return jsonify(access_token=access_token), 200
    
    except mysql.connector.Error as err:
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor: cursor.close()

"""
    Logout and revoke access token
    ---
    Invalidates the current JWT token, preventing future use.
    Requires valid JWT in Authorization header.
    
    Returns:
    - 200 OK: Successfully logged out
    - 401 Unauthorized: Missing or invalid token
    - 500 Internal Server Error: Database error
"""
@auth_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    conn = None
    cursor = None
    try:
        jwt_data = get_jwt()
        jti = jwt_data['jti']
        expires_at = datetime.fromtimestamp(jwt_data['exp'])

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert into revoked tokens, ensures logging out
        cursor.execute(
            "INSERT INTO RevokedTokens (jti, expires_at) VALUES (%s, %s)",
            (jti, expires_at)
        )
        conn.commit()
        return jsonify({'message': 'Successfully logged out'}), 200

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor: cursor.close()

"""
    Get current authenticated user status
    ---
    Returns the name and email of the currently authenticated user.
    Requires a valid JWT in the Authorization header or cookie.
    
    Returns:
    - 200 OK: { "name": <user's name>, "email": <user's email> }
    - 401 Unauthorized: Missing or invalid token
    - 404 Not Found: User does not exist
    - 500 Internal Server Error: Database error
"""
@auth_bp.route('/auth/status', methods=['GET'])
@admin_user_only()
def status():
    try:
        # Get the user ID from the JWT token
        user_id = get_jwt_identity()
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Query the database for the user's name and email using the user ID
        cursor.execute("SELECT user_id, name, email FROM Users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user_id': user['user_id'], 'name': user['name'], 'email': user['email']}), 200

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor: cursor.close()

"""
    Get information about the current user
    ---
    Returns the name and email of the currently authenticated user.
    Requires a valid JWT in the Authorization header or cookie.
    
    Returns:
    - 200 OK: User information
    - 404 Not Found: User does not exist
    - 500 Internal Server Error: Database error
"""
@auth_bp.route('/auth/profile', methods=['GET'])
@jwt_required()
def profile():
    try:
        # Get the user ID from the JWT token
        user_id = get_jwt_identity()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query for profile fields (matching /auth/register schema)
        cursor.execute("SELECT name, email, age, phone_number, disability FROM Users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor: 
            cursor.close()

"""
    Verifies the password for the current user.
    
    Returns:
    - 200 OK: User information
    - 401 Unauthorized: Invalid credentials
    - 404 Not found: User not found
    - 500 Internal Server Error: Database error
"""
@auth_bp.route('/auth/verify_password', methods=['POST'])
@jwt_required()
def verify_password():
    data = request.get_json()
    password = (data.get('password') or '').strip()
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    try:
        user_id = get_jwt_identity()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get the hashed password
        cursor.execute("SELECT password_hash FROM Users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404
        if bcrypt.check_password_hash(user['password_hash'], password):
            return jsonify({'message': 'Password verified'}), 200
        else:
            return jsonify({'error': 'Incorrect password'}), 401
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor:
            cursor.close()

"""
    Forget Password Route for users
    Request body (JSON):
    - email (str): user's email
    Returns:
    - 200 OK: SMS SENT
    - 400 BAD REQUEST: Email isn't provided or invalid format or that email doesn't exist
    - 500 Internal Server Error: Database error
"""
@auth_bp.route('/auth/forget_password', methods=['POST'])
def forget_password():
    data = request.get_json()
    email = (data.get('email') or '').strip()
    
    # Validate data
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    if not re.match(EMAIL_REGEX, email):
        return jsonify({'error': 'Invalid email format!'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        session = boto3.session.Session(aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                                        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'))
        client = session.client("sns", region_name="ap-southeast-2")

        # Validate if user exists
        cursor.execute("SELECT * FROM Users WHERE email=%s", (email, ))
        user = cursor.fetchall()
        if len(user) == 0:
            return jsonify({'error': 'No user with that email!'}), 400
        selectedUser = user[0]

        # Make OTP
        token = random.randint(100000, 999999)
        phone_number = selectedUser['phone_number']
        expired = datetime.strftime(
            datetime.now() + timedelta(minutes = 10),
            "%Y-%m-%d %H:%M:%S"
        )
        cursor.execute(
            "INSERT INTO SmsTokens (email, token, expires_at) VALUES (%s,%s,%s)",
            (email, token, expired)
        )
        conn.commit()

        # Send the message
        client.publish(
            PhoneNumber=str(phone_number),
            Message=f"""This is your token - {token}. Don't give it to anyone else!"""
        )

        return jsonify({"message": "A token was sent to your phone number"}), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor:
            cursor.close()

"""
    Reset Password Route for users
    Request body (JSON):
    - email (str): user's email
    - password (str): new password
    - token (str): token sent to user
    Returns:
    - 200 OK: Password is resetted
    - 400 BAD REQUEST: Token isn't provided, bad password, wrong token
    - 401 Unauthorized: This token is expired
    - 500 Internal Server Error: Database error
"""
@auth_bp.route('/auth/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = (data.get('email') or '').strip()
    password = (data.get('password') or '').strip()
    token = (data.get('token') or '').strip()
    if not token:
        return jsonify({'error': 'Token is required'}), 400
    if not re.match(PASSWORD_REGEX, password):
        return jsonify({'error': 'Password must be at least 8 characters long and contain at least one letter and one number!'}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        current_datetime = datetime.now()
        cursor.execute(
            "SELECT * FROM SmsTokens WHERE token=%s and email=%s",
            (token, email)
        )
        token_row = cursor.fetchall()
        if len(token_row) == 0:
            return jsonify({'error': 'Token provided is wrong!'}), 400
        selected_token_row = token_row[0]
        expired_at = selected_token_row['expires_at']
        if expired_at < current_datetime:
            return jsonify({'error': 'This token has expired!'}), 401
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')


        cursor.execute(
            "UPDATE Users SET password_hash=%s WHERE email=%s",
            (hashed_password, email)
        )
        conn.commit()

        return jsonify({"message": f"Password was resetted for {email}!"}), 200
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor:
            cursor.close()
