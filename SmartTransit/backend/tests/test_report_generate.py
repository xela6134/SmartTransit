import pytest
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from backend.report_generate import route_gen_bp
import mysql.connector
import os
import pprint as pp
from backend.auth import auth_bp, bcrypt
from names_generator import generate_name
from random import randint
import random
from datetime import datetime as dt
import phonenumbers

bcrypt = Bcrypt()
access_token = None

from dotenv import load_dotenv
load_dotenv()
today = dt.today().strftime('%Y-%m-%d')

TEST_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME')
}

conn = mysql.connector.connect(**TEST_CONFIG)
cursor = conn.cursor()

# Helper function to register a user via the API
def register_user(client, name="Test User", email="test@example.com", password="Password123"):
    return client.post('/auth/register', json={
        'name': name,
        'email': email,
        'password': password
    })

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

    # Register blueprint
    app.register_blueprint(route_gen_bp)
    
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def close_db():
    cursor.execute("DELETE FROM Bookings")
    cursor.execute("DELETE FROM Operates")
    cursor.execute("DELETE FROM Rides")
    cursor.execute("DELETE FROM Users")
    cursor.execute("DELETE FROM Locations")
    cursor.execute("DELETE FROM Drivers")
    cursor.execute("DELETE FROM Vehicles")
    cursor.execute("ALTER TABLE Users AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE Rides AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE Bookings AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE Locations AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE Drivers AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE Vehicles AUTO_INCREMENT = 1")

    conn.rollback()
    cursor.close()
    conn.close()

@pytest.fixture(scope="session", autouse=True)
def init_db(request):
    #Insert test data and initilise connection
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

        cursor.execute("INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES (\"Taman Botani Putrajaya\", 2.9456905105411244, 101.69552778052814)")
        cursor.execute("INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES (\"SplashMania WaterPark\", 2.8941380184914514, 101.61723825574)")
        cursor.execute("INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES (\"Embun Resort Putrajaya\", 2.901970767377098, 101.720348001138)")
        cursor.execute("INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES (\"Raja Haji Fisabilillah Mosque\", 2.9360120541693138, 101.64924144683476)")
        cursor.execute("INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES (\"Kuala Lumpur International Airport\", 2.742562238864031, 101.7013405254904)")
        cursor.execute("INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES (\"Xiamen University Malaysia\", 2.8363818888542016, 101.7043806614408)")
        cursor.execute("INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES (\"Hospital Banting\", 2.804855893883764, 101.50129864142178)")

        hashed_password = bcrypt.generate_password_hash('validpassword1').decode('utf-8')
        email = "login@example.com"
        user = "Login User"
        phone_num = "+61419007079"
        # phone_number = phonenumbers.format_number("+61419007079", phonenumbers.PhoneNumberFormat.E164)

        cursor.execute("INSERT INTO Users (name, email, password_hash, phone_number) VALUES (%s, %s, %s, %s)", (user, email, hashed_password, phone_num))

        for i in range(0,101):
            name = generate_name(seed=i, style='capital')
            
            cursor.execute("INSERT INTO Users (name) VALUES (\"%s\")"), (name, )

        cursor.execute("INSERT INTO Rides (start_location, end_location, ride_status, profit, ride_duration, environmental) VALUES (5, 7, 'C', 1000, 765.232, 1212)")
        cursor.execute("INSERT INTO Rides (start_location, end_location, ride_status, profit, ride_duration, environmental) VALUES (1, 4, 'C', 2000, 343.121, 424.12)")
        cursor.execute("INSERT INTO Rides (start_location, end_location, ride_status, profit, ride_duration, environmental) VALUES (2, 6, 'C', 3000, 314.121, 4332.132)")
        cursor.execute("INSERT INTO Rides (start_location, end_location, ride_status, profit, ride_duration, environmental) VALUES (3, 7, 'C', 4000, 31.121, 3421.12)")
        cursor.execute("INSERT INTO Rides (start_location, end_location, ride_status, profit, ride_duration, environmental) VALUES (5, 6, 'C', 5000, 23.912, 1212.41)")

        random.seed(10)
        for i in range(0,101):
            rid = randint(1, 5)
            uid = randint(1, 100)
            if i % 4 == 0:
                cursor.execute("""
                    INSERT INTO Bookings (ride_id, user_id, ride_date) VALUES (%s, %s, "2025-03-01")
                """,  (int(rid), int(uid))
                )
            if i % 4 == 1:
                cursor.execute("""
                    INSERT INTO Bookings (ride_id, user_id, ride_date) VALUES (%s, %s, "2025-03-02")
                """,  (int(rid), int(uid))
                )
            if i % 4 == 2:
                cursor.execute("""
                    INSERT INTO Bookings (ride_id, user_id, ride_date) VALUES (%s, %s, "2025-03-03")
                """,  (int(rid), int(uid))
                )
            if i % 4 == 3:
                cursor.execute("""
                    INSERT INTO Bookings (ride_id, user_id, ride_date) VALUES (%s, %s, "2025-03-04")
                """,  (int(rid), int(uid))
                )
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error initialising test data: {err}")
        conn.rollback()
        cursor.close()
        conn.close()
        exit(0)

    request.addfinalizer(close_db)

