import React, { useEffect, useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  ActivityIndicator,
  Alert,
} from 'react-native';
import MapView, { Marker } from 'react-native-maps';
import * as ExpoLocation from 'expo-location';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../App';
import Header from '../components/LogoHeader';
import Footer from '../components/Footer';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import config from '../config';

export type HomeScreenNavigationProp = NativeStackNavigationProp<
  RootStackParamList,
  'Home'
>;

interface HomeProps {
  navigation: HomeScreenNavigationProp;
}

interface SLocation {
  location_id: number;
  location_name: string;
  x_coordinate: number;
  y_coordinate: number;
}

interface Coordinate {
  lat: number;
  lng: number;
}

/* Color palette */
const DARK = '#1A237E';
const LIGHT_BG = '#FFFFFF';
const MUTED_TEXT = '#555';
const CARD_BG = '#F5F7FF';

function Homepage({ navigation }: HomeProps) {
  const [username, setUsername] = useState<string | null>(null);
  const [loadingUser, setLoadingUser] = useState(false);
  const [locations, setLocations] = useState<SLocation[]>([]);
  const [loadingLocs, setLoadingLocs] = useState(false);
  const [userCoord, setUserCoord] = useState<Coordinate>({ lat: 3.14827, lng: 101.616 });
  const [zoomLevel, setZoomLevel] = useState<number>(14);
  const mapRef = useRef<MapView | null>(null);
  const insets = useSafeAreaInsets();

  const { isAuthenticated, logout, accessToken } = useAuth();

  // Fetching user data
  useEffect(() => {
    const fetchUser = async () => {
      try {
        setLoadingUser(true);
        const res = await axios.get(`${config.apiUrl}/auth/status`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        });
        setUsername(res.data.name);

        if (res.data.user_id === 1) {
          navigation.navigate('Admin');
        }
      } catch {
        setUsername(null);
      } finally {
        setLoadingUser(false);
      }
    };
    if (isAuthenticated) fetchUser();
  }, [isAuthenticated, accessToken]);

  // Fetch location data
  useEffect(() => {
    if (isAuthenticated) {
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
          setLoadingLocs(false);
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
      })();
    }
  }, [isAuthenticated]);

  // Helper function for zooming in
  const animateZoom = (delta: number) => {
    if (!mapRef.current) return;
    const newZoom = zoomLevel + delta;
    if (newZoom < 5 || newZoom > 20) return;
    mapRef.current.animateCamera({ zoom: newZoom }, { duration: 160 });
    setZoomLevel(newZoom);
  };

  const Option = ({ label, icon, onPress }: { label: string; icon: React.ComponentProps<typeof Ionicons>['name']; onPress: () => void }) => (
    <Pressable style={styles.option} android_ripple={{ color: '#e1e1e1' }} onPress={onPress}>
      <Ionicons name={icon} size={22} color={LIGHT_BG} style={{ marginBottom: 4 }} />
      <Text style={styles.optionText}>{label}</Text>
    </Pressable>
  );

  const optionData = [
    { label: 'Book Ride', icon: 'car', route: () => navigation.navigate('Booking') },
    { label: 'Current', icon: 'time', route: () => navigation.navigate('CurrentBookings') },
    { label: 'Past Trips', icon: 'albums', route: () => navigation.navigate('PastBookings') },
    { label: 'Profile', icon: 'person', route: () => navigation.navigate('Profile') },
    { label: 'Logout', icon: 'log-out', route: logout },
  ];

  if (loadingUser || loadingLocs) {
    return (
      <View style={[styles.centered, { flex: 1, backgroundColor: LIGHT_BG }]}>
        <ActivityIndicator size="large" color={DARK} />
      </View>
    );
  }

  // Guest View
  if (!isAuthenticated) {
    return (
      <View style={[styles.container, { paddingBottom: insets.bottom }]}>
        <Header />
        <View style={styles.heroCard}>
          <Text style={styles.heroTitle}>SmartTransit</Text>
          <Text style={styles.heroSub}>Your intelligent ride companion!</Text>

          <Pressable style={styles.primaryBtn} android_ripple={{ color: '#e5e5ff' }} onPress={() => navigation.navigate('SignIn')}>
            <Text style={styles.primaryText}>SIGN IN</Text>
          </Pressable>
          <Pressable style={styles.outlinedBtn} android_ripple={{ color: '#d1d1d1' }} onPress={() => navigation.navigate('Register')}>
            <Text style={styles.outlinedText}>CREATE ACCOUNT</Text>
          </Pressable>
          <Pressable style={styles.driverBtn} android_ripple={{ color: '#d1d1d1' }} onPress={() => navigation.navigate('DriverLogin')}>
            <Text style={styles.driverText}>LOGIN FOR DRIVERS</Text>
          </Pressable>
        </View>
      </View>
    );
  }

  // Authorised User View
  return (
    <View style={[styles.container, { paddingBottom: insets.bottom }]}>
      <ScrollView contentContainerStyle={{ paddingBottom: 100 }} showsVerticalScrollIndicator={false}>
        <Header />

        <View style={styles.greetWrap}>
          <Text style={styles.greetHi}>Hey,</Text>
          <Text style={styles.greetName}>{username || 'Rider'}</Text>
        </View>

        <Text style={{ marginLeft: 24, marginTop: 16, fontWeight: '600', fontSize: 16, color: '#333' }}>
          Current locations:
        </Text>
        <View style={styles.mapWrap}>
          <MapView
            style={StyleSheet.absoluteFill}
            initialRegion={{
              latitude: userCoord.lat,
              longitude: userCoord.lng,
              latitudeDelta: 0.0922,
              longitudeDelta: 0.0421,
            }}
            region={{
              latitude: userCoord.lat,
              longitude: userCoord.lng,
              latitudeDelta: 0.0922,
              longitudeDelta: 0.0421,
            }}
            ref={mapRef}
          >
            {locations.map((l) => (
              <Marker key={l.location_id} coordinate={{ latitude: l.x_coordinate, longitude: l.y_coordinate }} title={l.location_name} pinColor="#1A237E" />
            ))}
            {userCoord && (
              <Marker coordinate={{ latitude: userCoord.lat, longitude: userCoord.lng }} title="Your Location" pinColor="#D22B2B" />
            )}
          </MapView>

          <View style={styles.zoomControls} pointerEvents="box-none">
            <Pressable style={styles.zoomBtn} android_ripple={{ color: '#ccd' }} onPress={() => animateZoom(1)}>
              <Ionicons name="add" size={20} color={DARK} />
            </Pressable>
            <Pressable style={styles.zoomBtn} android_ripple={{ color: '#ccd' }} onPress={() => animateZoom(-1)}>
              <Ionicons name="remove" size={20} color={DARK} />
            </Pressable>
          </View>
        </View>

        <Text style={{ marginLeft: 24, marginTop: 20, fontWeight: '600', fontSize: 16, color: '#333' }}>
          List of Options:
        </Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.optionBar}>
          {optionData.map((o) => (
            <Option key={o.label} label={o.label} icon={o.icon as any} onPress={o.route} />
          ))}
        </ScrollView>
      </ScrollView>

      <Footer />
    </View>
  );
}

