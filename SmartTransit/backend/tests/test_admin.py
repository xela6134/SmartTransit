import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
import mysql.connector
import os
from backend.admin import admin_bp
from backend.auth import auth_bp, bcrypt
import json

TEST_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME')
}

@pytest.fixture
def app():
    # Create test Flask app
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 15))

    # Initialise extensions
    jwt = JWTManager(app)
    bcrypt.init_app(app)

    # Register blueprint
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)

    # Clean database before tests
    with app.app_context():
        clear_test_data()

    yield app

    # Cleanup after tests
    with app.app_context():
        clear_test_data()

@pytest.fixture
def client(app):
    return app.test_client()

def clear_test_data():
    # Clear test data from Users table without dropping tables
    conn = mysql.connector.connect(**TEST_CONFIG)
    cursor = conn.cursor()

    try:
        # Delete everything
        cursor.execute("DELETE FROM Operates")
        cursor.execute("DELETE FROM Bookings")
        cursor.execute("DELETE FROM Rides")
        cursor.execute("DELETE FROM Users")
        cursor.execute("DELETE FROM Locations")        
        cursor.execute("DELETE FROM Drivers")
        cursor.execute("DELETE FROM Vehicles")
        cursor.execute("DELETE FROM RevokedTokens")
        
        # Reset auto-increment so we can reuse id_s when db is reset
        cursor.execute("ALTER TABLE Drivers AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE Vehicles AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE Users AUTO_INCREMENT = 1")


        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error cleaning test data: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# Helper function to register a user via the API
def register_user(client, name, email, password):
    return client.post('/auth/register', json={
        'name': name,
        'email': email,
        'password': password,
        'phone_number': "+61426871386"
    })

# Helper function to log in a user via the API
def login_user(client, email, password):
    return client.post('/auth/login', json={
        'email': email,
        'password': password
    })

# Helper function to log in and return auth headers
def get_auth_headers(client, email, password):
    login_res = login_user(client, email, password)
    if login_res.status_code != 200:
        # Raise an error in the test setup if login fails
        pytest.fail(f"Failed to log in user {email} to get token. Status: {login_res.status_code}, Response: {login_res.data}")
    token = login_res.json['access_token']
    return {'Authorization': f'Bearer {token}'}

def test_unsuccessful_admin_privileges(client):
    register_user(client, "admin", "user1@email.com", "password123")
    register_user(client, "user2", "user2@email.com", "password123")

    headers = get_auth_headers(client, "user2@email.com", "password123")

    status_response = client.get('/auth/status', headers=headers)
    assert status_response.status_code == 200

    response = client.post('/auth/admin/register_driver', headers=headers, json={
        'name': 'Driver One',
        'email': 'driver1@example.com',
        'password': 'Pass1234',
        'age': 30,
        'employee_type': 'F'
    })
    assert response.status_code == 403

    response2 = client.post('/auth/admin/add_vehicle', headers=headers, json={
        'capacity': 40,
        'disability_seats': 4,
        'licence_number': '12345678'
    })
    assert response2.status_code == 403

    response3 = client.get('/auth/admin/all_drivers', headers=headers)
    assert response3.status_code == 403

    response4 = client.get('/auth/admin/all_vehicles', headers=headers)
    assert response4.status_code == 403

def test_register_driver_success(client):
    register_user(client, "admin", "user1@email.com", "password123")
    headers = get_auth_headers(client, "user1@email.com", "password123")

    response = client.post('/auth/admin/register_driver', headers=headers, json={
        'name': 'Driver One',
        'email': 'driver1@example.com',
        'password': 'Pass1234',
        'age': 30,
        'employee_type': 'F'
    })
    assert response.status_code == 201

