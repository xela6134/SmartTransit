from flask import Blueprint, jsonify, request, g
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity
from datetime import datetime, timedelta
import mysql.connector
from dotenv import load_dotenv
import os
from datetime import timedelta
import logging
from custom_decorator import driver_only

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

driver_bp = Blueprint('driver', __name__)
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

# Add a register function for the sake of testing, will be changed and implemented 
# properly later when admin stuff is tackled
def driver_register(email, password, name):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check for existing email
        cursor.execute("SELECT driver_id FROM Drivers WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Email already registered!'}), 409

        # Hash password and insert new user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        cursor.execute(
            "INSERT INTO Drivers (name, email, password_hash) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )
        conn.commit()
        return jsonify({'message': 'Driver registered successfully'}), 201

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor: cursor.close()

# An add_vehicle function which is just a placeholder for testing and will be properly implemented and 
# modified later when admin stuff will be tackled
def add_vehicle(capacity, licence_number):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert new vehicle
        cursor.execute(
            "INSERT INTO Vehicles (capacity, licence_number) VALUES (%s, %s)",
            (capacity, licence_number)
        )
        conn.commit()
        return jsonify({'message': 'Vehicle added successfully'}), 201

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor: cursor.close()

"""
    Authenticate driver and generate access token
    ---
    Validates user credentials and returns a JWT for authorisation
    Request body (JSON):
    - email (str): registered email address
    - password (str): account password
    
    Returns:
    - 200 OK: { access_token: JWT }
    - 400 Bad Request: { 'error': 'Missing email or password' }
    - 401 Unauthorized: Invalid credentials
    - 500 Internal Server Error: { 'error': 'Database error', 'details': str(err) }
"""
@driver_bp.route('/auth/driver/login', methods=['POST'])
def driver_login():
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

        # Check for incorrect email
        cursor.execute("""
            SELECT driver_id, password_hash 
            FROM Drivers 
            WHERE email = %s
        """, (email,))
        driver = cursor.fetchone()

        if not driver or not bcrypt.check_password_hash(driver['password_hash'], password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Credentials are valid, create JWT
        access_token = create_access_token(
            identity=str(driver['driver_id']),
            expires_delta=jwt_access_expires,
            additional_claims={"is_admin": False, "is_driver": True}
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
    - 200 OK: { 'message': 'Successfully logged out' }
    - 401 Unauthorized: Missing or invalid token
    - 500 Internal Server Error: { 'error': 'Database error', 'details': str(err) }
"""
@driver_bp.route('/auth/driver/logout', methods=['POST'])
@driver_only()
def logout():
    conn = None
    cursor = None
    try:
        jwt_data = get_jwt()
        jti = jwt_data['jti']
        expires_at = datetime.fromtimestamp(jwt_data['exp'])

        conn = get_db_connection()
        cursor = conn.cursor()

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
    Assign a vehicle to the authenticated driver
    ---
    Request body (JSON):
    - licence_number (varchar(8)): licence number of the vehicle

    Returns:
    - 200 OK: { 'message': 'Vehicle assigned successfully' }
    - 400 Bad Request: { 'error': 'Missing vehicle licence number' }
    - 404 Not Found: { 'error': 'Driver not found' } or { 'error': 'Vehicle not found' }
    - 500 Internal Server Error: { 'error': 'Database error', 'details': str(err) }
"""
@driver_bp.route('/driver/assign_vehicle', methods=['POST'])
@driver_only()
def assign_vehicle():
    data = request.get_json()
    driver_id = get_jwt_identity()
    licence_number = (data.get('licence_number') or '').strip()

    if not licence_number:
        return jsonify({'error': 'Missing vehicle licence number'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)

        # Check if driver exists
        cursor.execute("SELECT driver_id FROM Drivers WHERE driver_id = %s", (driver_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Invalid or unauthorized driver'}), 404

        # Find vehicle by licence number
        cursor.execute("SELECT vehicle_id FROM Vehicles WHERE licence_number = %s", (licence_number,))
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'Vehicle not found'}), 404

        vehicle_id = result[0]

        # Assign vehicle to driver
        cursor.execute(
            "UPDATE Drivers SET assigned_vehicle = %s WHERE driver_id = %s",
            (vehicle_id, driver_id)
        )
        conn.commit()
        return jsonify({'message': 'Vehicle assigned successfully'}), 200

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor: cursor.close()

"""
    Unassign a vehicle to the authenticated driver
    ---
    Request body (JSON):
    - licence_number (varchar(8)): licence number of the vehicle

    Returns:
    - 200 OK: { 'message': 'Vehicle unassigned successfully' }
    - 400 Bad Request: { 'error': 'Missing vehicle licence number' }
    - 404 Not Found: { 'error': 'Driver not found' } or { 'error': 'Vehicle not found' }
    - 500 Internal Server Error: { 'error': 'Database error', 'details': str(err) }
"""
@driver_bp.route('/driver/unassign_vehicle', methods=['POST'])
@driver_only()
def unassign_vehicle():
    data = request.get_json()
    driver_id = get_jwt_identity()
    licence_number = (data.get('licence_number') or '').strip()

    if not licence_number:
        return jsonify({'error': 'Missing vehicle licence number'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)

        # Check if driver exists
        cursor.execute("SELECT assigned_vehicle FROM Drivers WHERE driver_id = %s", (driver_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'Invalid or unauthorized driver'}), 404
        
        assigned_vehicle = result[0]

        # Find vehicle by licence number
        cursor.execute("SELECT vehicle_id FROM Vehicles WHERE licence_number = %s", (licence_number,))
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'Vehicle not found'}), 404

        vehicle_id = result[0]

        # Check if given vehicle matches the drivers assigned vehicle
        if vehicle_id != assigned_vehicle:
            return jsonify({'error': 'Driver is not assigned to the given vehicle'}), 400

        # Unassign vehicle from driver
        cursor.execute(
            "UPDATE Drivers SET assigned_vehicle = NULL WHERE driver_id = %s",
            (driver_id,)
        )
        conn.commit()
        return jsonify({'message': 'Vehicle unassigned successfully'}), 200

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor: cursor.close()

"""
    The driver's location is periodically updated
    -------------------------------------------------------
    Update the vehicle's location based on driver's GPS (most probably) in the DB

    Parameters:
        latitude (float): latitide value of vehicle
        longitude (float): longitude value of vehicle
    Returns:
    - 200 OK: Updated loacations
    - 400 Bad Request: Missing latitude or longitude
    - 500 Internal Server Error: Database error
"""
@driver_bp.route('/driver/updateLocation', methods=['PATCH'])
@driver_only()
def updateLocation():
    data = request.get_json()
    driverId = get_jwt_identity()
    latitude = float(data.get('latitude'))
    longitude = float(data.get('longitude'))


    if latitude == '' or longitude == '':
        return jsonify({"message": "Missing longitude or latitude"}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT assigned_vehicle FROM Drivers WHERE driver_id=%s", (driverId, ))
        vehicleId = cursor.fetchall()[0]['assigned_vehicle']
        cursor.execute(
        """
        UPDATE Vehicles SET x_coordinate=%s, y_coordinate=%s
        WHERE vehicle_id=%s
        """, (latitude, longitude, vehicleId))
        conn.commit()
        return jsonify({'message': f'Location updated to ({latitude}, {longitude})'}), 200
    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor: cursor.close()