const CARD_SIZE = 80;
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: LIGHT_BG },
  centered: { justifyContent: 'center', alignItems: 'center' },
  heroCard: {
    backgroundColor: LIGHT_BG,
    marginTop: 20,
    marginHorizontal: 20,
    padding: 28,
    borderRadius: 16,
    elevation: 3,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowOffset: { width: 0, height: 2 },
    alignItems: 'center',
  },
  heroTitle: { fontSize: 32, fontWeight: '700', color: DARK, marginBottom: 6 },
  heroSub: { fontSize: 16, color: MUTED_TEXT, marginBottom: 24, textAlign: 'center' },
  primaryBtn: {
    backgroundColor: DARK,
    borderRadius: 10,
    paddingVertical: 14,
    paddingHorizontal: 32,
    marginBottom: 12,
    width: '100%',
    alignItems: 'center',
  },
  primaryText: { color: LIGHT_BG, fontWeight: '600', fontSize: 16 },
  outlinedBtn: {
    borderColor: DARK,
    borderWidth: 2,
    borderRadius: 10,
    paddingVertical: 14,
    paddingHorizontal: 32,
    marginBottom: 12,
    width: '100%',
    alignItems: 'center',
  },
  outlinedText: { color: DARK, fontWeight: '600', fontSize: 16 },
  driverBtn: {
    backgroundColor: CARD_BG,
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 32,
    marginTop: 4,
    width: '100%',
    alignItems: 'center',
  },
  driverText: { color: MUTED_TEXT, fontWeight: '500' },
  mapWrap: {
    height: 260,
    borderRadius: 20,
    overflow: 'hidden',
    marginHorizontal: 20,
    marginTop: 16,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  zoomControls: {
    position: 'absolute',
    right: 10,
    top: 10,
    rowGap: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  zoomBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: LIGHT_BG,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 2,
  },
  greetWrap: { marginLeft: 24, marginTop: 12 },
  greetHi: { color: MUTED_TEXT, fontSize: 18 },
  greetName: { color: DARK, fontSize: 28, fontWeight: '700' },
  optionBar: {
    paddingVertical: 20,
    paddingHorizontal: 20,
    columnGap: 12,
  },
  option: {
    width: CARD_SIZE,
    height: CARD_SIZE,
    backgroundColor: DARK,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  optionText: { color: LIGHT_BG, fontSize: 12, fontWeight: '600' },
});

export default Homepage;
