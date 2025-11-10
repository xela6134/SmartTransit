import os
from dotenv import load_dotenv
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager
import mysql.connector
from backend.auth import auth_bp, bcrypt, register_jwt_blocklist_loader, close_db_connection
from backend.booking import booking_bp
from backend.admin import admin_bp
from backend.driver import driver_bp
try:
    # Assumes .env.test is in the parent directory of the 'tests' directory
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env.test')
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"Loaded test environment from: {os.path.abspath(env_path)}")
except Exception as e:
    print(f"Warning: Could not load .env.test file: {e}")

TEST_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME')
}

JWT_SECRET = os.getenv('JWT_SECRET_KEY')
JWT_EXPIRES_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 15))

@pytest.fixture(scope='module')
def app():
    # Create test Flask app
    flask_app = Flask(__name__)
    flask_app.config['TESTING'] = True
    flask_app.config['JWT_SECRET_KEY'] = JWT_SECRET
    flask_app.config['JWT_ACCESS_TOKEN_EXPIRES'] = JWT_EXPIRES_MINUTES
    
    # Enable JWT blocklisting feature in Flask-JWT-Extended
    flask_app.config["JWT_BLOCKLIST_ENABLED"] = True

    # Initialise extensions
    jwt = JWTManager(flask_app)
    bcrypt.init_app(flask_app)
    
    # Register the callback function that checks the RevokedTokens table
    register_jwt_blocklist_loader(jwt)
    
    # Close db when done
    flask_app.teardown_appcontext(close_db_connection)

    # Register blueprint
    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(booking_bp)
    flask_app.register_blueprint(admin_bp)
    flask_app.register_blueprint(driver_bp)

    # Database Setup/Teardown for the module
    print("\nClearing test database before module tests...")
    clear_test_data() # Ensure clean state before any tests run
    yield flask_app
    
    print("\nClearing test database after module tests...")
    clear_test_data() # Clean up after all tests in the module are done
        
@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

################## HELPER FUNCTIONS #####################

def clear_test_data():
    # Clear test data from Users table without dropping tables
    conn = mysql.connector.connect(**TEST_CONFIG)
    cursor = conn.cursor()

    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # Clear users and revoked tokens
        cursor.execute("TRUNCATE TABLE Users")
        cursor.execute("TRUNCATE TABLE RevokedTokens")
        cursor.execute("TRUNCATE TABLE Drivers")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error cleaning test data: {err}")
        if conn: conn.rollback()
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# Helper function to register a user via the API
def register_user(client, email, password, name="John"):
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


#Check that the admin can't access users and driver routes
def test_bad_access_as_admin(client, app):
    response = register_user(client, email='admin@example.com', password='Password123')
    response = login_user(client, email='admin@example.com', password='Password123')
    access_token = response.json['access_token']
    assert response.status_code == 200
    assert 'access_token' in response.json
    assert isinstance(response.json['access_token'], str)
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/booking/view', headers=headers)

    assert response.status_code == 403
    assert response.json['msg'] == "Users only!"

    response = client.post('/driver/assign_vehicle', headers=headers)

 
    assert response.status_code == 403
    assert response.json['msg'] == "Drivers only!"

#Check that the user can't access admin and driver routes
def test_bad_access_as_user(client, app):
    #Create Admin
    response = register_user(client, email='admin@example.com', password='Password123')
    response = login_user(client, email='admin@example.com', password='Password123')
    access_token = response.json['access_token']
    assert response.status_code == 200
    assert 'access_token' in response.json
    assert isinstance(response.json['access_token'], str)
    #Create user
    response = register_user(client, email='user@example.com', password='Password123')
    response = login_user(client, email='user@example.com', password='Password123')
    access_token = response.json['access_token']
    assert response.status_code == 200
    assert 'access_token' in response.json
    assert isinstance(response.json['access_token'], str)
    headers = {'Authorization': f'Bearer {access_token}'}

    response = client.post('/auth/admin/register_driver', headers=headers)
 
    assert response.status_code == 403
    assert response.json['msg'] == "Admins only!"

    response = client.post('/driver/assign_vehicle', headers=headers)

 
    assert response.status_code == 403
    assert response.json['msg'] == "Drivers only!"

#Check that the drivers can't access users and admins routes
def test_bad_access_as_driver(client, app):
    #Create Admin
    response = register_user(client, email='admin@example.com', password='Password123')
    response = login_user(client, email='admin@example.com', password='Password123')
    access_token = response.json['access_token']
    assert response.status_code == 200
    assert 'access_token' in response.json
    assert isinstance(response.json['access_token'], str)

    #Create driver
    headers = {'Authorization': f'Bearer {access_token}'}

    response = client.post(
        '/auth/admin/register_driver',
        json={
            "name": "Jeffzzzzzzre",
            "email": "jeff3434@gmail.com",
            "password": "password123",
            "age": 50,
            "employee_type": "F"
        },
        headers=headers
    )
    
    assert response.status_code == 201
    assert client.post('/auth/logout', headers=headers).status_code == 200
    response = client.post(
        '/auth/driver/login',
        json={
            "email": "jeff3434@gmail.com",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    access_token = response.json['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}

    response = client.post('/auth/admin/register_driver', headers=headers)
    assert response.status_code == 403
    assert response.json['msg'] == "Admins only!"

    response = client.get('/booking/view', headers=headers)
    assert response.status_code == 403
    assert response.json['msg'] == "Users only!"