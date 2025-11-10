import boto3.session
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from flask_bcrypt import Bcrypt
import mysql.connector
from dotenv import load_dotenv
import os
import requests
load_dotenv()
import heapq
import boto3
from custom_decorator import driver_only

# Constants & Setups

CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME')
}

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

SET_PROFIT_CONSTANT = 30
SET_COST_CONSTANT = 2

CARBON_PER_PASSENGER_PER_MINUTE_BUS = 0.885
CARBON_PER_PER_MINUTE_CAR = 2.83

route_op_bp = Blueprint('route_optimisation', __name__)
bcrypt = Bcrypt()

def get_db_connection():
    return mysql.connector.connect(**CONFIG)

def get_travel_time(origin, destination):
    """
    Calls the Google Maps Directions API to get the travel time (in minutes)
    from the origin to the destination.
    
    Parameters:
        origin (dict): Dictionary with keys "lat" and "lng" for the starting point.
        destination (dict): Dictionary with keys "lat" and "lng" for the destination.
    
    Returns:
        float: Travel time in minutes, or None if not available.
    """
    try:
        if not origin or not destination:
            return None
        if not origin.get("lat") or not origin.get("lng") or not destination.get("lat") or not destination.get("lng"):
            return None

        base_url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": f"{origin['lat']},{origin['lng']}",
            "destination": f"{destination['lat']},{destination['lng']}",
            "key": GOOGLE_MAPS_API_KEY
        }

        response = requests.get(base_url, params=params)
        data = response.json()
        if data["status"] == "OK" and data["routes"]:
            duration_sec = data["routes"][0]["legs"][0]["duration"]["value"]
            return duration_sec / 60.0
        else:
            return None
    except Exception as e:
        print(f"Exception during API call: {e}")
        return None

