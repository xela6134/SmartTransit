import os
import pytest
import mysql.connector
from flask import Flask
from flask_jwt_extended import JWTManager
from backend.auth import auth_bp, bcrypt, register_jwt_blocklist_loader, close_db_connection
from backend.settings import settings_bp

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.test'), override=True)

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
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = JWT_SECRET
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = JWT_EXPIRES_MINUTES
    app.config["JWT_BLOCKLIST_ENABLED"] = True

    jwt = JWTManager(app)
    bcrypt.init_app(app)
    register_jwt_blocklist_loader(jwt)

    app.teardown_appcontext(close_db_connection)
    app.register_blueprint(auth_bp)
    app.register_blueprint(settings_bp)

    clear_test_data()
    yield app
    clear_test_data()

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

def clear_test_data():
    conn = mysql.connector.connect(**TEST_CONFIG)
    cursor = conn.cursor()
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DELETE FROM Bookings")
        cursor.execute("DELETE FROM Operates")
        cursor.execute("DELETE FROM Rides")
        cursor.execute("DELETE FROM Users")
        cursor.execute("DELETE FROM Locations")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()
    finally:
        cursor.close()
        conn.close()

#################### Helpers ####################

def register_user(client, name="Test User", email="user@example.com", password="Password123"):
    return client.post('/auth/register', json={
        'name': name,
        'email': email,
        'password': password,
        'phone_number': "+61412345678"
    })

def login_user(client, email="user@example.com", password="Password123"):
    return client.post('/auth/login', json={
        'email': email,
        'password': password
    })

def get_auth_headers(client, email="user@example.com", password="Password123"):
    res = login_user(client, email, password)
    if res.status_code != 200:
        pytest.fail(f"Login failed: {res.json}")
    token = res.json["access_token"]
    return {"Authorization": f"Bearer {token}"}

#################### Tests ####################

def test_settings_get_user_info_success(client):
    register_user(client)
    headers = get_auth_headers(client)
    response = client.get('/settings/profile', headers=headers)
    
    assert response.status_code == 200
    data = response.json
    assert data["name"] == "Test User"
    assert data["email"] == "user@example.com"

def test_settings_edit_profile_success(client):
    register_user(client)
    headers = get_auth_headers(client)

    patch_data = {
        "name": "Updated User",
        "email": "updated@example.com",
        "age": 30,
        "phone_number": "+61498765432",
        "disability": 1,
        "password": "NewPassword123"
    }

    response = client.patch('/settings/profile/edit', json=patch_data, headers=headers)
    assert response.status_code == 200

    updated = response.json
    assert updated["name"] == "Updated User"
    assert updated["email"] == "updated@example.com"
    assert updated["age"] == 30
    assert updated["phone_number"] == "+61498765432"
    assert updated["disability"] is True  # Since 1 is cast to True

def test_settings_edit_profile_partial_update(client):
    register_user(client, email="partial@example.com")
    headers = get_auth_headers(client, email="partial@example.com")

    patch_data = {
        "name": "Partial Update",
        "email": "partial_update@example.com",
        "age": 25,
        "phone_number": "+61499999999",
        "disability": 0
        # No password update
    }

    response = client.patch('/settings/profile/edit', json=patch_data, headers=headers)
    assert response.status_code == 200
    data = response.json
    assert data["name"] == "Partial Update"
    assert data["disability"] is False
