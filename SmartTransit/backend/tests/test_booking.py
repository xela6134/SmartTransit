import pytest
from flask import Flask
from flask_jwt_extended import JWTManager
import mysql.connector
import os
from backend.auth import auth_bp, bcrypt
from backend.booking import booking_bp
from datetime import datetime
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
    app.register_blueprint(auth_bp)
    app.register_blueprint(booking_bp)

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

        cursor.execute("ALTER TABLE Users AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE Rides AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE Bookings AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE Locations AUTO_INCREMENT = 1")

        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error cleaning test data: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

############### HELPER FUNCTIONS ###############

def register_user(client, email="booking@example.com", password="Password123", ensure_non_admin=True):
    if ensure_non_admin:
        # Dummy admin
        client.post('/auth/register', json={
            'name': "Admin Placeholder",
            'email': "admin@example.com",
            'password': "Password123",
            'phone_number': "+61400000000"
        })

    return client.post('/auth/register', json={
        'name': "Booking User",
        'email': email,
        'password': password,
        'phone_number': "+61426871386"
    })


def login_user(client, email="booking@example.com", password="Password123"):
    return client.post('/auth/login', json={
        'email': email,
        'password': password
    })

def get_auth_headers(client, email="booking@example.com", password="Password123"):
    login_res = login_user(client, email, password)
    
    token = login_res.json['access_token']
    return {'Authorization': f'Bearer {token}'}

def create_locations():
    conn = mysql.connector.connect(**TEST_CONFIG)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES ('A', -33.86, 151.21)")
        cursor.execute("INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES ('B', -33.87, 151.22)")
        conn.commit()

    finally:
        cursor.close()
        conn.close()


def get_location_ids():
    conn = mysql.connector.connect(**TEST_CONFIG)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT location_id FROM Locations ORDER BY location_id ASC LIMIT 2")
        return [row[0] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()

def insert_example_booking():
    conn = mysql.connector.connect(**TEST_CONFIG)
    cursor = conn.cursor()
    try:
        booking_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO Bookings (ride_id, user_id, ride_date) VALUES (%s, %s, %s)", (1, 2, booking_time))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


############### TEST CASES ###############

def test_booking_initiation_success(client):
    register_user(client)
    headers = get_auth_headers(client)

    create_locations()
    start_id, end_id = get_location_ids()

    response = client.post('/booking/initiate', json={
        "start_location": start_id,
        "end_location": end_id
    }, headers=headers)

    assert response.status_code == 200
    data = response.json
    
    assert "ride_id" in data
    assert "estimated_duration" in data
    assert "estimated_price_cents" in data

def test_booking_duplicate_conflict(client):
    register_user(client)
    headers = get_auth_headers(client)
    
    create_locations()
    start_id, end_id = get_location_ids()

    # First booking
    client.post('/booking/initiate', json={
        "start_location": start_id,
        "end_location": end_id
    }, headers=headers)
    
    # This assumes we call the Stripe payment, and the example booking data has been inserted
    insert_example_booking()
    
    # Second booking for same ride
    response = client.post('/booking/initiate', json={
        "start_location": start_id,
        "end_location": end_id
    }, headers=headers)

    assert response.status_code == 409
    assert "error" in response.json

def test_booking_view(client):
    register_user(client)
    headers = get_auth_headers(client)
    response = client.get('/booking/view', headers=headers)
    assert response.status_code == 200
    assert "bookings" in response.json
    assert isinstance(response.json["bookings"], list)

def test_booking_initiate_missing_fields(client):
    register_user(client)
    headers = get_auth_headers(client)
    create_locations()
    _, end_id = get_location_ids()

    response = client.post('/booking/initiate', json={
        # start_location is missing
        "end_location": end_id
    }, headers=headers)

    assert response.status_code == 400
    assert "error" in response.json
    assert "start_location" in response.json["error"]

def test_booking_initiate_invalid_location_ids(client):
    register_user(client)
    headers = get_auth_headers(client)

    response = client.post('/booking/initiate', json={
        "start_location": 9999,
        "end_location": 9998
    }, headers=headers)

    assert response.status_code in (400, 500)
    assert "error" in response.json

def test_booking_view_after_initiation(client):
    register_user(client)
    headers = get_auth_headers(client)

    create_locations()
    start_id, end_id = get_location_ids()

    response = client.post('/booking/initiate', json={
        "start_location": start_id,
        "end_location": end_id
    }, headers=headers)
    
    # This assumes we call the Stripe payment, and the example booking data has been inserted
    insert_example_booking()

    response = client.get('/booking/view', headers=headers)
    assert response.status_code == 200
    assert "bookings" in response.json
    assert isinstance(response.json["bookings"], list)
    assert len(response.json["bookings"]) >= 1

def test_booking_initiate_unauthenticated(client):
    create_locations()
    start_id, end_id = get_location_ids()

    response = client.post('/booking/initiate', json={
        "start_location": start_id,
        "end_location": end_id
    })  # No headers

    assert response.status_code == 401
    assert "error" in response.json or "msg" in response.json