"""
    Route Start
    ---
    Starts a route when vehicle wants to.
    Request body (JSON):
    - driver_id (int): id of driver that wants to start ride

    Returns: Array of 3 elements [float, dictionary, float]
    - 200 OK: route: [
        profit of ride (float), 
        {
            "ride_id": rideid,
            "num_passengers": number of pasengers,
            "passengers": array of passenger userids [user_id],
            "start_name": start location name,
            "start_x_coordinate": start location xcoord,
            "start_y_coordinate": start location ycoord,
            "end_name": end location name,
            "end_x_coordinate": end location xcoord,
            "end_y_coordinate": end location ycoord,
            "time_start_end": time of journey from start to end location,
            "time_veh_start": time for bus to get to start location,
        },
        carbon emissions saved from ride (float)
        ]
    - 400 Bad Request: Missing driver id
    - 400 Bad Request: No waiting passengers
    - 401 Unauthorized Request: Driver of id does not exist
    - 403 Forbidden Request: Driver already on a route
    - 500 Internal Server Error: Database error
"""
@route_op_bp.route('/route/start', methods=['POST'])
@driver_only()
def startRoute():
    d_id = get_jwt_identity()
    data = request.get_json()
    try:
        driver_lat = float(data.get("lat"))
        driver_lng = float(data.get("lng"))
        if driver_lat == 0.0 and driver_lng == 0.0:
            raise ValueError("Fallback GPS coordinates received (0,0)")
    except (TypeError, ValueError) as e:
        print(f"Invalid location data: {e}")
        return jsonify({'error': 'Invalid or missing driver location'}), 400
    
    # 400, no vehicle id
    if d_id == None:
        return jsonify({
            'error': 'Missing driver id'
        }), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # 401, driver not in db

        cursor.execute(
            """
            SELECT driver_id
            FROM Drivers
            WHERE driver_id = %s
            """, (d_id,)
        )

        check_did = cursor.fetchone()
        if check_did is None:
            return jsonify({
                    'error': 'Driver not in dB'
                }), 401

        # 403, driver on route and cannot request to start another
        cursor.execute(
            """
            SELECT r.ride_status
            FROM Operates o
            JOIN Rides r ON o.ride_id = r.ride_id
            WHERE o.driver_id = %s
            """, (d_id,)
        )

        driver_ops = cursor.fetchall()

        if len(driver_ops) >= 1:
            driver_ops = [x[0] for x in driver_ops]
            if driver_ops.count('A') >= 1: 
                return jsonify({
                    'error': 'Driver already enroute'
                }), 403
    except Exception as err:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Internal Error', 'details': str(err)}), 500

    # 1) Get vId of vehicle driver is driving
    # 2) First query non-active routes (get the ride_id)
    # 3) Next query the ammount of passengers waiting at 
    # each pickup point (look through bookings and get a 
    # count for each ride an an array of passenger ids)
    # 4) Get coordinates for locations and vehicle
    # 5) Run algo
    # 6) Make the chosen ride active and return the 
    # details of the ride and passengers
    try:
        cursor.execute(
            """
            SELECT assigned_vehicle
            FROM Drivers
            WHERE driver_id = %s
            """, (d_id, )
        )

        vid = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT *
            FROM Rides
            WHERE ride_status = 'I'
            """
        )

        potential_rides = list([i[0] for i in cursor.fetchall()])

        if not potential_rides:
            return jsonify({
                'error': 'No rides available with waiting passengers'
            }), 400  # No rides available for passengers

        ride_details = []

        for rideid in potential_rides:
            cursor.execute(
                """
                SELECT user_id
                FROM Bookings
                WHERE ride_id = %s
                """, (rideid, )
            )

            # List of user_ids
            passengers = list(cursor.fetchall())
            head_count = len(passengers)

            cursor.execute(
                """
                SELECT start_location, end_location
                FROM Rides
                WHERE ride_id = %s
                """, (rideid,)
            )

            start_end_loc = cursor.fetchone()
            start_loc = start_end_loc[0]
            end_loc = start_end_loc[1]

            cursor.execute(
                """
                SELECT x_coordinate, y_coordinate, location_name 
                FROM Locations 
                WHERE location_id = %s
                """, (start_loc,)
            )

            start_coords = cursor.fetchone()

            # 0th entry x coord, 1st entry y coord
            start_loc_xcoord = start_coords[0]
            start_loc_ycoord = start_coords[1]
            start_name = start_coords[2]

            cursor.execute(
                """
                SELECT x_coordinate, y_coordinate, location_name 
                FROM Locations 
                WHERE location_id = %s
                """, (end_loc,)
            )

            end_coords = cursor.fetchone()

            end_loc_xcoord = end_coords[0]
            end_loc_ycoord = end_coords[1]
            end_name = end_coords[2]
            
            ride_details.append({
                "ride_id": rideid,
                "num_passengers": head_count,
                "passengers": passengers,
                "start_name": start_name,
                "start_x_coordinate": start_loc_xcoord,
                "start_y_coordinate": start_loc_ycoord,
                "end_name": end_name,
                "end_x_coordinate": end_loc_xcoord,
                "end_y_coordinate": end_loc_ycoord
            })
    

        vehicle_x_coord = float(driver_lat)
        vehicle_y_coord = float(driver_lng)

        # Route optimisation algorithm
        heap = []
        for rides in ride_details:
            dist_start_end =  get_travel_time({
                "location_name": rides.get("start_name"), 
                "lat": rides.get("start_x_coordinate"), 
                "lng": rides.get("start_y_coordinate")
            }, {
                "location_name": rides.get("end_name"), 
                "lat": rides.get("end_x_coordinate"), 
                "lng": rides.get("end_y_coordinate")
            })

            dist_veh_start =  get_travel_time({
                "location_name": f"Vehicle: {vid}", 
                "lat": vehicle_x_coord, 
                "lng": vehicle_y_coord
            }, {
                "location_name": rides.get("start_name"), 
                "lat": rides.get("start_x_coordinate"), 
                "lng": rides.get("start_y_coordinate")
            })

            # Currently setting profit constant, will need to get this from client (via frontend or db)
            profit = rides.get("num_passengers") * (dist_start_end * SET_PROFIT_CONSTANT)

            # Currently setting cost constant, will need to get this from client (via frontend or db)
            route_profit = profit * rides.get("num_passengers") - SET_COST_CONSTANT * (dist_start_end + dist_veh_start)
            detailed_rides = rides
            detailed_rides['time_veh_arrive'] = dist_veh_start
            detailed_rides['time_start_end'] = dist_start_end
            carbon_saved = (CARBON_PER_PER_MINUTE_CAR * rides.get("num_passengers") * dist_start_end) 
            - CARBON_PER_PASSENGER_PER_MINUTE_BUS * rides.get("num_passengers") * (dist_start_end + dist_veh_start)

            heapq.heappush(heap, (-1 * route_profit, detailed_rides, carbon_saved))
        
        route_chosen = list(heapq.heappop(heap))

        route_chosen[0] = -1 * route_chosen[0]
        route_chosen_profit = route_chosen[0]
        route_chosen_details = route_chosen[1]
        cursor.execute(
            """
            UPDATE Rides
            SET ride_status='A', profit=%s, ride_duration=%s, environmental=%s
            WHERE ride_id = %s
            """, (route_chosen_profit, route_chosen_details.get("time_start_end"), route_chosen[2], route_chosen_details.get("ride_id"))
        )
        conn.commit()

        cursor.execute(
            """
            INSERT INTO Operates
            (driver_id, ride_id)
            VALUES
            (%s, %s)
            """, (d_id, route_chosen_details.get("ride_id"))
        )
        conn.commit()

        sendSMSToUsers(route_chosen[1]["passengers"], cursor, route_chosen[1]["start_name"],
                       route_chosen[1]["end_name"], route_chosen[1]["time_start_end"],
                       route_chosen[1]["time_veh_arrive"])
        return jsonify({
            "route" : route_chosen
        }), 200
    # Error for Google API
    except Exception as err:
        return jsonify({'error': 'Internal Error', 'details': str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

"""
    The driver presses end route when he's at the last stop
    -------------------------------------------------------
    Update the rides to complete in the DB

    Parameters:
        ride_id: the route that the driver is taking
    Returns:
    - 200 OK: route ended
    - 401 Unauthorized: not logged in
    - 500 Internal Server Error: Database error
