import pytest
from flask import Flask
from flask_jwt_extended import JWTManager
import mysql.connector
import os
from backend.driver import driver_bp, bcrypt, driver_register, add_vehicle
from backend.auth import register_jwt_blocklist_loader
import json
import time
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
    register_jwt_blocklist_loader(jwt)

    # Register blueprint
    app.register_blueprint(driver_bp)

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
        # Delete all Drivers
        cursor.execute("DELETE FROM Drivers")
        # Delete all Vehicles
        cursor.execute("DELETE FROM Vehicles")
        # Delete all revoked tokens
        cursor.execute("DELETE FROM RevokedTokens")
        # Reset auto-increment so we can reuse driver_ids when db is reset
        cursor.execute("ALTER TABLE Drivers AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE Vehicles AUTO_INCREMENT = 1")


        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error cleaning test data: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def test_driver_login(client, app):
    with app.app_context():  
        driver_register('test@example.com', 'password123', 'Test Driver')

    response = client.post('/auth/driver/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })

    assert response.status_code == 200
    assert 'access_token' in response.get_json()

def test_driver_failed_login(client, app):
    with app.app_context():  
        driver_register('test@example.com', 'password123', 'Test Driver')

    response = client.post('/auth/driver/login', json={
        'email': 'test@example.com',
        'password': 'wrongpassword123'
    })

    assert response.status_code == 401

def test_driver_logout(client, app):
    with app.app_context():  
        driver_register('test@example.com', 'password123', 'Test Driver')
        add_vehicle(20, "ABD")

    login_res = client.post('/auth/driver/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })

    token = login_res.json['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    logout_response = client.post('/auth/driver/logout', headers=headers)

    assert logout_response.status_code == 200
    assert logout_response.json == {'message': 'Successfully logged out'}

    # Verify token is now blocked by trying to access a protected route
    assign_response = client.post('/driver/assign_vehicle', headers=headers, json={'licence_number': "ABD"})
    assert assign_response.status_code == 401 # Access should be denied

def test_driver_assign_fail(client, app):
    with app.app_context():  
        driver_register('test@example.com', 'password123', 'Test Driver')
        add_vehicle(20, "ABD")
    
    login_res = client.post('/auth/driver/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })

    token = login_res.json['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # Missing licence number
    response_1 = client.post('/driver/assign_vehicle', headers=headers, json={'licence_number': ""})
    assert response_1.status_code == 400
    assert response_1.json == {'error': 'Missing vehicle licence number'}

    # Licence number is not a valid vehicle
    response_2 = client.post('/driver/assign_vehicle', headers=headers, json={'licence_number': "ABCD"})
    assert response_2.status_code == 404
    assert response_2.json == {'error': 'Vehicle not found'}

def test_driver_assign(client, app):
    with app.app_context():  
        driver_register('test@example.com', 'password123', 'Test Driver')
        add_vehicle(20, "ABD")
    
    login_res = client.post('/auth/driver/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })

    token = login_res.json['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    response = client.post('/driver/assign_vehicle', headers=headers, json={'licence_number': "ABD"})
    assert response.status_code == 200
    assert response.json == {'message': 'Vehicle assigned successfully'}

def test_driver_unassign_fail(client, app):
    with app.app_context():  
        driver_register('test@example.com', 'password123', 'Test Driver')
        add_vehicle(20, "CATBALL")
        add_vehicle(15, "HUH")
    
    login_res = client.post('/auth/driver/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })

    token = login_res.json['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    client.post('/driver/assign_vehicle', headers=headers, json={'licence_number': "CATBALL"})

    # Missing licence number
    response_1 = client.post('/driver/unassign_vehicle', headers=headers, json={'licence_number': ""})
    assert response_1.status_code == 400
    assert response_1.json == {'error': 'Missing vehicle licence number'}

    # Licence number is not a valid vehicle
    response_2 = client.post('/driver/unassign_vehicle', headers=headers, json={'licence_number': "ABCD"})
    assert response_2.status_code == 404
    assert response_2.json == {'error': 'Vehicle not found'}

    # Given Licence number is not assigned to driver
    response_3 = client.post('/driver/unassign_vehicle', headers=headers, json={'licence_number': "HUH"})
    assert response_3.status_code == 400
    assert response_3.json == {'error': 'Driver is not assigned to the given vehicle'}

def test_driver_unassign(client, app):
    with app.app_context():  
        driver_register('test@example.com', 'password123', 'Test Driver')
        add_vehicle(20, "ABD")
    
    login_res = client.post('/auth/driver/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })

    token = login_res.json['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    client.post('/driver/assign_vehicle', headers=headers, json={'licence_number': "ABD"})

    response = client.post('/driver/unassign_vehicle', headers=headers, json={'licence_number': "ABD"})
    assert response.status_code == 200
    assert response.json == {'message': 'Vehicle unassigned successfully'}

def test_driver_update_location(client, app):
    with app.app_context():  
        driver_register('test@example.com', 'password123', 'Test Driver')
        add_vehicle(20, "ABD")
    
    login_res = client.post('/auth/driver/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })

    token = login_res.json['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    assign_response = client.post('/driver/assign_vehicle', headers=headers, json={'licence_number': "ABD"})
    assert assign_response.status_code == 200

    locationUpdateResponse = client.patch('/driver/updateLocation', headers=headers,
                                          json={
                                              'latitude': str(2.32324),
                                              'longitude': str(3.23212)
                                          })
    assert locationUpdateResponse.status_code == 200
    time.sleep(2)
    locationUpdateResponse = client.patch('/driver/updateLocation', headers=headers,
                                          json={
                                              'latitude': str(3.32324),
                                              'longitude': str(3.53212)
                                          })
    assert locationUpdateResponse.status_code == 200

    logout_response = client.post('/auth/driver/logout', headers=headers)

    assert logout_response.status_code == 200
    assert logout_response.json == {'message': 'Successfully logged out'}

