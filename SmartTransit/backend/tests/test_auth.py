import os
from dotenv import load_dotenv
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager
import mysql.connector
from backend.auth import auth_bp, bcrypt, register_jwt_blocklist_loader, close_db_connection

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
        
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error cleaning test data: {err}")
        if conn: conn.rollback()
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# Helper function to register a user via the API
def register_user(client, name="Test User", email="test@example.com", password="Password123"):
    return client.post('/auth/register', json={
        'name': name,
        'email': email,
        'password': password,
        'phone_number': "+61426871386"
    })

# Helper function to log in a user via the API
def login_user(client, email="test@example.com", password="Password123"):
    return client.post('/auth/login', json={
        'email': email,
        'password': password
    })

# Helper function to log in and return auth headers
def get_auth_headers(client, email="test@example.com", password="Password123"):
    login_res = login_user(client, email, password)
    if login_res.status_code != 200:
        # Raise an error in the test setup if login fails
        pytest.fail(f"Failed to log in user {email} to get token. Status: {login_res.status_code}, Response: {login_res.data}")
    token = login_res.json['access_token']
    return {'Authorization': f'Bearer {token}'}

        
def test_register_success(client):
    # Test successful user registration
    response = register_user(client, 'Test User', 'test@example.com', 'Password123')
    assert response.status_code == 201
    assert response.json == {'message': 'User registered successfully'}
    
@pytest.mark.parametrize("name, email, password, expected_error_part, status_code", [
    (None, 'test@example.com', 'Password123', 'Missing required fields', 400),            # None as fields
    ('Test User', None, 'Password123', 'Missing required fields', 400),
    ('Test User', 'test@example.com', None, 'Missing required fields', 400),
    ('', 'test@example.com', 'Password123', 'Missing required fields', 400),
    ('Test User', '', 'Password123', 'Missing required fields', 400),                     # Empty as fields
    ('Test User', 'test@example.com', '', 'Missing required fields', 400),
    ('Test User', 'invalid-email', 'Password123', 'Invalid email format', 400),           # Invalid emails
    ('Test User', 'test@example', 'Password123', 'Invalid email format', 400),
    ('Test User', 'test@example.com', 'short', 'Password must be at least 8', 400),
    ('Test User', 'test@example.com', 'onlyletters', 'Password must be at least 8', 400), # Regex needs number
    ('Test User', 'test@example.com', '12345678', 'Password must be at least 8', 400),    # Regex needs letter
])
def test_register_invalid_input(client, name, email, password, expected_error_part, status_code):
    """Verify registration fails correctly with various invalid inputs."""
    response = client.post('/auth/register', json={'name': name, 'email': email, 'password': password})
    assert response.status_code == status_code
    assert expected_error_part in response.json['error']
    
def test_login_success(client):
    register_user(client, email='login@example.com', password='Password123')
    response = login_user(client, email='login@example.com', password='Password123')
    assert response.status_code == 200
    assert 'access_token' in response.json
    assert isinstance(response.json['access_token'], str)

def test_logout_success_and_token_revoked(client):
    # Register and Login
    register_user(client, email='logout@example.com', password='Password123')
    headers = get_auth_headers(client, email='logout@example.com', password='Password123')

    # Logout
    logout_response = client.post('/auth/logout', headers=headers)
    assert logout_response.status_code == 200
    assert logout_response.json == {'message': 'Successfully logged out'}

    # Verify token is now blocked by trying to access a protected route
    status_response = client.get('/auth/status', headers=headers)
    assert status_response.status_code == 401 # Access should be denied
    # Check for the specific message that shows revocation
    assert 'Token has been revoked' in status_response.json.get('msg', status_response.json.get('message', ''))

def test_get_profile_success(client):
    register_user(client, name="Profile Tester", email="profile@example.com", password="TestPassword123")
    headers = get_auth_headers(client, email="profile@example.com", password="TestPassword123")

    response = client.get('/auth/profile', headers=headers)

    assert response.status_code == 200
    data = response.json

    assert data["name"] == "Profile Tester"
    assert data["email"] == "profile@example.com"
    assert "age" in data
    assert "phone_number" in data
    assert "disability" in data

def test_verify_password(client):
    register_user(client, email="verifier@example.com", password="Secret123")
    headers = get_auth_headers(client, email="verifier@example.com", password="Secret123")

    # Correct password
    correct_response = client.post('/auth/verify_password', json={"password": "Secret123"}, headers=headers)
    assert correct_response.status_code == 200
    assert correct_response.json == {"message": "Password verified"}

    # Incorrect password
    wrong_response = client.post('/auth/verify_password', json={"password": "WrongPass"}, headers=headers)
    assert wrong_response.status_code == 401
    assert "Incorrect password" in wrong_response.json["error"]

    # No password provided
    missing_response = client.post('/auth/verify_password', json={}, headers=headers)
    assert missing_response.status_code == 400
    assert "Password is required" in missing_response.json["error"]
