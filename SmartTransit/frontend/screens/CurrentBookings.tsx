import React, { useState, useEffect } from "react";
import { View, Text, StyleSheet, FlatList, ActivityIndicator, TouchableOpacity } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../App';
import Header from "../components/LogoHeader";
import axios from "axios";
import config from "../config";
import { useAuth } from "../context/AuthContext";
import { io } from "socket.io-client";
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';

type CurrentBookingsNavigationProp = NativeStackNavigationProp<RootStackParamList, 'CurrentBookings'>;

interface CurrentBookingsProps {
  navigation: CurrentBookingsNavigationProp;
}

interface Booking {
  ride_id: number;
  start_location: string;
  end_location: string;
  ride_duration: number;
  ride_status: string;
}

interface DriverLocation {
  trip_id: number;
  location: {
    latitude: number;
    longitude: number;
  };
}

const CurrentBookings: React.FC<CurrentBookingsProps> = ({ navigation }) => {
  const { accessToken } = useAuth();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [driverLocations, setDriverLocations] = useState<Record<number, DriverLocation>>({});
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);
  const [socket, setSocket] = useState<any>(null);

  useEffect(() => {
    // Initialize socket connection
    const socketInstance = io(config.socketUrl);
    setSocket(socketInstance);

    // Listen for driver location updates
    socketInstance.on("driver_location_update", (data: DriverLocation) => {
      setDriverLocations(prev => ({
        ...prev,
        [data.trip_id]: data
      }));
    });

    // Fetch bookings
    fetchBookings();

    return () => {
      if (socketInstance) socketInstance.disconnect();
    };
  }, [accessToken]);

  // Fetch all the current fetched bookings
  const fetchBookings = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${config.apiUrl}/booking/view`, {
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      });

      if (response.data.bookings) {
        setBookings(response.data.bookings);
      }
    } catch (err: any) {
      console.error("Error fetching bookings:", err);
      setError(err.response?.data?.error || "Failed to fetch bookings");
    } finally {
      setLoading(false);
    }
  };

  const renderBookingItem = ({ item }: { item: Booking }) => {
    const isActive = item.ride_status === 'A';
    const hasDriverLocation = isActive && driverLocations[item.ride_id];

    return (
      <TouchableOpacity
        style={[styles.bookingItem, isActive ? styles.activeBooking : {}]}
        onPress={() => setSelectedBooking(item)}
      >
        <Text style={styles.bookingTitle}>Ride #{item.ride_id}</Text>
        <Text style={styles.bookingDetail}>From: {item.start_location}</Text>
        <Text style={styles.bookingDetail}>To: {item.end_location}</Text>
        <Text style={styles.bookingDetail}>Duration: {item.ride_duration} min</Text>
        <Text style={styles.bookingStatus}>
          Status: {
            item.ride_status === 'I' ? 'Initiated' :
              item.ride_status === 'A' ? 'Active' :
                item.ride_status === 'C' ? 'Completed' : 'Unknown'
          }
        </Text>
        {hasDriverLocation && (
          <Text style={styles.driverInfo}>
            Driver is on the way! Track on map.
          </Text>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <Header onBackPress={() => navigation.goBack()} />
      <Text style={styles.title}>Current Bookings</Text>

      {loading ? (
        <ActivityIndicator size="large" color="#1A237E" style={styles.loader} />
      ) : error ? (
        <Text style={styles.errorText}>{error}</Text>
      ) : bookings.length === 0 ? (
        <Text style={styles.noBookingsText}>You have no current bookings</Text>
      ) : (
        <>
          <FlatList
            data={bookings}
            renderItem={renderBookingItem}
            keyExtractor={(item) => item.ride_id.toString()}
            contentContainerStyle={styles.bookingsList}
          />

          {selectedBooking && driverLocations[selectedBooking.ride_id] && (
            <View style={styles.mapContainer}>
              <Text style={styles.mapTitle}>Driver Location for Ride #{selectedBooking.ride_id}</Text>
              <MapView
                provider={PROVIDER_GOOGLE}
                style={styles.map}
                region={{
                  latitude: driverLocations[selectedBooking.ride_id].location.latitude,
                  longitude: driverLocations[selectedBooking.ride_id].location.longitude,
                  latitudeDelta: 0.01,
                  longitudeDelta: 0.01,
                }}
              >
                <Marker
                  coordinate={{
                    latitude: driverLocations[selectedBooking.ride_id].location.latitude,
                    longitude: driverLocations[selectedBooking.ride_id].location.longitude,
                  }}
                  title="Driver Location"
                />
              </MapView>
              <TouchableOpacity
                style={styles.closeMapButton}
                onPress={() => setSelectedBooking(null)}
              >
                <Text style={styles.closeMapButtonText}>Close Map</Text>
              </TouchableOpacity>
            </View>
          )}
        </>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9f9f9',
    padding: 20,
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: '#333',
    textAlign: 'center',
    marginVertical: 20,
  },
  loader: {
    flex: 1,
    justifyContent: 'center',
  },
  errorText: {
    color: 'red',
    textAlign: 'center',
    marginTop: 20,
  },
  noBookingsText: {
    textAlign: 'center',
    fontSize: 16,
    color: '#666',
    marginTop: 40,
  },
  bookingsList: {
    paddingBottom: 20,
  },
  bookingItem: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 15,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  activeBooking: {
    borderLeftWidth: 5,
    borderLeftColor: '#4CAF50',
  },
  bookingTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  bookingDetail: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  bookingStatus: {
    fontSize: 14,
    fontWeight: 'bold',
    marginTop: 5,
    color: '#1A237E',
  },
  driverInfo: {
    fontSize: 14,
    fontWeight: 'bold',
    marginTop: 10,
    color: '#4CAF50',
  },
  mapContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: '50%',
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.1,
    shadowRadius: 5,
    elevation: 5,
  },
  mapTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  map: {
    flex: 1,
    borderRadius: 10,
    overflow: 'hidden',
  },
  closeMapButton: {
    backgroundColor: '#1A237E',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 10,
  },
  closeMapButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
});

export default CurrentBookings;
