
/**
 * Component for administrators to view all locations in the system.
 * Displays a list of locations with their details and a delete button
 */

import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Platform,
  ActivityIndicator,
  TouchableOpacity,
  Modal,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../App';
import { useAuth } from '../../context/AuthContext';
import Header from '../../components/LogoHeader';
import config from '../../config';
import axios from 'axios';
import MapView, { Marker as NativeMarker } from 'react-native-maps';
import { GoogleMap, Marker as WebMarker, useJsApiLoader } from '@react-google-maps/api';
import { GlobalStyles, COLORS, SPACING } from '../../GlobalStyles';

const GOOGLE_API_KEY = 'redacted';

type ViewLocationsNavigationProp = NativeStackNavigationProp<RootStackParamList, 'AdminViewLocations'>;

interface AdminViewLocationsProps {
  navigation: ViewLocationsNavigationProp;
}

interface Location {
  location_id: number;
  location_name: string;
  x_coordinate: number;
  y_coordinate: number;
}

const AdminViewLocations: React.FC<AdminViewLocationsProps> = ({ navigation }) => {
  const { accessToken } = useAuth();
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [focusedLocation, setFocusedLocation] = useState<{ lat: number; lng: number } | null>(null);

  const mapRef = useRef<MapView | null>(null);

  const { isLoaded } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: GOOGLE_API_KEY,
  });

  // Fetch all the locations
  useEffect(() => {
    const fetchLocations = async () => {
      try {
        const res = await axios.get(`${config.apiUrl}/location`, {
          headers: { Authorization: `Bearer ${accessToken}` }
        });
        setLocations(res.data.locations || []);
      } catch (err) {
        console.error('Failed to fetch locations', err);
      } finally {
        setLoading(false);
      }
    };

    fetchLocations();
  }, [accessToken]);

  useEffect(() => {
    if (Platform.OS !== 'web' && focusedLocation && mapRef.current) {
      mapRef.current.animateToRegion({
        latitude: focusedLocation.lat,
        longitude: focusedLocation.lng,
        latitudeDelta: 0.01,
        longitudeDelta: 0.01,
      }, 1000);
    }
  }, [focusedLocation]);

  // Deleting location functionality (after location has been selected)
  const handleDeleteConfirm = async () => {
    if (!selectedLocation) return;
    try {
      setDeleting(selectedLocation.location_id);
      await axios.delete(`${config.apiUrl}/location/${selectedLocation.location_id}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      setLocations((prev) =>
        prev.filter((loc) => loc.location_id !== selectedLocation.location_id)
      );
    } catch (err: any) {
      const msg = err.response?.data?.error || 'Error deleting location';
      alert(msg);
    } finally {
      setDeleting(null);
      setShowConfirmModal(false);
      setSelectedLocation(null);
    }
  };

  const openConfirmModal = (location: Location) => {
    setSelectedLocation(location);
    setShowConfirmModal(true);
  };

  // Renders the map into the screen
  const renderMap = () => {
    const center = locations.length
      ? { lat: locations[0].x_coordinate, lng: locations[0].y_coordinate }
      : { lat: 3.14827, lng: 101.616 };

    if (Platform.OS === 'web') {
      return isLoaded ? (
        <GoogleMap
          mapContainerStyle={{ width: '100%', height: 300 }}
          center={focusedLocation || center}
          zoom={14}
        >
          {locations.map(loc => (
            <WebMarker
              key={loc.location_id}
              position={{ lat: loc.x_coordinate, lng: loc.y_coordinate }}
              title={loc.location_name}
            />
          ))}
        </GoogleMap>
      ) : <Text>Loading Map...</Text>;
    } else {
      return (
        <MapView
          ref={mapRef}
          style={{ height: 300 }}
          initialRegion={{
            latitude: center.lat,
            longitude: center.lng,
            latitudeDelta: 0.05,
            longitudeDelta: 0.05,
          }}
        >
          {locations.map(loc => (
            <NativeMarker
              key={loc.location_id}
              coordinate={{ latitude: loc.x_coordinate, longitude: loc.y_coordinate }}
              title={loc.location_name}
            />
          ))}
        </MapView>
      );
    }
  };
  return (
    <ScrollView style={GlobalStyles.container}>
      <Header onBackPress={() => navigation.goBack()} />
      <View style={GlobalStyles.card}>
        <Text style={GlobalStyles.title}>All Bus Stops</Text>

        {loading ? (
          <ActivityIndicator size="large" color={COLORS.PRIMARY} style={{ marginVertical: SPACING.LARGE }} />
        ) : (
          <>
            {renderMap()}
            <Text style={GlobalStyles.label}>STOPS LIST</Text>
            {locations.map(loc => (
              <View key={loc.location_id} style={styles.item}>
                <TouchableOpacity
                  style={styles.itemTextGroup}
                  onPress={() =>
                    setFocusedLocation({ lat: loc.x_coordinate, lng: loc.y_coordinate })
                  }
                >
                  <Text style={styles.itemTitle}>{loc.location_name}</Text>
                  <Text style={styles.itemSubtitle}>
                    Lat: {loc.x_coordinate.toFixed(4)}, Lng: {loc.y_coordinate.toFixed(4)}
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={GlobalStyles.deleteButton}
                  onPress={() => openConfirmModal(loc)}
                  disabled={deleting === loc.location_id}
                >
                  <Text style={GlobalStyles.deleteButtonText}>
                    {deleting === loc.location_id ? 'Deleting...' : 'Delete'}
                  </Text>
                </TouchableOpacity>
              </View>
            ))}
          </>
        )}
      </View>

      {/* Confirm Delete Modal */}
      <Modal
        visible={showConfirmModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowConfirmModal(false)}
      >
        <View style={GlobalStyles.modalOverlay}>
          <View style={GlobalStyles.modalBox}>
            <Text style={GlobalStyles.modalTitle}>Confirm Deletion</Text>
            <Text style={GlobalStyles.modalText}>
              Are you sure you want to delete{' '}
              <Text style={{ fontWeight: 'bold' }}>{selectedLocation?.location_name}</Text>?
            </Text>
            <View style={GlobalStyles.modalButtonGroup}>
              <TouchableOpacity
                style={[GlobalStyles.modalButton, { backgroundColor: COLORS.DELETE_RED }]}
                onPress={handleDeleteConfirm}
              >
                <Text style={GlobalStyles.modalButtonText}>Yes, Delete</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[GlobalStyles.modalButton, { backgroundColor: COLORS.BUTTON_DISABLED }]}
                onPress={() => setShowConfirmModal(false)}
              >
                <Text style={[GlobalStyles.modalButtonText, { color: COLORS.TEXT_DARK }]}>Cancel</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  item: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
    paddingVertical: 10,
  },
  itemTextGroup: {
    flex: 1,
  },
  itemTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1A237E',
  },
  itemSubtitle: {
    fontSize: 14,
    color: '#555',
  },
});

export default AdminViewLocations;
