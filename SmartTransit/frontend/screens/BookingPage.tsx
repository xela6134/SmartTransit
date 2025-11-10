import React, { useEffect, useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  Button,
  Alert,
  Platform
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../App';
import Header from '../components/LogoHeader';
import axios from 'axios';
import config from '../config';
import * as ExpoLocation from 'expo-location';
import { useAuth } from '../context/AuthContext';
import polyline from '@mapbox/polyline';
import MapView, { Marker, Polyline as NativePolyline } from 'react-native-maps';
import RNPickerSelect from 'react-native-picker-select';

export interface Location {
  location_id: number;
  location_name: string;
  x_coordinate: number;
  y_coordinate: number;
}

interface Coordinate {
  lat: number;
  lng: number;
}

interface BookingDetails {
  ride_id: number;
  estimated_duration: number;
  estimated_price_cents: number;
  start_location: number;
  end_location: number;
}

const GOOGLE_API_KEY = 'redacted';

const containerStyle = {
  width: '100%',
  height: '100%',
};

const BookingPage: React.FC<{ navigation: NativeStackNavigationProp<RootStackParamList, 'Booking'> }> = ({ navigation }) => {
  const { accessToken } = useAuth();
  const [startLocation, setStartLocation] = useState('');
  const [endLocation, setEndLocation] = useState('');
  const [routeCoords, setRouteCoords] = useState<Coordinate[]>([]);
  const [bookingDetails, setBookingDetails] = useState<BookingDetails | null>(null);
  const [mapCenter, setMapCenter] = useState<Coordinate>({ lat: 3.15517, lng: 101.70254 });
  const [locations, setLocations] = useState<Location[]>([]);
  const [userCoord, setUserCoord] = useState<Coordinate>();
  const [fetchingLocations, setFetchingLocations] = useState(true);
  const [isRouteFound, setIsRouteFound] = useState(false);
  const [zoomLevel, setZoomLevel] = useState<number>(14);
  const mapRef = useRef<any>(null);

  useEffect(() => {
    const fetchLocations = async () => {
      try {
        const response = await axios.get(`${config.apiUrl}/location`, {
          headers: { 'Authorization': `Bearer ${accessToken}` },
        });
        const locs = response.data.locations;
        setLocations(locs);
      } catch (error) {
        console.error('Error fetching locations:', error);
      } finally {
        setFetchingLocations(false);
      }
    };
    fetchLocations();

    (async () => {
      // Ask for location permissions
      const { status } = await ExpoLocation.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'Permission to access location was denied.');
        return;
      }
      
      // Get the current position
      const currentLocation = await ExpoLocation.getCurrentPositionAsync({});
      const { latitude, longitude } = currentLocation.coords;
      
      // Update the map center state
      setUserCoord({ lat: latitude, lng: longitude });
      setMapCenter({ lat: latitude, lng: longitude });
    })();
  }, [accessToken]);

  const handleFunctions = async () => {
    handleFindRoute();
    handleInitiateBooking();
  };

  // Find route by calling /directions route, then decode the polyline
  const handleFindRoute = async () => {
    const startLoc = locations.find((loc) => loc.location_id === Number(startLocation));
    const endLoc = locations.find((loc) => loc.location_id === Number(endLocation));

    if (!startLoc || !endLoc) {
      Alert.alert('Please select both start and end locations.');
      return;
    }
    if (startLoc.location_id === endLoc.location_id) {
      Alert.alert('Start and End locations must be different.');
      return;
    }

    const origin = `${startLoc.x_coordinate},${startLoc.y_coordinate}`;
    const destination = `${endLoc.x_coordinate},${endLoc.y_coordinate}`;


    try {
      const response = await axios.get(
        `${config.apiUrl}/directions?origin=${origin}&destination=${destination}&t=${Date.now()}`,
        {
          timeout: 10000,
          maxContentLength: Infinity,
          maxBodyLength: Infinity,
          withCredentials: true,
        }
      );

      if (response.data.routes && response.data.routes.length > 0) {
        const points = polyline.decode(response.data.routes[0].overview_polyline.points);
        const coords = points.map((point: [number, number]) => ({
          lat: point[0],
          lng: point[1],
        }));
        setRouteCoords(coords);
        
        if (mapRef.current) {
          mapRef.current.fitToCoordinates(
            coords.map(c => ({ latitude: c.lat, longitude: c.lng })),
            {
              edgePadding: { top: 80, right: 80, bottom: 80, left: 80 },
              animated: true,
            },
          );
        }
        setIsRouteFound(true);      
      } else {
        Alert.alert('No route found.');
        setRouteCoords([]);
        setIsRouteFound(false);
      }
    } catch (error: any) {
      console.error('Error fetching route:', error.response?.data?.msg || error);
      Alert.alert('Error fetching route.');
    }
  };

  // Initiate booking by calling existing /booking/initiate route
  const handleInitiateBooking = async () => {
    if (!startLocation || !endLocation) {
      Alert.alert('Please select both start and end locations.');
      return;
    }
    try {
      const response = await axios.post(
        `${config.apiUrl}/booking/initiate`,
        {
          start_location: Number(startLocation),
          end_location: Number(endLocation),
        },
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        }
      );
      if (response.status === 200) {
        setBookingDetails(response.data);
      }
    } catch (err: any) {
      console.error('Error initiating booking:', err.response?.data?.error || err);
      Alert.alert('Error initiating booking.');
    }
  };

  const renderMap = () => {
  
    return (
      <View style={styles.mapContainer}>
        <MapView
          ref={mapRef}
          style={StyleSheet.absoluteFill}
          initialRegion={{
            latitude: mapCenter.lat,
            longitude: mapCenter.lng,
            latitudeDelta: 0.0922,
            longitudeDelta: 0.0421,
          }}
        >
          {locations
            .filter(
              loc =>
                !isRouteFound ||
                loc.location_id === Number(startLocation) ||
                loc.location_id === Number(endLocation)
            )
            .map(loc => (
              <Marker
                key={loc.location_id}
                coordinate={{ latitude: loc.x_coordinate, longitude: loc.y_coordinate }}
                title={loc.location_name}
                pinColor="#1A237E"
              />
            ))}
  
          {userCoord && (
            <Marker
              coordinate={{ latitude: userCoord.lat, longitude: userCoord.lng }}
              title="Your Location"
              pinColor="#D22B2B"
            />
          )}
  
          {routeCoords.length > 0 && (
            <NativePolyline
              coordinates={routeCoords.map(c => ({ latitude: c.lat, longitude: c.lng }))}
              strokeColor="#000"
              strokeWidth={3}
            />
          )}
        </MapView>
      </View>
    );
  };  

  const animateZoom = (delta: number) => {
    if (!mapRef.current) return;
    const newZoom = zoomLevel + delta;
    if (newZoom < 5 || newZoom > 20) return;    // clamp
    mapRef.current.animateCamera({ zoom: newZoom }, { duration: 160 });
    setZoomLevel(newZoom);
  };

  // When the user chooses to proceed to payment, navigate to PaymentScreen
  // passing the ride_id from bookingDetails.
  const handleProceedPayment = async () => {
    if (!bookingDetails) {
      Alert.alert("Booking details are missing. Please find a route first.");
      return;
    }
    navigation.navigate('Payment', { rideId: bookingDetails.ride_id });
  };

  if (fetchingLocations) {
    return (
      <View style={[styles.loadingContainer, styles.container]}>
        <ActivityIndicator size="large" color="#000" />
        <Text style={styles.loadingText}>Loading locations...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Header onBackPress={() => navigation.goBack()} />
      <View style={styles.mapWrapper}>{renderMap()}</View>

      <View style={styles.routeInfoContainer}>
        {bookingDetails ? (
          <>
            <Text style={styles.routeInfoText}>
              Estimated Duration: {bookingDetails.estimated_duration.toFixed(2)} minutes
            </Text>
            <Text style={styles.routeInfoText}>Estimated Price: {bookingDetails.estimated_price_cents} cents</Text>
            <Text style={styles.routeInfoText}>
              Start Location:{" "}
              {locations.find((loc) => loc.location_id === bookingDetails.start_location)?.location_name ||
                bookingDetails.start_location}
            </Text>
            <Text style={styles.routeInfoText}>
              End Location:{" "}
              {locations.find((loc) => loc.location_id === bookingDetails.end_location)?.location_name ||
                bookingDetails.end_location}
            </Text>
          </>
        ) : (
          <Text style={styles.routeInfoText}>
            Select start and end locations, then press "Find a Route" and "Get Booking Info"
          </Text>
        )}
      </View>
      <View style={styles.dropdownContainer}>
        <Text style={styles.dropdownLabel}>Start Location:</Text>
        <RNPickerSelect
          onValueChange={(value) => setStartLocation(value)}
          value={startLocation}
          placeholder={{ label: "Select start location", value: "" }}
          items={locations.map((loc) => ({
            label: loc.location_name,
            value: loc.location_id.toString(),
          }))}
          style={{
            ...pickerSelectStyles,
            iconContainer: {
              top: 10,
              right: 12,
            },
          }}
          useNativeAndroidPickerStyle={false}
          Icon={() => {
            return Platform.OS === "ios" ? <Text style={{ fontSize: 12, color: "gray" }}>▼</Text> : null
          }}
        />

        <Text style={styles.dropdownLabel}>End Location:</Text>
        <RNPickerSelect
          onValueChange={(value) => setEndLocation(value)}
          value={endLocation}
          placeholder={{ label: "Select end location", value: "" }}
          items={locations.map((loc) => ({
            label: loc.location_name,
            value: loc.location_id.toString(),
          }))}
          style={{
            ...pickerSelectStyles,
            iconContainer: {
              top: 10,
              right: 12,
            },
          }}
          useNativeAndroidPickerStyle={false}
          Icon={() => {
            return Platform.OS === "ios" ? <Text style={{ fontSize: 12, color: "gray" }}>▼</Text> : null
          }}
        />
      </View>
      <View style={styles.buttonContainer}>
        <View style={styles.buttonWrapper}>
          <Button title="Find a Route" onPress={handleFunctions} disabled={!startLocation || !endLocation} />
        </View>
        <View style={styles.buttonWrapper}>
          <Button title="Proceed to Payment" onPress={handleProceedPayment} disabled={!isRouteFound} />
        </View>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  mapWrapper: { flex: 1, height: 300 },
  routeInfoContainer: {
    padding: 10,
    backgroundColor: "#fff",
    alignItems: "center",
  },
  routeInfoText: { fontSize: 16, fontWeight: "bold" },
  dropdownContainer: { padding: 10, backgroundColor: "#fff", zIndex: 10 },
  dropdownLabel: { fontWeight: "bold", marginBottom: 5 },
  picker: { height: 50, width: "100%", marginBottom: 10 },
  loadingContainer: { flex: 1, justifyContent: "center", alignItems: "center" },
  loadingText: { marginTop: 10, color: "#000", fontSize: 16 },
  buttonContainer: {
    flexDirection: "row",
    justifyContent: "space-between",
    padding: 10,
    backgroundColor: "#fff",
  },
  buttonWrapper: {
    flex: 1,
    marginHorizontal: 5,
  },
  mapContainer: {
    flex: 1,
    height: 300,
    borderRadius: 8,
    overflow: 'hidden',
  },
  zoomControls: {
    position: 'absolute',
    right: 10,
    top: 10,
    rowGap: 8,
    alignItems: 'center',
  },
  zoomBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 2,
  },
})

const pickerSelectStyles = StyleSheet.create({
  inputIOS: {
    fontSize: 16,
    paddingVertical: 12,
    paddingHorizontal: 10,
    borderWidth: 1,
    borderColor: "gray",
    borderRadius: 4,
    color: "black",
    paddingRight: 30,
    marginBottom: 10,
    backgroundColor: "white",
  },
  inputAndroid: {
    fontSize: 16,
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderWidth: 0.5,
    borderColor: "gray",
    borderRadius: 4,
    color: "black",
    marginBottom: 10,
  },
})

export default BookingPage;
