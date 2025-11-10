from flask import Blueprint, jsonify, request
from flask_bcrypt import Bcrypt
import mysql.connector
from dotenv import load_dotenv
import os
from datetime import datetime as dt
import re
from custom_decorator import admin_only
load_dotenv()

# Constants & Setups

CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME')
}

route_gen_bp = Blueprint('route_generate', __name__)
bcrypt = Bcrypt()
today = dt.today().strftime('%Y-%m-%d')

def get_db_connection():
    return mysql.connector.connect(**CONFIG)

"""
    Route Generate Report
    ---
    Generates a report for routes in dB for a range of dates (inclusive, inclusive). 
    Dates are given in ISO 8601 standard and should be quoted in double quotes. 
    Request body (JSON):
    - date_range (tuple): tuple containing the range of date
    For 1 date: ("2025-03-25", "2025-03-25"), for 2 dates (range): ("2025-03-14", "2025-04-26")
    date_2 must be > than date_1

    Returns: Array of dictionaries
    - 200 OK: report: [{
            "ride_id": rideid,
            "number_passengers":  number of passengers,
            "passengers": array of passenger userids [user_id],
            "start_location": start location name,
            "end_location": end location name,
            "ride_duration": time of journey from start to end location,
            "profit": profit from ride journey
            "ride_date": date of ride
            "environmental": amount of carbon emissions saved from journey
        }]
    - 400 Bad Request: Missing date range
    - 400 Bad Request: len(date_range) != 2
    - 400 Bad Request: Invalid date (regex)
    - 400 Bad request: Invalid date range
    - 400 Bad Request: Route is current or future day
    - 403 Unauthorized Request: Route requested by non-admin
    - 500 Internal Server Error: Database error
"""
@route_gen_bp.route('/report/generate', methods=['PUT'])
@admin_only()
def generate():
    data = request.get_json()
    date_range = list(data.get('date_range'))
    
    # Different error checking
    # Return 400 for all invalid inputs
    if date_range is None:
        return jsonify({'error': 'Missing date range'}), 400
    
    if (len(date_range) != 2):
        return jsonify({'error': 'Invalid number of dates'}), 400
    
    if (not isinstance(date_range[0], str) or not isinstance(date_range[1], str)):
        return jsonify({'error': 'Date not a string'}), 400
    
    if (not re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", date_range[0]) 
        or not re.match(r"[0-9]{4}-[0-9]{2}-[0-9]{2}$", date_range[1])):
        return jsonify({'error': 'Invalid date format'}), 400
    
    if (date_range[1] < date_range[0]):
        return jsonify({'error': 'Invalid date range'}), 400
    
    if (date_range[1] >= today or date_range[0] >= today):
        return jsonify({'error': 'Can not query report for current or future date'}), 400

    # Report generation
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT DISTINCT ride_id, ride_date
            FROM Bookings
            WHERE ride_date BETWEEN %s AND %s
            ORDER BY ride_date ASC
            """
        
        start_datetime = f"{date_range[0]} 00:00:00.000000"
        end_datetime = f"{date_range[1]} 23:59:59.999999"
        
        cursor.execute(query, (start_datetime, end_datetime))
        all_rides = cursor.fetchall()

        ride_details = []
        
        # Add necessary fields to each ride_details
        for rideid, ridedate in all_rides:
            cursor.execute(
                """
                SELECT count(*)
                FROM Bookings
                WHERE ride_id = %s
                """, (rideid,)
            )
            headcount = cursor.fetchone()

            cursor.execute(
                """
                SELECT user_id
                FROM Bookings
                WHERE ride_id = %s
                """, (rideid,)
            )
            all_users = cursor.fetchall()

            cursor.execute(
                """
                SELECT start_location, end_location, ride_duration, profit, environmental
                FROM Rides
                WHERE ride_id = %s
                """, (rideid,)
            )
            ride_deets = cursor.fetchone()

            if not ride_deets:
                continue

            cursor.execute(
                """
                SELECT location_name
                FROM Locations
                WHERE location_id  = %s
                """, (ride_deets[0],)
            )
            start_location = cursor.fetchone()

            cursor.execute(
                """
                SELECT location_name
                FROM Locations
                WHERE location_id  = %s
                """, (ride_deets[1],)
            )
            end_location = cursor.fetchone()

            # Add into one JSON, then append to ride_details
            ride_details.append({
                "ride_id": rideid,
                "ride_date": ridedate,
                "number_passengers": headcount[0],
                "passengers": [user[0] for user in all_users],
                "start_location": start_location,
                "end_location": end_location,
                "ride_duration": ride_deets[2],
                "profit": ride_deets[3],
                "environmental": ride_deets[4]
            })
            
            return jsonify({
                "report": ride_details 
            }), 200
    except Exception as err:
        return jsonify({'error': 'Internal Error', 'details': str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        