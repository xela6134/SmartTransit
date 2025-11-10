import pytest
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from backend.route_optimisation import route_op_bp
from backend.driver import driver_bp, bcrypt, driver_register, add_vehicle
import mysql.connector
import os
import json
import pprint as pp
import requests

bcrypt = Bcrypt()

from dotenv import load_dotenv
load_dotenv()

TEST_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME')
}

conn = mysql.connector.connect(**TEST_CONFIG)
cursor = conn.cursor()

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
    app.register_blueprint(route_op_bp)
    app.register_blueprint(driver_bp)
    with app.app_context():
        driver_register('test@example.com', 'password123', 'Test Driver')
        driver_register('test2@example.com', 'password123', 'Test Driver 2')
        add_vehicle(20, "AUS-319")
        add_vehicle(20, "SIN-120")
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
        # cursor.execute("SET FOREIGN_KEY_CHECKS=0")

        cursor.execute("INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES (\"Taman Botani Putrajaya\", 2.9456905105411244, 101.69552778052814)")
        cursor.execute("INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES (\"SplashMania WaterPark\", 2.8941380184914514, 101.61723825574)")
        cursor.execute("INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES (\"Embun Resort Putrajaya\", 2.901970767377098, 101.720348001138)")
        cursor.execute("INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES (\"Raja Haji Fisabilillah Mosque\", 2.9360120541693138, 101.64924144683476)")
        cursor.execute("INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES (\"Kuala Lumpur International Airport\", 2.742562238864031, 101.7013405254904)")
        cursor.execute("INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES (\"Xiamen University Malaysia\", 2.8363818888542016, 101.7043806614408)")
        cursor.execute("INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES (\"Hospital Banting\", 2.804855893883764, 101.50129864142178)")

        cursor.execute("INSERT INTO Vehicles (capacity, disability_seats, x_coordinate, y_coordinate) VALUES (30, 5, 2.8001301358507744, 101.61802053391877)")
        cursor.execute("INSERT INTO Vehicles (capacity, disability_seats, x_coordinate, y_coordinate) VALUES (25, 3, 2.8001301358507744, 101.61802053391877)")
        cursor.execute("INSERT INTO Vehicles (capacity, disability_seats, x_coordinate, y_coordinate) VALUES (10, 1, 2.8001301358507744, 101.61802053391877)")
        cursor.execute("INSERT INTO Vehicles (capacity, disability_seats, x_coordinate, y_coordinate) VALUES (20, 8, 2.8001301358507744, 101.61802053391877)")

        # cursor.execute("INSERT INTO Drivers (name, age, assigned_vehicle) VALUES (\"Michelle Yeoh\", 40, 3)")
        # cursor.execute("INSERT INTO Drivers (name, age, assigned_vehicle) VALUES (\"Nicholas Teo\", 32, 4)")
        # cursor.execute("INSERT INTO Drivers (name, age, assigned_vehicle) VALUES (\"Amber Chia\", 29, 5)")
        # cursor.execute("INSERT INTO Drivers (name, age, assigned_vehicle) VALUES (\"Joe Biden\", 85, 6)")

        cursor.execute("INSERT INTO Users (name) VALUES (\"Danny Quah\")")
        cursor.execute("INSERT INTO Users (name) VALUES (\"Halim Saad\")")
        cursor.execute("INSERT INTO Users (name) VALUES (\"Yi Ren Ng\")")
        cursor.execute("INSERT INTO Users (name) VALUES (\"Christopher Lee\")")
        cursor.execute("INSERT INTO Users (name) VALUES (\"Nabil Ahmad\")")
        cursor.execute("INSERT INTO Users (name) VALUES (\"Siti Aisyah Alias\")")
        cursor.execute("INSERT INTO Users (name) VALUES (\"Tan Sri Lim Kit Siang\")")
        cursor.execute("INSERT INTO Users (name) VALUES (\"Yeoh Seng Zoe\")")
        cursor.execute("INSERT INTO Users (name) VALUES (\"Valeree Siow\")")
        cursor.execute("INSERT INTO Users (name) VALUES (\"Jazeman Jaafar\")")

        cursor.execute("INSERT INTO Rides (start_location, end_location, ride_status) VALUES (5, 7, 'I')")
        cursor.execute("INSERT INTO Rides (start_location, end_location, ride_status) VALUES (1, 4, 'I')")
        cursor.execute("INSERT INTO Rides (start_location, end_location, ride_status) VALUES (2, 6, 'I')")
        cursor.execute("INSERT INTO Rides (start_location, end_location, ride_status) VALUES (3, 7, 'I')")
        cursor.execute("INSERT INTO Rides (start_location, end_location, ride_status) VALUES (5, 6, 'I')")
        cursor.execute("INSERT INTO Rides (start_location, end_location, ride_status) VALUES (3, 4, 'I')")

        cursor.execute("INSERT INTO Bookings (ride_id, user_id) VALUES (1, 1)")
        cursor.execute("INSERT INTO Bookings (ride_id, user_id) VALUES (1, 2)")
        cursor.execute("INSERT INTO Bookings (ride_id, user_id) VALUES (2, 3)")
        cursor.execute("INSERT INTO Bookings (ride_id, user_id) VALUES (2, 4)")
        cursor.execute("INSERT INTO Bookings (ride_id, user_id) VALUES (2, 5)")
        cursor.execute("INSERT INTO Bookings (ride_id, user_id) VALUES (3, 6)")
        cursor.execute("INSERT INTO Bookings (ride_id, user_id) VALUES (4, 7)")
        cursor.execute("INSERT INTO Bookings (ride_id, user_id) VALUES (4, 8)")
        cursor.execute("INSERT INTO Bookings (ride_id, user_id) VALUES (5, 9)")

        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error cleaning test data: {err}")
        conn.rollback()
        cursor.close()
        conn.close()
        exit(1)

    request.addfinalizer(close_db)

