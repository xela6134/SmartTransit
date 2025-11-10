from flask import Blueprint, jsonify, request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
import mysql.connector
from dotenv import load_dotenv
import os

# Constants & Setups

# Email and Password regex
EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
PASSWORD_REGEX = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*?&]{8,}$'  # At least 8 characters, 1 letter, 1 number

load_dotenv()

CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME')
}

settings_bp = Blueprint('settings', __name__)
bcrypt = Bcrypt()

def get_db_connection():
    return mysql.connector.connect(**CONFIG)

"""
    Return user info
    ---
    Get all user's info from the DB (without id)
    Request body (JSON):
    - start_location (int): the location id in the DB
    - end_location (int): the location id in the DB
    
    Returns:
    - 200 OK: {
        name: str,
        password_hash: str,
        email: str
    }
    - 401 Unauthorized: Not logged in
    - 500 Internal Server Error: Database error
"""
@settings_bp.route('/settings/profile', methods=['GET'])
@jwt_required()
def getUserInfo():
    userId = get_jwt_identity()

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Users WHERE user_id=%s", (userId,))
        userInfo = cursor.fetchone()
        if not userInfo:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({
            "name": userInfo["name"],
            "email": userInfo["email"]
        }), 200
    except mysql.connector.Error as err:
        conn.rollback()

        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

"""
    Edit profile information
    ---
    Edits the profile information with its supplied parameters.
    Request body (JSON):
    - Too many request bodies
    - Password is optional

    Returns:
    - 200 OK: New profile information
    - 500 Internal Server Error: Database error
"""
@settings_bp.route('/settings/profile/edit', methods=['PATCH'])
@jwt_required()
def edit_profile():
    # Unpack data
    user_id = get_jwt_identity()
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    age = data.get('age')
    phone_number = data.get('phone_number')
    disability = data.get('disability')
    
    # Only change password if provided
    hashed_password = None
    if password:
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Update each of the fields
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "UPDATE Users SET name = %s, email = %s, age = %s, phone_number = %s, disability = %s"
        params = [name, email, age, phone_number, disability]

        if hashed_password:
            query += ", password_hash = %s"
            params.append(hashed_password)

        query += " WHERE user_id = %s"
        params.append(user_id)

        cursor.execute(query, tuple(params))
        conn.commit()

        # Update the new profile details
        cursor.execute("SELECT name, email, age, phone_number, disability FROM Users WHERE user_id = %s", (user_id,))
        updated = cursor.fetchone()
        updated_profile = {
            "name": updated[0],
            "email": updated[1],
            "age": updated[2],
            "phone_number": updated[3],
            "disability": bool(updated[4]) if updated[4] is not None else None
        }
        return jsonify(updated_profile), 200

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({'error': str(err)}), 500

    finally:
        if cursor: cursor.close()
        if conn: conn.close()