def test_report_gen_success(client):
    # Login
    access_token = client.post('/auth/login', json={
        'email': 'login@example.com',
        'password': 'validpassword1',
        'phone_number': '+61419007079'
    }).json['access_token']

    response = client.put('/report/generate', headers={'Authorization': f'Bearer {access_token}'}, json={
        'date_range': ("2025-03-01", "2025-03-04")
    })

    assert response.status_code == 200
    res = response.json['report']
    assert res is not None
    
    for i in res:
        assert i['ride_id'] is not None
        assert i['number_passengers'] is not None
        assert i['passengers'] is not None
        assert i['start_location'] is not None
        assert i['end_location'] is not None
        assert i['profit'] is not None
        assert i['ride_date'] is not None
        assert i['ride_duration'] is not None
        assert i['environmental'] is not None

    logout_response = client.post('/auth/logout', headers={'Authorization': f'Bearer {access_token}'})

    assert logout_response.status_code == 200

def test_report_invalid_date_param(client):
    # Login
    access_token = client.post('/auth/login', json={
        'email': 'login@example.com',
        'password': 'validpassword1',
        'phone_number': '+61419007079'
    }).json['access_token']

    response = client.put('/report/generate', headers={'Authorization': f'Bearer {access_token}'}, json={
        'date_range': ()
    })

    response = client.put('/report/generate', headers={'Authorization': f'Bearer {access_token}'}, json={
        'date_range': ("2025/03/01", "2025/03/04", "2025/03/05")
    })

    assert response.status_code == 400

    response = client.put('/report/generate', headers={'Authorization': f'Bearer {access_token}'}, json={
        'date_range': ("", "2025-03-04")
    })

    assert response.status_code == 400

    response = client.put('/report/generate', headers={'Authorization': f'Bearer {access_token}'}, json={
        'date_range': ("2025-03-01", "")
    })

    assert response.status_code == 400

    response = client.put('/report/generate', headers={'Authorization': f'Bearer {access_token}'}, json={
        'date_range': ("", "")
    })

    assert response.status_code == 400

    response = client.put('/report/generate', headers={'Authorization': f'Bearer {access_token}'}, json={
        'date_range': (20250301, 20250304)
    })

    assert response.status_code == 400

def test_report_invalid_dates(client):
    # Login
    access_token = client.post('/auth/login', json={
        'email': 'login@example.com',
        'password': 'validpassword1',
        'phone_number': '+61419007079'
    }).json['access_token']
    
    response = client.put('/report/generate', headers={'Authorization': f'Bearer {access_token}'}, json={
        'date_range': ("2025-03-04", "2025-03-01")
    })

    assert response.status_code == 400

    response = client.put('/report/generate', headers={'Authorization': f'Bearer {access_token}'}, json={
        'date_range': (today, today)
    })

    assert response.status_code == 400

    response = client.put('/report/generate', headers={'Authorization': f'Bearer {access_token}'}, json={
        'date_range': ("2025/03/01", "2025/03/04")
    })

    assert response.status_code == 400

    response = client.put('/report/generate', headers={'Authorization': f'Bearer {access_token}'}, json={
        'date_range': ("2025--03--01", "2025--03--04")
    })

    assert response.status_code == 400

    response = client.put('/report/generate', headers={'Authorization': f'Bearer {access_token}'}, json={
        'date_range': ("20250301", "20250304")
    })

    assert response.status_code == 400

    response = client.put('/report/generate', headers={'Authorization': f'Bearer {access_token}'}, json={
        'date_range': ("2025\\03\\01", "2025\\03\\04")
    })

    assert response.status_code == 400

    response = client.put('/report/generate', headers={'Authorization': f'Bearer {access_token}'}, json={
        'date_range': ("01-03-2025", "04-03-2025")
    })

    assert response.status_code == 400
