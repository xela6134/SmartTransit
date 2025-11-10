from flask import Blueprint, jsonify, request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
import mysql.connector
from dotenv import load_dotenv
import os, requests
from datetime import datetime
from payment import calculate_ride_price
from custom_decorator import user_only

load_dotenv()

# Constants & Setups

CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME')
}

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

booking_bp = Blueprint('booking', __name__)
bcrypt = Bcrypt()

def get_db_connection():
    return mysql.connector.connect(**CONFIG)

"""
    Initiate Booking
    ---
    Prepares ride info for payment
    Request body (JSON):
    - start_location (int): the location id in the DB
    - end_location (int): the location id in the DB
    
    Logic:
    1. Add a new entry into Rides with the start location and the end location.
       ride_duration is calculated with current time, and ride_status = 'I'.
    2. If a ride exists with the same start and end location where ride_status = 'I'
       don't add a new enty in Rides.

    Returns:
    - 200 OK: {
        "ride_id": ride_id,
        "estimated_duration": ride_duration,
        "estimated_price_cents": ride_price
    }
    - 400 Bad Request: Missing start_location and/or end_location
    - 401 Unauthorized: Not logged in
    - 409 Conflict: User tries to create another incomplete booking (ride_status = 'I') from startLocation to endLocation
                    from startLocation to endLocation
    - 500 Internal Server Error
"""
@booking_bp.route('/booking/initiate', methods=['POST'])
@user_only()
def initiate_booking():
    data = request.get_json()
    user_id = get_jwt_identity()
    start_location = data.get('start_location')
    end_location = data.get('end_location')

    # Check if either location hasn't been specified
    if start_location is None or end_location is None:
        return jsonify({'error': 'Missing start_location or end_location'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) # Access through column names
        
        # Check if the user already has an incomplete booking for the same ride
        cursor.execute(
            """
            SELECT *
            FROM Bookings b
            JOIN Rides r ON b.ride_id = r.ride_id
            WHERE b.user_id = %s
            AND r.ride_status IN ('I', 'A')
            """,
            (user_id,)
        )
        duplicate_booking = cursor.fetchone()
        if duplicate_booking:
            return jsonify({
                'error': 'User already has an ongoing booking.'
            }), 409

        # Step 1: Check if a matching ride already exists where the ride hasn't started or finished
        cursor.execute(
            """
            SELECT ride_id, ride_duration FROM Rides
            WHERE start_location = %s AND end_location = %s
            AND ride_status = 'I'
            """,
            (start_location, end_location)
        )
        ride = cursor.fetchone()
        ride_id = None
        ride_duration = None

        if ride:
            ride_id = ride['ride_id']
            ride_duration = ride['ride_duration']
        else:
            # Calculate duration
            ride_duration = get_estimated_time(start_location, end_location)
            if ride_duration is None:
                return jsonify({'error': 'Could not estimate ride duration'}), 500

            # Step 2: Create a ride entry
            cursor.execute(
                """
                INSERT INTO Rides (start_location, end_location, ride_duration, ride_status)
                VALUES (%s, %s, %s, 'I')
                """,
                (start_location, end_location, ride_duration)
            )
            conn.commit()

            # Get the new ride_id
            ride_id = cursor.lastrowid
            
        # Step 3: Check if user already has a PAID booking for this specific ride_id
        cursor.execute(
            "SELECT ride_id FROM Bookings WHERE ride_id = %s AND user_id = %s",
            (ride_id, user_id)
        )
        existing_booking = cursor.fetchone()
        if existing_booking:
            return jsonify({'error': 'You have already booked this ride.'}), 409
        
        # Step 4: Return Ride Info and price for Payment
        ride_price = calculate_ride_price(ride_duration)
        
        ride_price = round(ride_price, 2)
        ride_duration = round(ride_duration, 2)
        
        return jsonify({
            "ride_id": ride_id,
            "estimated_duration": ride_duration,
            "estimated_price_cents": ride_price,
            "start_location": start_location,
            "end_location": end_location
        }), 200

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'error': 'An unexpected error occured'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

"""
    View Bookings
    ---
    Retrieve all bookings for the authenticated user.
    
    Logic:
    1. Join the Bookings and Rides tables to obtain ride details along with the booking date.
    2. Return ride information such as ride_id, start_location, end_location, ride_date,
       ride_duration, ride_status.
       
    Returns:
    - 200 OK: {
        "bookings": [{
            "ride_id": <ride_id>,
            "start_location": <start_location>,
            "end_location": <end_location>,
            "ride_date": <ride_date>,
            "ride_duration": <ride_duration>,
            "ride_status": <ride_status>,
        }, ...]
    }
    - 401 Unauthorized: Invalid credentials.
    - 500 Internal Server Error: Database error.
"""
@booking_bp.route('/booking/view', methods=['GET'])
@user_only()
def viewBookings():
    userId = get_jwt_identity()
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get all the necessary information
        query = """
            SELECT r.ride_id, l1.location_name AS start_location, 
                   l2.location_name AS end_location, 
                   r.ride_duration, r.ride_status
            FROM Bookings b
            JOIN Rides r ON b.ride_id = r.ride_id
            JOIN Locations l1 ON r.start_location = l1.location_id
            JOIN Locations l2 ON r.end_location = l2.location_id
            WHERE b.user_id = %s
        """
        cursor.execute(query, (userId,))
        results = cursor.fetchall()
        
        if not results:
            return jsonify({"message": "User has no bookings", "bookings": []}), 200

        # Append the results in bookings
        bookings = []
        for row in results:
            bookings.append({
                "ride_id": row["ride_id"],
                "start_location": row["start_location"],
                "end_location": row["end_location"],
                "ride_duration": row["ride_duration"],
                "ride_status": row["ride_status"],
            })
        return jsonify({"bookings": bookings}), 200

    except mysql.connector.Error as err:
        return jsonify({'error': 'Database error', 'details': str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

"""
    Update Pending Ride Durations
    ---
    For every ride in the Rides table where ride_status = 'I',
    this function retrieves the estimated travel time using the get_estimated_time function,
    and updates the ride_duration column accordingly. (This will be used sometime)
    
    Logic:
    1. Query all rides from the Rides table where ride_status = 'I'
    2. For each ride, call get_estimated_time(start_location, end_location) to get the estimated travel time.
    3. Update the ride_duration field with the retrieved estimated time.
"""
def update_pending_ride_durations():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Retrieve rides that haven't started or finished.
        cursor.execute("""
            SELECT ride_id, start_location, end_location 
            FROM Rides 
            WHERE ride_status = 'I'
        """)
        rides = cursor.fetchall()
        
        for ride in rides:
            ride_id = ride["ride_id"]
            start_location_id = ride["start_location"]
            end_location_id = ride["end_location"]

            # Use the existing get_estimated_time function to compute travel time (in minutes)
            estimated_time = get_estimated_time(start_location_id, end_location_id)
            if estimated_time is not None:
                cursor.execute(
                    "UPDATE Rides SET ride_duration = %s WHERE ride_id = %s",
                    (estimated_time, ride_id)
                )
            else:
                print(f"Could not retrieve estimated time for ride_id {ride_id} (from {start_location_id} to {end_location_id}).")
        
        conn.commit()
    except mysql.connector.Error as err:
        print("Database error:", err)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

"""
    Helper function to retrieve the estimated travel time (in minutes) between 
    two locations specified by their location IDs in the Locations table using 
    the Google Maps Directions API.

    Parameters:
        start_location_id (int): The ID of the starting location in the database.
        end_location_id (int): The ID of the destination location in the database.
        
    Returns:
        float: Estimated travel time in minutes, or None if the API call fails
               or one of the locations cannot be found.
"""
def get_estimated_time(start_location_id, end_location_id):
    # Retrieve coordinates for start and end locations from the database
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get start location coordinates
        cursor.execute(
            "SELECT x_coordinate, y_coordinate FROM Locations WHERE location_id = %s",
            (start_location_id,)
        )
        start_loc = cursor.fetchone()
        if not start_loc:
            return None

        # Get end location coordinates
        cursor.execute(
            "SELECT x_coordinate, y_coordinate from Locations WHERE location_id = %s",
            (end_location_id,)
        )
        end_loc = cursor.fetchone()
        if not end_loc:
            print(f"End location with ID {end_location_id} not found.")
            return None
        
        # Map database coordinates to API parameters.
        # Here we assume x_coordinate represents latitude and y_coordinate longitude
        origin = {"lat": start_loc["x_coordinate"], "lng": start_loc["y_coordinate"]}
        destination = {"lat": end_loc["x_coordinate"], "lng": end_loc["y_coordinate"]}
    finally:
        cursor.close()
        conn.close()

    # Prepare the API request to Google Maps Directions API
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{origin['lat']},{origin['lng']}",
        "destination": f"{destination['lat']},{destination['lng']}",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=5)
        data = response.json()
        if data.get("status") == "OK" and data.get("routes"):
            # Use the first route and its first leg
            leg = data["routes"][0]["legs"][0]
            duration_sec = leg["duration"]["value"]
            duration_min = duration_sec / 60.0
            return duration_min
        else:
            print("Error retrieving directions from Google Maps API. Status:", data.get("status"))
            return None
    except Exception as e:
        print("Exception during API call:", e)
        return None
