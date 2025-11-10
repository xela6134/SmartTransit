
/**
 * Component for administrators to add new bus stop locations to the system.
 * Provides an interface to select a location on a map and enter stop details.
 */
import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet, TouchableOpacity, Alert, Modal, Platform, ScrollView } from 'react-native';
import MapView, { Marker as NativeMarker } from 'react-native-maps';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../App';
import { useAuth } from '../../context/AuthContext';
import Header from '../../components/LogoHeader';
import config from '../../config';
import axios from 'axios';
import { useJsApiLoader, GoogleMap, Marker as WebMarker } from '@react-google-maps/api';
import GlobalStyles, { SuccessModalStyles } from '../../GlobalStyles';


const GOOGLE_API_KEY = 'redacted';

type AddLocationNavigationProp = NativeStackNavigationProp<RootStackParamList, 'RegisterDriver'>;

interface AddLocationProps {
  navigation: AddLocationNavigationProp;
}

const AddLocation: React.FC<AddLocationProps> = ({ navigation }) => {
  const { accessToken } = useAuth();
  const [stopName, setStopName] = useState('');
  const [markerCoord, setMarkerCoord] = useState<{ lat: number; lng: number } | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);


  const { isLoaded } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: GOOGLE_API_KEY,
  });

  // Saves the coordinate pressed on the map
  const handleMapPress = (e: any) => {
    const coords = Platform.OS === 'web'
      ? { lat: e.latLng.lat(), lng: e.latLng.lng() }
      : { lat: e.nativeEvent.coordinate.latitude, lng: e.nativeEvent.coordinate.longitude };
    setMarkerCoord(coords);
  };

  const handleSubmit = async () => {
    if (!stopName || !markerCoord) {
      setError('Please select a location and enter a stop name.');
      return;
    }

    // Sends the location adding response
    try {
      const response = await axios.post(`${config.apiUrl}/location/create`, {
        location_name: stopName,
        x_coordinate: markerCoord.lat.toString(),
        y_coordinate: markerCoord.lng.toString()
      }, {
        headers: { Authorization: `Bearer ${accessToken}` }
      });

      if (response.status === 200) {
        setShowSuccess(true);
        navigation.navigate('Admin');
      }
    } catch (error: any) {
      if (error.response) {
        setError(error.response.data.error || 'Location adding failed');
      } else {
        setError('Network error. Please try again.');
      }
    }
  };
  const renderMap = () => {
    const center = markerCoord || { lat: 3.14827, lng: 101.616 };

    if (Platform.OS === 'web') {
      return isLoaded ? (
        <GoogleMap
          mapContainerStyle={{ width: '100%', height: 300 }}
          center={center}
          zoom={14}
          onClick={handleMapPress}
        >
          {markerCoord && <WebMarker position={markerCoord} />}
        </GoogleMap>
      ) : <Text>Loading Map...</Text>;
    } else {
      return (
        <MapView
          style={{ height: 300 }}
          initialRegion={{
            latitude: center.lat,
            longitude: center.lng,
            latitudeDelta: 0.01,
            longitudeDelta: 0.01
          }}
          onPress={handleMapPress}
        >
          {markerCoord && (
            <NativeMarker
              coordinate={{ latitude: markerCoord.lat, longitude: markerCoord.lng }}
            />
          )}
        </MapView>
      );
    }
  };

  return (
    <ScrollView style={GlobalStyles.container}>
      <Header onBackPress={() => navigation.goBack()} />
      <View style={GlobalStyles.card}>
        <Text style={GlobalStyles.title}>Add New Bus Stop</Text>

        {error && <Text style={GlobalStyles.errorText}>{error}</Text>}

        <Text style={GlobalStyles.label}>SELECT LOCATION ON MAP</Text>
        {renderMap()}

        <Text style={GlobalStyles.label}>STOP NAME</Text>
        <TextInput
          style={GlobalStyles.input}
          placeholder="Enter stop name"
          value={stopName}
          onChangeText={setStopName}
          placeholderTextColor="#aaa"
        />

        <TouchableOpacity style={GlobalStyles.button} onPress={handleSubmit}>
          <Text style={GlobalStyles.buttonText}>ADD STOP</Text>
        </TouchableOpacity>
      </View>

      <Modal
        visible={showSuccess}
        transparent
        animationType="fade"
        onRequestClose={() => setShowSuccess(false)}
      >
        <View style={SuccessModalStyles.centeredView}>
          <View style={SuccessModalStyles.successModalView}>
            <Text style={SuccessModalStyles.successModalTitle}>Success!</Text>
            <Text style={SuccessModalStyles.successModalText}>Bus stop added successfully.</Text>
            <TouchableOpacity
              style={SuccessModalStyles.successModalButton}
              onPress={() => setShowSuccess(false)}
            >
              <Text style={SuccessModalStyles.successModalButtonText}>OK</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
};

export default AddLocation;