"""
@route_op_bp.route('/route/end', methods=['POST'])
@driver_only()
def endRoute():
    data = request.get_json()
    rideId = data.get('ride_id')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE Rides SET ride_status=%s WHERE ride_id=%s",
            ('C', rideId)
        )
        conn.commit()
        return jsonify(), 200

    except Exception as err:
        return jsonify({'error': 'Internal Error', 'details': str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

"""
    Calls the Amazon SNS API to send SMS to phone number about the bookings

    Parameters:
        userIds [list]: list of users
        cursor (mysql cursor): cursor to DB
        start_location (float): starting location of the ride
        end_location (float): end location of the ride
        tripDuration (float): how long the trip will take
        vehDuration (float): how long it takes for the driver to get to the starting location
    Returns:
        Nothing
"""
def sendSMSToUsers(userIds, cursor, start_location, end_location, tripDuration, vehDuration):
    session = boto3.session.Session(aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'))
    client = session.client("sns", region_name="ap-southeast-2")

    for userId in userIds:
        cursor.execute("SELECT phone_number FROM Users WHERE user_id=" + str(userId[0]))
        phoneNumber = cursor.fetchall()[0][0]
        try:
            if phoneNumber == None:
                pass
            else:
                response = client.publish(
                    PhoneNumber=str(phoneNumber),
                    Message=f"""Your booking from {start_location} to {end_location} is starting! Expect a bus to arrive within {int(vehDuration)} minutes. The trip will take {int(tripDuration)} minutes."""
                )
        except Exception as err:
            return jsonify({'error': 'Internal Error', 'details': 'Amazon ' + str(err)}), 500
    return