def test_optimization_booking_start_success(client):
    response = client.post('/auth/driver/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })

    assert response.status_code == 200
    assert 'access_token' in response.get_json()

    token = response.json['access_token']
    tokenHeaders = {'Authorization': f'Bearer {token}'}
    assign_response = client.post('/driver/assign_vehicle', headers=tokenHeaders, json={'licence_number': "SIN-120"})

    assert assign_response.status_code == 200

    response = client.post('/route/start', json={  
        'lat': "2.9456905105411212", 
        'lng': "101.69552778052843"
    }, headers=tokenHeaders)

    assert response.status_code == 200

    res = response.json['route']
    assert len(res) == 3
    ride_deets = res[1]
    assert res[0] is not None
    assert ride_deets.get("ride_id") is not None
    assert ride_deets.get("num_passengers") is not None
    assert ride_deets.get("passengers") is not None
    assert ride_deets.get("num_passengers") is not None
    assert ride_deets.get("start_name") is not None
    assert ride_deets.get("start_x_coordinate") is not None
    assert ride_deets.get("start_y_coordinate") is not None
    assert ride_deets.get("end_name") is not None
    assert ride_deets.get("end_x_coordinate") is not None
    assert ride_deets.get("end_y_coordinate") is not None
    assert ride_deets.get("time_veh_arrive") is not None
    assert ride_deets.get("time_start_end") is not None
    assert res[2] is not None

    # Check relevant rables updated
    cursor.execute(
        """
        SELECT driver_id
        FROM Operates
        where ride_id = %s
        """, (ride_deets.get("ride_id"),)
    )

    ret_id = cursor.fetchone()[0]
    assert ret_id == 1

    cursor.execute(
        """
        SELECT ride_duration, ride_status, profit, environmental
        FROM Rides
        where ride_id = %s
        """, (ride_deets.get("ride_id"),)
    )
    ret = cursor.fetchone()
    response = client.post('/route/end', json={
        'ride_id': 1
    }, headers=tokenHeaders)


    assert "{0:.2f}".format(ret[0]) == "{0:.2f}".format(ride_deets.get("time_start_end"))
    assert ret[1] == 'A'
    assert "{0:.2f}".format(ret[2]) == "{0:.2f}".format(res[0])
    assert "{0:.3f}".format(ret[3]) == "{0:.3f}".format(res[2])


def test_optimization_booking_start_end_rides(client):
    #first driver login
    response = client.post('/auth/driver/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })

    assert response.status_code == 200
    assert 'access_token' in response.get_json()

    token = response.json['access_token']
    tokenHeaders = {'Authorization': f'Bearer {token}'}
    assign_response = client.post('/driver/assign_vehicle', headers=tokenHeaders, json={'licence_number': "SIN-120"})

    assert assign_response.status_code == 200

    response = client.post('/route/start', json={  
        'lat': "2.9456905105411212", 
        'lng': "101.69552778052843"
    }, headers=tokenHeaders)

    first_ride = response.json['route'][1].get("ride_id")

    assert response.status_code == 200

    response = client.post('/route/start', json={  
        'lat': "2.9456905105411212", 
        'lng': "101.69552778052843"
    }, headers=tokenHeaders)

    assert response.status_code == 403

    response = client.post('/route/end', json={
        'ride_id': first_ride
    }, headers=tokenHeaders)

    assert response.status_code == 200

def test_optimization_multiple_drivers(client):
    #first driver login
    response = client.post('/auth/driver/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })

    assert response.status_code == 200
    assert 'access_token' in response.get_json()

    token = response.json['access_token']
    tokenHeaders1 = {'Authorization': f'Bearer {token}'}
    assign_response = client.post('/driver/assign_vehicle', headers=tokenHeaders1, json={'licence_number': "SIN-120"})

    response = client.post('/route/start', json={
        'lat': "2.9456905105411212", 
        'lng': "101.69552778052843"
    }, headers=tokenHeaders1)

    assert response.status_code == 200

    first_ride = response.json['route'][1].get("ride_id")
    #Second Driver Login
    response = client.post('/auth/driver/login', json={
        'email': 'test2@example.com',
        'password': 'password123'
    })

    assert response.status_code == 200
    assert 'access_token' in response.get_json()

    token = response.json['access_token']
    tokenHeaders2 = {'Authorization': f'Bearer {token}'}
    assign_response = client.post('/driver/assign_vehicle', headers=tokenHeaders2, json={'licence_number': "AUS-319"})

    assert assign_response.status_code == 200

    response = client.post('/route/start', json={
         'lat': "2.9456905105411123", 
        'lng': "101.69552778052912"
    }, headers=tokenHeaders2)

    assert response.status_code == 200
    second_ride = response.json['route'][1].get("ride_id")

    assert first_ride != second_ride

    response = client.post('/route/end', json={
        "ride_id": first_ride
    }, headers=tokenHeaders1)
 
    assert response.status_code == 200

    response = client.post('/route/end', json={
        "ride_id": second_ride
    }, headers=tokenHeaders2)

    assert response.status_code == 200

def test_optimization_driver_enroute(client):
    #first driver login
    response = client.post('/auth/driver/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })

    assert response.status_code == 200
    assert 'access_token' in response.get_json()

    token = response.json['access_token']
    tokenHeaders1 = {'Authorization': f'Bearer {token}'}
    assign_response = client.post('/driver/assign_vehicle', headers=tokenHeaders1, json={'licence_number': "AUS-319"})

    assert assign_response.status_code == 200

    response = client.post('/route/start', json={
        'lat': "2.9456905105411123", 
        'lng': "101.69552778052912"
    }, headers=tokenHeaders1)

    assert response.status_code == 200

    first_ride = response.json['route'][1].get("ride_id")

    response = client.post('/route/start', json={
        'lat': "2.9456905105411123", 
        'lng': "101.69552778052912"
    }, headers=tokenHeaders1)

    assert response.status_code == 403

    response = client.post('/route/end', json={
        "ride_id": first_ride
    }, headers=tokenHeaders1)

    assert response.status_code == 200
