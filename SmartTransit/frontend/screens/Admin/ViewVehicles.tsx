
/**
 * Component for administrators to view all vehicles in the system.
 * Displays a list of vehicles with their details.
 */

import React, { useState, useEffect } from 'react';
import { View, TextInput, Text, StyleSheet, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../App';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/LogoHeader';
import axios from 'axios';
import config from '../../config';
import { useAuth } from '../../context/AuthContext';
import GlobalStyles, { COLORS, SPACING } from '../../GlobalStyles';
import { VehicleCard } from '../../components/ListCards';

// Type definition for navigation prop
type ViewVehiclesNavigationProp = NativeStackNavigationProp<RootStackParamList, 'RegisterDriver'>;

interface ViewVehiclesProps {
  navigation: ViewVehiclesNavigationProp;
}

interface Vehicle {
  licence_number: string;
  capacity: number;
  disability_seats: number;
}

/**
 * ViewVehicles Component
 * 
 * Displays a list of all vehicles in the system with their details
 */
const ViewVehicles: React.FC<ViewVehiclesProps> = ({ navigation }) => {
  const { accessToken } = useAuth();
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchVehicles();
  }, []);

  /**
   * Fetches the list of vehicles from the API
   */
  const fetchVehicles = async () => {
    try {
      const response = await axios.get(`${config.apiUrl}/auth/admin/all_vehicles`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (response.status === 200) {
        setVehicles(response.data.vehicles || []);
      }
    } catch (err: any) {
      console.error('Error fetching vehicles:', err);
      setError(err.response?.data?.error || 'Failed to fetch vehicles');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={[GlobalStyles.container, GlobalStyles.centerContainer]}>
        <Header onBackPress={() => navigation.goBack()} />
        <ActivityIndicator size="large" color={COLORS.PRIMARY} />
        <Text style={GlobalStyles.loadingText}>Loading Vehicles...</Text>
      </View>
    );
  }

  return (
    <View style={GlobalStyles.container}>
      <Header onBackPress={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={GlobalStyles.scrollContent}>
        <Text style={GlobalStyles.title}>Vehicles</Text>

        {/* Display error if any */}
        {error && (
          <View style={GlobalStyles.errorContainer}>
            <Text style={GlobalStyles.errorText}>{error}</Text>
          </View>
        )}

        {/* Display message if no vehicles found */}
        {vehicles.length === 0 ? (
          <View style={styles.noVehiclesContainer}>
            <Text style={styles.noVehiclesText}>No vehicles were found!</Text>
          </View>
        ) : (
          vehicles.map((vehicle, index) => (
            <VehicleCard
              key={index}
              licensePlate={vehicle.licence_number}
              capacity={vehicle.capacity}
              disabilitySeats={vehicle.disability_seats}
            // Uncomment if delete functionality is implemented
            // showDeleteButton={true}
            // onDelete={() => handleDeleteVehicle(vehicle.licence_number)}
            />
          ))
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  noVehiclesContainer: {
    padding: SPACING.LARGE,
    alignItems: 'center',
  },
  noVehiclesText: {
    fontSize: 18,
    color: COLORS.TEXT_LIGHT,
    textAlign: 'center',
  },
});

export default ViewVehicles;