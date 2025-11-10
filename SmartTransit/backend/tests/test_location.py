import os
from dotenv import load_dotenv
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager
import mysql.connector
from backend.auth import auth_bp, bcrypt
from backend.location import location_bp
import json
# Determine the path to .env.test
env_path = os.path.join('..', '.env.test')
load_dotenv(
    dotenv_path=env_path,
    override=True
)  # Load test environment variables

TEST_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME')
}

print(os.getenv('DB_PASSWORD'))

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
    # Register location
    app.register_blueprint(location_bp)

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
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("TRUNCATE TABLE Users")
        cursor.execute("TRUNCATE TABLE Bookings")
        cursor.execute("TRUNCATE TABLE Operates")
        cursor.execute("TRUNCATE TABLE Rides")
        cursor.execute("TRUNCATE TABLE Locations")
        cursor.execute("TRUNCATE TABLE Drivers")
        cursor.execute("TRUNCATE TABLE Vehicles")
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error cleaning test data: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def test_location_show_logged_in(client):
    # Register first
    client.post('/auth/register', json={
        'name': 'Login User',
        'email': 'login@example.com',
        'password': 'validpassword1',
        'phone_number': '+61419007079'
    })
    # Login
    access_token = client.post('/auth/login', json={
        'email': 'login@example.com',
        'password': 'validpassword1',
        'phone_number': '+61419007079'
    }).json['access_token']

    response = client.get(
        '/location',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    assert response.status_code == 200
    assert 'Location listed' in response.text

def test_location_show_when_not_logged_in(client):
    response = client.get('/location')
    assert response.status_code == 401


def test_location_delete(client):
    conn = mysql.connector.connect(**TEST_CONFIG)
    cursor = conn.cursor(buffered=True)
    cursor.execute(
        """INSERT INTO Locations (location_name, x_coordinate, y_coordinate)
        VALUES ('Their House', 9.0, 5.0)""",
    )
    conn.commit()

    cursor.execute("SELECT * FROM Locations where location_name='Their House'")
    newLocationId = cursor.fetchone()[0]

    # Register first
    client.post('/auth/register', json={
        'name': 'Login User',
        'email': 'login@example.com',
        'password': 'validpassword1',
        'phone_number': '+61419007079'
    })
    # Login
    access_token = client.post('/auth/login', json={
        'email': 'login@example.com',
        'password': 'validpassword1',
        'phone_number': '+61419007079'
    }).json['access_token']

    response = client.delete(
        '/location/' + str(newLocationId),
        headers={'Authorization': f'Bearer {access_token}'}
    )
    assert response.status_code == 200

def test_location_add(client):
    conn = mysql.connector.connect(**TEST_CONFIG)
    cursor = conn.cursor(buffered=True)
    # Register first
    client.post('/auth/register', json={
        'name': 'Login User',
        'email': 'login@example.com',
        'password': 'validpassword1',
        'phone_number': '+61419007079'
    })
    # Login
    access_token = client.post('/auth/login', json={
        'email': 'login@example.com',
        'password': 'validpassword1',
        'phone_number': '+61419007079'
    }).json['access_token']

    response = client.post('/location/create', json={
        'location_name': 'Their House',
        'x_coordinate': '6.232',
        'y_coordinate': '3.12321'
    }, headers={'Authorization': f'Bearer {access_token}'})
    assert response.status_code == 200

    locationId = json.loads(response.text)['location_id']
    #Delete the location
    response = client.delete(
        '/location/' + str(locationId),
        headers={'Authorization': f'Bearer {access_token}'}
    )

def test_location_admin_only_access(client):
    conn = mysql.connector.connect(**TEST_CONFIG)
    cursor = conn.cursor(buffered=True)
    # Register admin
    client.post('/auth/register', json={
        'name': 'KK Leong',
        'email': 'KK@gottheswag.com',
        'password': 'indonesiasocoolLOL123',
        'phone_number': '+61419007079'
    })
    # register another user
    client.post('/auth/register', json={
        'name': 'Normal User',
        'email': 'login@example.com',
        'password': 'validpassword1',
        'phone_number': '+61419007078'
    })
    # login regular user
    access_token_user = client.post('/auth/login', json={
        'email': 'login@example.com',
        'password': 'validpassword1',
        'phone_number': '+61419007078'
    }).json['access_token']
    # regular user can not make location
    response = client.post('/location/create', json={
        'location_name': 'Malaysia Airport',
        'x_coordinate': '120.232',
        'y_coordinate': '232.12321'
    }, headers={'Authorization': f'Bearer {access_token_user}'})
    assert response.status_code == 403
    # admin logs in and makes location
    access_token_admin = client.post('/auth/login', json={
        'email': 'KK@gottheswag.com',
        'password': 'indonesiasocoolLOL123',
        'phone_number': '+61419007079'
    }).json['access_token']

    response = client.post('/location/create', json={
        'location_name': 'Malaysia Airport',
        'x_coordinate': '120.232',
        'y_coordinate': '232.12321'
    }, headers={'Authorization': f'Bearer {access_token_admin}'})
    assert response.status_code == 200
    # User can not delete location
    response = client.delete(
        '/location/' + str(1),
        headers={'Authorization': f'Bearer {access_token_user}'}
    )
    assert response.status_code == 403
    # Admin can delete location, assume location id is 1
    response = client.delete(
        '/location/' + str(1),
        headers={'Authorization': f'Bearer {access_token_admin}'}
    )
    assert response.status_code == 200

def test_location_delete_not_found(client):
    client.post('/auth/register', json={
        'name': 'Admin User',
        'email': 'admin@deletecase.com',
        'password': 'ValidPass123',
        'phone_number': '+61400000001'
    })
    
    token = client.post('/auth/login', json={
        'email': 'admin@deletecase.com',
        'password': 'ValidPass123'
    }).json['access_token']

    # Try deleting a location that doesn't exist
    response = client.delete('/location/99999', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 400

def test_location_get_directions_valid(client):
    # 3.14827, lng: 101.616
    
    response = client.get('/directions', query_string={
        'origin': 3.14827,
        'destination': 101.616
    })
    
    print(response.data)
    assert response.status_code == 200


