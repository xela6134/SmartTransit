#!/usr/bin/env python3
# Alperen Onur (z5161138)
import heapq

def main():
    print("Welcome to the bus route optimisation algorithm.")
    print("Given a list of routes and passengers, this algorithm will greedily select the best.")
    print("Algorithm considers AUD as cost and minutes for traveltime.")
    print("Assume sensible inputs from user...")
    num_loc = int(input("Enter the amount of routes a bus needs to consider: "))
    if num_loc == 0:
        print("There are no routes... exiting...")
        exit(0)
    cost = float(input("Enter the cost associated per minute of travel: "))
    
    heap = []
    for i in range(0, num_loc):
        start = str(input(f"Enter name of start location of route {i+1}: "))
        end = str(input(f"Enter name of end location for route {i+1}: "))
        time_start = float(input(f"Enter travel time from minibus to {start}: "))
        num_pass = int(input(f"Enter number of passengers waiting to be transported from {start}: "))
        profit = float(input(f"Enter the proft per passenger for route {i+1}: "))
        time_route = float(input(f"Enter the travel time from {start} to {end}: "))
        forumula = profit*num_pass - cost*(time_start + time_route)
        heapq.heappush(heap, (-1 * forumula, f"Route {start} to {end}"))
        print()

    route_chosen = heapq.heappop(heap)
    print(f"{route_chosen[1]} generating profit ${-1 * route_chosen[0]} will be chosen by the minibus")
    if (route_chosen[0]) >= 0:
        print(f"KK has lost ${-1 * route_chosen[0]} LOL")
    else:
        print(f"KK has made ${-1 * route_chosen[0]}! Big money!")

if __name__ == "__main__":
    main()
