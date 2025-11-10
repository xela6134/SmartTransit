/**
 * Main driver page providing access to start and end route for drivers
 */

import type React from "react"
import { useState, useEffect } from "react"
import { View, Text, StyleSheet, TextInput, TouchableOpacity, ScrollView, ActivityIndicator, Alert } from "react-native"
import type { NativeStackNavigationProp } from "@react-navigation/native-stack"
import type { RootStackParamList } from "../../App"
import Header from "../../components/LogoHeader"
import axios from "axios"
import config from "../../config"
import { useAuth } from "../../context/AuthContext"
import * as Location from "expo-location"
import { io } from "socket.io-client";


type DriverDashboardScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, "DriverDashboard">

interface DriverDashboardProps {
  navigation: DriverDashboardScreenNavigationProp
}

interface RouteDetails {
  ride_id: number
  num_passengers: number
  start_name: string
  end_name: string
  time_start_end: number
  time_veh_arrive: number
}

const DriverDashboard: React.FC<DriverDashboardProps> = ({ navigation }) => {
  const { accessToken, setAccessToken } = useAuth();
  const [vehicleId, setVehicleId] = useState<string>("");
  const [assignedVehicle, setAssignedVehicle] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [currentRoute, setCurrentRoute] = useState<RouteDetails | null>(null);
  const [socket, setSocket] = useState<any>(null);;
  const [location, setLocation] = useState<{ latitude: number; longitude: number }>(
    { latitude: 0, longitude: 0 }
  );

  const handleLogout = () => {
    setAccessToken(null);  // Clear the access token
    navigation.navigate("DriverLogin");  // Navigate to login screen
  };

  useEffect(() => {
    setupLocationTracking();

    // Initialize socket connection
    const socketInstance = io(config.socketUrl);
    setSocket(socketInstance);

    return () => {
      if (socketInstance) socketInstance.disconnect();
    };
  }, []);

  useEffect(() => {
    // Broadcast location when we have an active trip and location changes
    if (currentRoute && location && socket) {
      socket.emit("driver_location_update", {
        trip_id: currentRoute.ride_id,
        location: location,
      });
    }
  }, [location, currentRoute]);

  const setupLocationTracking = async () => {
    let { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== "granted") {
      setError("Permission to access location was denied");
      return;
    }

    // Get current location immediately
    try {
      let initialLocation = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Highest });
      setLocation({
        latitude: initialLocation.coords.latitude,
        longitude: initialLocation.coords.longitude,
      });
    } catch (error) {
      console.error("Error getting initial location:", error);
    }

    // Setup location tracking
    Location.watchPositionAsync(
      {
        accuracy: Location.Accuracy.High,
        timeInterval: 5000,
        distanceInterval: 10,
      },
      (newLocation) => {
        setLocation({
          latitude: newLocation.coords.latitude,
          longitude: newLocation.coords.longitude,
        });
      }
    );
  };

  // Assign the vehicle with the given vehicleId
  const assignVehicle = async () => {
    if (!vehicleId.trim()) {
      setError("Please enter a vehicle ID");
      return
    }

    try {
      setLoading(true);
      setError(null);

      const response = await axios.post(
        `${config.apiUrl}/driver/assign_vehicle`,
        { licence_number: vehicleId },
        {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
        },
      );

      if (response.status === 200) {
        setAssignedVehicle(vehicleId)
        setVehicleId("")
        setError(null);
        Alert.alert("Success", "Vehicle assigned successfully")
      }
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to assign vehicle")
    } finally {
      setLoading(false)
    }
  }

  // Function to unassign the vehicle
  const unassignVehicle = async () => {
    if (!assignedVehicle) {
      setError("No vehicle assigned");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${config.apiUrl}/driver/unassign_vehicle`,
        { licence_number: assignedVehicle },
        {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );

      if (response.status === 200) {
        setAssignedVehicle(null); // Clear assigned vehicle
        setError(null);
        Alert.alert("Success", "Vehicle unassigned successfully");
      }
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to unassign vehicle");
    } finally {
      setLoading(false);
    }
  };

  const startRoute = async () => {
    if (!assignedVehicle) {
      setError("You must assign a vehicle first")
      return
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${config.apiUrl}/route/start`,
        {
          lat: location.latitude,
          lng: location.longitude,
        },
        {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );

      // Start the route after 200 response is returned
      if (response.status === 200 && response.data.route) {
        setError(null);
        const routeData = response.data.route[1];
        setCurrentRoute(routeData);
        if (socket) {
          socket.emit("driver_start_trip", {
            trip_id: routeData.ride_id,
            start_location: routeData.start_name,
            end_location: routeData.end_name,
            passengers: routeData.passengers,
          });
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to start route");
    } finally {
      setLoading(false);
    }
  };

  const endRoute = async () => {
    if (!currentRoute) {
      setError("No active route to end");
      return
    }
    setLoading(true);
    try {
      const response = await axios.post(
        `${config.apiUrl}/route/end`,
        { ride_id: currentRoute.ride_id },
        {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
        },
      )

      if (response.status === 200) {
        if (socket) {
          socket.emit("driver_end_trip", { trip_id: currentRoute.ride_id });
        }
        setCurrentRoute(null);
        setError(null);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to end route");
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.container}>
      <Header />
      <ScrollView>
        <View style={styles.card}>
          <Text style={styles.title}>Driver Dashboard</Text>

          {error && <Text style={styles.errorText}>{error}</Text>}

          {!assignedVehicle ? (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Assign Vehicle</Text>
              <Text style={styles.label}>VEHICLE ID</Text>
              <TextInput
                style={styles.input}
                value={vehicleId}
                onChangeText={setVehicleId}
                placeholder="Enter vehicle ID"
                editable={!loading}
              />
              <TouchableOpacity style={styles.button} onPress={assignVehicle} disabled={loading}>
                {loading ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text style={styles.buttonText}>ASSIGN VEHICLE</Text>
                )}
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.section}>
              <View style={styles.vehicleInfoContainer}>
                <Text style={styles.sectionTitle}>Vehicle Information</Text>
                <View style={styles.vehicleInfo}>
                  <Text style={styles.label}>ASSIGNED VEHICLE ID:</Text>
                  <Text style={styles.value}>{assignedVehicle}</Text>
                </View>
                {!currentRoute && (
                  <TouchableOpacity
                    style={[styles.button, styles.endRouteButton]}
                    onPress={unassignVehicle}
                    disabled={loading}
                  >
                    {loading ? (
                      <ActivityIndicator color="#fff" size="small" />
                    ) : (
                      <Text style={styles.buttonText}>UNASSIGN VEHICLE</Text>
                    )}
                  </TouchableOpacity>
                )}
              </View>

              {!currentRoute ? (
                <TouchableOpacity style={styles.button} onPress={startRoute} disabled={loading}>
                  {loading ? (
                    <ActivityIndicator color="#fff" size="small" />
                  ) : (
                    <Text style={styles.buttonText}>START ROUTE</Text>
                  )}
                </TouchableOpacity>
              ) : (
                <View style={styles.routeContainer}>
                  <Text style={styles.sectionTitle}>Current Route</Text>

                  <View style={styles.routeDetails}>
                    <View style={styles.detailRow}>
                      <Text style={styles.label}>RIDE ID:</Text>
                      <Text style={styles.value}>{currentRoute.ride_id}</Text>
                    </View>
                    <View style={styles.detailRow}>
                      <Text style={styles.label}>PASSENGERS:</Text>
                      <Text style={styles.value}>{currentRoute.num_passengers}</Text>
                    </View>
                    <View style={styles.detailRow}>
                      <Text style={styles.label}>FROM:</Text>
                      <Text style={styles.value}>{currentRoute.start_name}</Text>
                    </View>
                    <View style={styles.detailRow}>
                      <Text style={styles.label}>TO:</Text>
                      <Text style={styles.value}>{currentRoute.end_name}</Text>
                    </View>
                    <View style={styles.detailRow}>
                      <Text style={styles.label}>ESTIMATED DURATION:</Text>
                      <Text style={styles.value}>{Math.round(currentRoute.time_start_end)} min</Text>
                    </View>
                    <View style={styles.detailRow}>
                      <Text style={styles.label}>ARRIVAL TIME:</Text>
                      <Text style={styles.value}>{Math.round(currentRoute.time_veh_arrive)} min</Text>
                    </View>
                  </View>

                  <TouchableOpacity
                    style={[styles.button, styles.endRouteButton]}
                    onPress={endRoute}
                    disabled={loading}
                  >
                    {loading ? (
                      <ActivityIndicator color="#fff" size="small" />
                    ) : (
                      <Text style={styles.buttonText}>END ROUTE</Text>
                    )}
                  </TouchableOpacity>
                </View>
              )}
            </View>
          )}
          {!currentRoute && (
            <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
              <Text style={styles.buttonText}>LOGOUT</Text>
            </TouchableOpacity>
          )}
        </View>
      </ScrollView>
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f9f9f9",
    padding: 20,
  },
  card: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 30,
    marginTop: 20,
    marginBottom: 20,
    elevation: 4,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  title: {
    fontSize: 26,
    fontWeight: "700",
    color: "#333",
    textAlign: "center",
    marginBottom: 20,
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#333",
    marginBottom: 15,
  },
  label: {
    fontSize: 14,
    fontWeight: "600",
    color: "#333",
    marginBottom: 8,
  },
  value: {
    fontSize: 16,
    color: "#333",
  },
  input: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    fontSize: 16,
    color: "#333",
  },
  button: {
    backgroundColor: "#1A237E",
    borderRadius: 12,
    paddingVertical: 15,
    alignItems: "center",
    marginTop: 10,
  },
  buttonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  errorText: {
    color: "#D32F2F",
    fontSize: 16,
    textAlign: "center",
    marginBottom: 15,
  },
  vehicleInfoContainer: {
    marginBottom: 20,
  },
  vehicleInfo: {
    backgroundColor: "#f5f5f5",
    borderRadius: 8,
    padding: 15,
  },
  routeContainer: {
    marginTop: 20,
  },
  routeDetails: {
    backgroundColor: "#f5f5f5",
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
  },
  detailRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 10,
  },
  endRouteButton: {
    backgroundColor: "#D32F2F",
  },
  logoutButton: {
    backgroundColor: "#D32F2F",
    borderRadius: 12,
    paddingVertical: 15,
    alignItems: "center",
    marginTop: 20,
  },
})

export default DriverDashboard
