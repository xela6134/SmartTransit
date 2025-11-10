from flask import Blueprint, jsonify, request
from flask_bcrypt import Bcrypt
from flask_jwt_extended import get_jwt_identity
from datetime import datetime
import mysql.connector
from dotenv import load_dotenv
import os, re
from datetime import datetime
from auth import get_db_connection, EMAIL_REGEX, PASSWORD_REGEX
from custom_decorator import admin_only

load_dotenv()

# Constants & Setups

CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME')
}

admin_bp = Blueprint('admin', __name__)
bcrypt = Bcrypt()

"""
    Registers a driver under admin privileges
    ---
    Registers a driver with given information(JSON):
    - name (str): name of driver
    - email (str): registered email address
    - password (str): account password
    - age (int): age of driver
    - employee_type (char): Indicates whether driver is casual, part time or full time\
    
    Returns:
    - 200 OK: { 'message': 'Driver registered successfully' }
    - 400 Bad Request: { 'error': 'Missing required fields (email, password, name)' } or 
        { 'error': 'Invalid email format!' } 
        or { 'error': 'Password must be at least 8 characters long and contain at least one letter and one number!' }
        or { 'error': 'Age must be an integer'} or {'error': 'employee_type must be a single character' }
    - 401 Unauthorized: Invalid credentials
    - 403 Forbidden: { 'error': 'User does not have access' }
    - 409 Conflict: { 'error': 'Email already registered!' }
    - 500 Internal Server Error: { 'error': 'Database error', 'details': str(err) }
"""
@admin_bp.route('/auth/admin/register_driver', methods=['POST'])
@admin_only()
def driver_register():
    user_id = get_jwt_identity()
    user_id = int(user_id)
    
    if user_id != 1:
        return jsonify({'error': 'User does not have access'}), 403

    # Get data fields
    data = request.get_json()
    email = (data.get('email') or '').strip()
    password = (data.get('password') or '').strip()
    name = (data.get('name') or '').strip()
    age = data.get('age')
    employee_type = (data.get('employee_type') or '').strip()
    
    driver_salary = data.get('driver_salary')
    hire_date = datetime.today().strftime('%Y-%m-%d')

    # Validate required fields
    if not all([email, password, name]):
        return jsonify({'error': 'Missing required fields (email, password, name)'}), 400
    if not re.match(EMAIL_REGEX, email):
        return jsonify({'error': 'Invalid email format!'}), 400
    if not re.match(PASSWORD_REGEX, password):
        return jsonify({'error': 'Password must be at least 8 characters long and contain at least one letter and one number!'}), 400
    
    # Convert and validate optional fields if provided
    if age is not None:
        try:
            age = int(age)
        except ValueError:
            return jsonify({'error': 'Age must be an integer'}), 400
        
    if employee_type is not None:
        if not isinstance(employee_type, str) or len(employee_type) != 1:
            return jsonify({'error': 'employee_type must be a single character'}), 400

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
            """
            INSERT INTO Drivers (
                name, email, password_hash, age, employee_type, driver_salary, hire_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (name, email, hashed_password, age, employee_type, driver_salary, hire_date)
        )
        conn.commit()
        return jsonify({'message': 'Driver registered successfully'}), 201
    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor: cursor.close()


"""
    Adds a vehicle under admin privileges
    ---
    Adds a vehicle into the database(JSON):
    - capacity (int): amount of seats in bus
    - disability_seats (int): amount of disabled seats in bus
    - licence_number (varchar(8)): licence number of the vehicle
    
    Returns:
    - 201 OK: { 'message': 'Vehicle added successfully' }
    - 400 Bad Request: { 'error': 'Missing required fields (capacity, disability_seats, licence_number)' } or 
        { 'error': 'Licence number must be 8 characters or less' } or { 'error': 'capacity must be an integer' } 
        or { 'error': 'disability_seats must be an integer' } 
        or { 'error': 'disability_seats cannot be greater than capacity' }
    - 401 Unauthorized: Invalid credentials
    - 403 Forbidden: { 'error': 'User does not have access' }
    - 500 Internal Server Error: { 'error': 'Database error', 'details': str(err) }
"""
@admin_bp.route('/auth/admin/add_vehicle', methods=['POST'])
@admin_only()
def add_vehicle():
    user_id = get_jwt_identity()
    user_id = int(user_id)
    
    # Extra security check for admins only
    if user_id != 1:
        return jsonify({'error': 'User does not have access'}), 403
    data = request.get_json()

    capacity = (data.get('capacity'))
    disability_seats = (data.get('disability_seats'))
    licence_number = str(data['licence_number']).strip()

    # Validate Required Fields
    if not all([capacity, disability_seats, licence_number]):
        return jsonify({'error': 'Missing required fields (capacity, disability_seats, licence_number)'}), 400

    # Convert and validate optional fields if provided
    if len(licence_number) > 8:
            return jsonify({'error': 'Licence number must be 8 characters or less'}), 400
    
    if capacity is not None:
        try:
            capacity = int(capacity)
        except ValueError:
            return jsonify({'error': 'capacity must be an integer'}), 400
        
    if disability_seats is not None:
        try:
            disability_seats = int(disability_seats)
        except ValueError:
            return jsonify({'error': 'disability_seats must be an integer'}), 400

    if disability_seats > capacity:
        return jsonify({'error': 'disability_seats cannot be greater than capacity'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert new vehicle
        cursor.execute(
            "INSERT INTO Vehicles (capacity, disability_seats, licence_number) VALUES (%s, %s, %s)",
            (capacity, disability_seats, licence_number)
        )
        conn.commit()
        return jsonify({'message': 'Vehicle added successfully'}), 201
    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor: cursor.close()

"""
    Lists all drivers
    ---
    List all the drivers that have been registered
    
    Returns:
    - 200 OK: { 'drivers': drivers }
    - 401 Unauthorized: Invalid credentials
    - 403 Forbidden: { 'error': 'User does not have access' }
    - 500 Internal Server Error: { 'error': 'Database error', 'details': str(err) }
"""
@admin_bp.route('/auth/admin/all_drivers', methods=['GET'])
@admin_only()
def list_drivers():
    user_id = get_jwt_identity()
    user_id = int(user_id)
    if user_id != 1:
        return jsonify({'error': 'User does not have access'}), 403

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) 

        # Get all the drivers
        cursor.execute("SELECT driver_id, name, email, age, employee_type, driver_salary, hire_date FROM Drivers")
        drivers = cursor.fetchall()
        return jsonify({'drivers': drivers}), 200
    except mysql.connector.Error as err:
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

"""
    Lists all vehicles
    ---
    List all the vehicles that have been added
    
    Returns:
    - 200 OK: { 'vehicles': vehicles }
    - 401 Unauthorized: Invalid credentials
    - 403 Forbidden: { 'error': 'User does not have access' }
    - 500 Internal Server Error: { 'error': 'Database error', 'details': str(err) }
"""
@admin_bp.route('/auth/admin/all_vehicles', methods=['GET'])
@admin_only()
def list_routes():
    user_id = get_jwt_identity()
    user_id = int(user_id)
    if user_id != 1:
        return jsonify({'error': 'User does not have access'}), 403

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get all the vehicles
        cursor.execute("SELECT * FROM Vehicles")
        vehicles = cursor.fetchall()
        return jsonify({'vehicles': vehicles}), 200
    except mysql.connector.Error as err:
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()