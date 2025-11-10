from flask import Response, stream_with_context, Blueprint, jsonify, request
from flask_bcrypt import Bcrypt
from flask_jwt_extended import jwt_required
from datetime import timedelta
import mysql.connector
from dotenv import load_dotenv
import os
from datetime import timedelta
import requests
from custom_decorator import admin_only

load_dotenv()

# Constants & Setups

CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME'),
}

# JWT configuration
jwt_secret_key = os.getenv('JWT_SECRET_KEY')
jwt_access_expires = timedelta(minutes=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 15)))

location_bp = Blueprint('location', __name__)
bcrypt = Bcrypt()

def get_db_connection():
    return mysql.connector.connect(**CONFIG)

"""
    Add a location to the database
    ---
    Get the input of the operator and insert into database.
    Request body (JSON):
    - location_name (str): name of the location to be added
    - x_coordinate (str): x-coordinate of the location
    - y_coordinate (str): y-coordinate of the location
    Returns:
    - 200 OK: Successfully added
    - 400 Bad Request: Missing x-coordinate, y-coordinate, duplicate location_name
    - 403 Unauthorized: Admin only route
    - 500 Internal Server Error: Database error
"""
@location_bp.route('/location/create', methods=['POST'])
@admin_only() # As admin
def addLocation():
    data = request.get_json()

    locationName = str(data.get('location_name'))
    xCoordinate = float(data.get('x_coordinate'))
    yCoordinate = float(data.get('y_coordinate'))
    # Start DB connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT location_name from Locations")
        allLocation = [data[0].lower() for data in cursor.fetchall()]
        
        if (locationName.lower() in allLocation):
            return jsonify({'error': 'Duplicated Location Name'}), 400
        
        # If no error has been found, insert into locations
        cursor.execute('INSERT INTO Locations (location_name, x_coordinate, y_coordinate) VALUES (%s, %s, %s)',
                       (locationName, xCoordinate, yCoordinate))
        conn.commit()

        cursor.execute("SELECT * FROM Locations WHERE location_name = %s", (locationName,))
        newLocationId = cursor.fetchall()[0][0]

        return jsonify({'message': 'Location added', 'location_id': str(newLocationId)}), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

"""
    Show all the locations to users, operators and drivers
    ---
    Query the database for a list of all the currently available pickup locations

    Returns:
    - 200 OK: Successfully shown all pickup locations
    - 401 Unauthorized: Not logged in as anything
    - 500 Internal Server Error: Database error
"""
@location_bp.route('/location', methods=['GET'])
@jwt_required() # As admins, users and drivers
def getLocations():
    try:
        # Add the location into an array
        locations = []
        # Start DB connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Locations")
        
        # Append each location data in list
        for location in cursor.fetchall():
            locationObj = {
                "location_id": location[0],
                "location_name": location[1],
                "x_coordinate": float(location[2]),
                "y_coordinate": float(location[3]),
            }
            locations.append(locationObj)
        return jsonify({"message": "Location listed", "locations": locations}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

"""
    Delete a location
    ---
    Get the id of the location and delete it from database.

    Returns:
    - 200 OK: Successfully destroyed
    - 400 Bad Request: Location is not found
    - 401 Unauthorized: Not logged in as anything
    - 500 Internal Server Error: Database error
"""
@location_bp.route('/location/<id>', methods=['DELETE'])
@admin_only() # As admins only
def deleteLocation(id):
    try:
        # Start DB connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM Locations WHERE location_id = %s", (id,))
        result = cursor.fetchall()
        
        # Handle case where location is not found        
        if len(result) == 0:
            return jsonify({'error': 'Location is not found'}), 400

        cursor.execute("SELECT ride_id FROM Rides WHERE start_location = %s OR end_location= %s", (id, id))

        # Delete all the associated data as well
        for ride in cursor.fetchall():
            rideId = ride["ride_id"]
            cursor.execute("DELETE FROM Bookings WHERE ride_id =" + str(rideId))
            cursor.execute("DELETE FROM Rides WHERE ride_id=" + str(rideId))
        
        cursor.execute("DELETE FROM Locations WHERE location_id=" + id)
        conn.commit()
        return jsonify({'message': 'Successfully exterminated the location'}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@location_bp.route('/directions', methods=['GET'])
def get_directions():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    
    if not origin or not destination:
        return jsonify({'error': 'Both origin and destination are required.'}), 400

    google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    directions_url = (
        f"https://maps.googleapis.com/maps/api/directions/json"
        f"?origin={origin}"
        f"&destination={destination}"
        f"&departure_time=now"
        f"&key={google_maps_api_key}"
    )
    
    try:
        response = requests.get(directions_url, timeout=15, stream=True)

        # Optional: log the content length if available
        print("Fetched directions, content length:", response.headers.get('Content-Length'))

        # Generator to yield the content in chunks
        def generate():
            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk

        # Return a streaming response
        response_headers = {'Content-Type': 'application/json', 'Connection': 'keep-alive'}
        return Response(stream_with_context(generate()), 
                        status=response.status_code, 
                        headers=response_headers)
    except Exception as err:
        return jsonify({'error': 'Error fetching directions', 'details': str(err)}), 500