def test_register_driver_fail(client):
    register_user(client, "admin", "user1@email.com", "password123")
    headers = get_auth_headers(client, "user1@email.com", "password123")

    # Missing Fields
    payload_1 = {
        'name': '',
        'email': 'driver1@example.com',
        'password': 'Pass1234',
        'age': 30,
        'employee_type': 'F'
    }
    response_1 = client.post('/auth/admin/register_driver', headers=headers, json=payload_1)
    assert response_1.status_code == 400
    assert response_1.json == {'error': 'Missing required fields (email, password, name)'}

    # Invalid email or password
    payload_2 = {
        'name': 'Sup Chromie',
        'email': 'driver1example.com',
        'password': 'Pass1234',
        'age': 30,
        'employee_type': 'F'
    }
    response_2 = client.post('/auth/admin/register_driver', headers=headers, json=payload_2)
    assert response_2.status_code == 400
    assert response_2.json == {'error': 'Invalid email format!'}

    payload_3 = {
        'name': 'Sup Chromie',
        'email': 'driver1@example.com',
        'password': 'weak.',
        'age': 30,
        'employee_type': 'F'
    }
    response_3 = client.post('/auth/admin/register_driver', headers=headers, json=payload_3)
    assert response_3.status_code == 400
    assert response_3.json == {'error': 'Password must be at least 8 characters long and contain at least one letter and one number!'}

    # Invalid age
    payload_4 = {
        'name': 'Sup Chromie',
        'email': 'driver1@example.com',
        'password': 'Pass1234',
        'age': 'sixty-nine',
        'employee_type': 'F'
    }
    response_4 = client.post('/auth/admin/register_driver', headers=headers, json=payload_4)
    assert response_4.status_code == 400
    assert response_4.json == {'error': 'Age must be an integer'}

    # Invalid Employee Type
    payload_5 = {
        'name': 'Dig Bick',
        'email': 'driver1@example.com',
        'password': 'Pass1234',
        'age': 69,
        'employee_type': 'Fat'
    }
    response_5 = client.post('/auth/admin/register_driver', headers=headers, json=payload_5)
    assert response_5.status_code == 400
    assert response_5.json == {'error': 'employee_type must be a single character'}

    # Using the same email for a new driver
    payload_6 = {
        'name': 'Driver One',
        'email': 'driver1@example.com',
        'password': 'Pass1234',
        'age': 30,
        'employee_type': 'F'
    }
    client.post('/auth/admin/register_driver', headers=headers, json=payload_6)
    response_6 = client.post('/auth/admin/register_driver', headers=headers, json=payload_6)
    assert response_6.status_code == 409
    assert response_6.json == {'error': 'Email already registered!'}

def test_add_vehicle_success(client, app):
    register_user(client, "admin", "user1@email.com", "password123")
    headers = get_auth_headers(client, "user1@email.com", "password123")

    response = client.post('/auth/admin/add_vehicle', headers=headers, json={
        'capacity': 40,
        'disability_seats': 4,
        'licence_number': '12345678'
    })
    assert response.status_code == 201
    assert response.json == {'message': 'Vehicle added successfully'}

def test_add_vehicle_fail(client):
    register_user(client, "admin", "user1@email.com", "password123")
    headers = get_auth_headers(client, "user1@email.com", "password123")

    # Missing Credentials/Fields
    response_1 = client.post('/auth/admin/add_vehicle', headers=headers, json={
        'capacity': 40,
        'licence_number': '12345678'
    })
    assert response_1.status_code == 400
    assert response_1.json == {'error': 'Missing required fields (capacity, disability_seats, licence_number)'}

    # Invalid Licence Number
    response_2 = client.post('/auth/admin/add_vehicle', headers=headers, json={
        'capacity': 40,
        'disability_seats': 4,
        'licence_number': '12345678231321'
    })
    assert response_2.status_code == 400
    assert response_2.json == {'error': 'Licence number must be 8 characters or less'}

    # Capacity is not an integer
    response_3 = client.post('/auth/admin/add_vehicle', headers=headers, json={
        'capacity': 'Sqaure',
        'disability_seats': 4,
        'licence_number': '12345678'
    })
    assert response_3.status_code == 400
    assert response_3.json == {'error': 'capacity must be an integer'}

    # Disability Seats is not an integer
    response_4 = client.post('/auth/admin/add_vehicle', headers=headers, json={
        'capacity': 5,
        'disability_seats': 'I am the lion.',
        'licence_number': '12345678'
    })
    assert response_4.status_code == 400
    assert response_4.json == {'error': 'disability_seats must be an integer'}

    # More disability seats than capacity
    response_5 = client.post('/auth/admin/add_vehicle', headers=headers, json={
        'capacity': 40,
        'disability_seats': 41,
        'licence_number': '12345678'
    })
    assert response_5.status_code == 400
    assert response_5.json == {'error': 'disability_seats cannot be greater than capacity'}
    

def test_list_drivers_success(client):
    register_user(client, "admin", "user1@email.com", "password123")
    headers = get_auth_headers(client, "user1@email.com", "password123")

    client.post('/auth/admin/register_driver', headers=headers, json={
        'name': 'Driver Two',
        'email': 'driver2@example.com',
        'password': 'Pass1234',
        'age': 25,
        'employee_type': 'P'
    })
    client.post('/auth/admin/register_driver', headers=headers, json={
        'name': 'Driver Three',
        'email': 'driver3@example.com',
        'password': 'Pass1234',
        'age': 25,
        'employee_type': 'C'
    })
    response = client.get('/auth/admin/all_drivers', headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json['drivers'], list)
    assert any(d['email'] == 'driver2@example.com' for d in response.json['drivers'])

def test_list_routes_success(client):
    register_user(client, "admin", "user1@email.com", "password123")
    headers = get_auth_headers(client, "user1@email.com", "password123")

    client.post('/auth/admin/add_vehicle', headers=headers, json={
        'capacity': 50,
        'disability_seats': 5,
        'licence_number': '87654321'
    })
    client.post('/auth/admin/add_vehicle', headers=headers, json={
        'capacity': 145,
        'disability_seats': 52,
        'licence_number': '32542422'
    })
    response = client.get('/auth/admin/all_vehicles', headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json['vehicles'], list)
    assert any(v['licence_number'] == '87654321' for v in response.json['vehicles'])