import heapq
import requests

locations = {
    23: {"location_name": "1 Utama Shopping Centre", "lat": 3.148303575002, "lng": 101.616398780107},
    24: {"location_name": "KL Sentral Bus Station Terminal", "lat": 3.134200206107, "lng": 101.687011739631},
    25: {"location_name": "KLIA1 Bus Terminal", "lat": 2.756717009217, "lng": 101.704872595449},
    26: {"location_name": "KLIA2 Bus Terminal", "lat": 2.745514903079, "lng": 101.684920451533},
    27: {"location_name": "Petronas Twin Towers", "lat": 3.157874187093, "lng": 101.711577674417},
    28: {"location_name": "Batu Caves", "lat": 3.239082421058, "lng": 101.684094793927},
    29: {"location_name": "Merdeka Square", "lat": 3.149360450571, "lng": 101.693702110795},
    30: {"location_name": "KL Tower", "lat": 3.153154862070, "lng": 101.703839804975},
    31: {"location_name": "Mid Valley Megamall", "lat": 3.117766343034, "lng": 101.677450210795},
    32: {"location_name": "Pasar Malam Connaught", "lat": 3.081662876663, "lng": 101.737587095450},
    33: {"location_name": "SS15 Courtyard", "lat": 3.078143150692, "lng": 101.586478781958},
    34: {"location_name": "Publika Shopping Gallery", "lat": 3.171681294478, "lng": 101.664200095451},
    35: {"location_name": "IOI Mall Puchong", "lat": 3.046550584078, "lng": 101.618401410794},
    36: {"location_name": "Pasar Malam Connaught", "lat": 3.081641450020, "lng": 101.737587095450},
    37: {"location_name": "ÆON Mall Wangsa Maju", "lat": 3.202366174696, "lng": 101.735060688839},
    38: {"location_name": "Melawati Mall", "lat": 3.210784132645, "lng": 101.748655254975}
}

GOOGLE_MAPS_API_KEY = "redacted"

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
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{origin['lat']},{origin['lng']}",
        "destination": f"{destination['lat']},{destination['lng']}",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        if data["status"] == "OK" and data["routes"]:
            # Use the first route and its first leg
            leg = data["routes"][0]["legs"][0]
            duration_sec = leg["duration"]["value"]  # duration in seconds
            duration_min = duration_sec / 60.0       # convert to minutes
            return duration_min
        else:
            print("Error retrieving directions from Google Maps API. Response status:", data.get("status"))
            return None
    except Exception as e:
        print("Exception during API call:", e)
        return None

def main():
    print("Welcome to the bus route optimisation algorithm.")
    print("This algorithm uses current database locations and Google Maps API to calculate travel times.")
    print("Profit is fixed at 1 per passenger and the minibus travel time to the start location is fixed at 5 minutes.")
    print("Routes will be ranked from most efficient to least efficient based on:")
    print("  route_profit = total_travel_time * (profit * num_pass - cost)")
    print("Assume sensible inputs from the user...\n")
    
    num_routes = int(input("Enter the number of routes a bus needs to consider: "))
    if num_routes == 0:
        print("There are no routes... exiting...")
        exit(0)
    
    cost = float(input("Enter the cost associated per minute of travel (AUD): "))
    
    # List to store all route details
    routes_info = []
    
    for i in range(num_routes):
        print(f"\nRoute {i+1}:")
        start_id = int(input("Enter the primary key ID for the start location: "))
        end_id = int(input("Enter the primary key ID for the destination location: "))
        num_pass = int(input("Enter the number of passengers waiting at the start location: "))
        
        # Retrieve location details from our simulated database
        if start_id not in locations:
            continue
        if end_id not in locations:
            print(f"Destination location with ID {end_id} not found in database. Skipping this route.")
            continue
        
        start_location = locations[start_id]
        end_location = locations[end_id]
        
        # Fixed values
        profit = 1         # fixed profit per passenger
        time_start = 5     # fixed travel time (minutes) for minibus to reach the start location
        
        # Get travel time from Google Maps API (in minutes)
        time_route = get_travel_time(start_location, end_location)
        if time_route is None:
            print("Could not retrieve travel time for this route. Skipping.")
            continue
        
        total_travel_time = time_start + time_route
        
        # Calculate route_profit using `route_profit = total_travel_time * (profit * num_pass - cost)`
        route_profit = total_travel_time * (profit * num_pass - cost)
        
        # Store the route details in a dictionary
        route_detail = {
            "description": f"Route from {start_location['location_name']} to {end_location['location_name']}",
            "travel_time": total_travel_time,
            "num_pass": num_pass,
            "route_profit": route_profit
        }
        routes_info.append(route_detail)
    
    if not routes_info:
        print("No valid routes were provided.")
        exit(0)
    
    # Rank routes from most efficient (highest route_profit) to least efficient.
    # If route_profit values are negative, the one with the highest (least negative) is still the best.
    ranked_routes = sorted(routes_info, key=lambda x: x["route_profit"], reverse=True)
    
    print("\nRoutes ranked from most efficient to least efficient:")
    for rank, route in enumerate(ranked_routes, start=1):
        print(f"Rank {rank}: {route['description']}")
        print(f"  - Total travel time: {route['travel_time']:.2f} minutes")
        print(f"  - Number of passengers: {route['num_pass']}")
        print(f"  - Efficiency (route_profit): {route['route_profit']:.2f}\n")

if __name__ == "__main__":
    main()
