/**
 * 
 * This screen allows administrators to add new vehicles to the system.
 */

import React, { useState } from 'react';
import { View, TextInput, Text, StyleSheet, TouchableOpacity, Modal } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../App';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/LogoHeader';
import axios from 'axios';
import config from '../../config';
import { useAuth } from '../../context/AuthContext';
import GlobalStyles, { COLORS, SuccessModalStyles } from '../../GlobalStyles';

// Type definition for the navigation prop
type RegisterVehicleNavigationProp = NativeStackNavigationProp<RootStackParamList, 'RegisterDriver'>;

interface RegisterVehicleProps {
  navigation: RegisterVehicleNavigationProp;
}

/**
 * RegisterVehicle Component
 * 
 * Form for adding new vehicles to the system with validation
 */
const RegisterVehicle: React.FC<RegisterVehicleProps> = ({ navigation }) => {
  const { accessToken } = useAuth();

  const [numberPlate, setNumberPlate] = useState('');
  const [capacity, setCapacity] = useState('');
  const [disabilitySeats, setDisabilitySeats] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  /**
   * Handles the vehicle registration process
   * Validates form input and makes API call
   */

  const handleRegister = async () => {
    try {
      if (!numberPlate || !capacity || !disabilitySeats) {
        setError('All fields are required');
        return;
      }

      const payload = {
        licence_number: numberPlate,
        capacity: parseInt(capacity, 10),
        disability_seats: parseInt(disabilitySeats, 10),
      };

      const response = await axios.post(`${config.apiUrl}/auth/admin/add_vehicle`, payload, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (response.status === 201) {
        setShowSuccessModal(true);
        navigation.navigate('Admin');
      }
    } catch (error: any) {
      if (error.response) {
        setError(error.response.data.error || 'Registration failed');
      } else {
        setError('Network error. Please try again.');
      }
    }
  };


  return (
    <View style={GlobalStyles.container}>
      <Header onBackPress={() => navigation.goBack()} />
      <View style={GlobalStyles.card}>
        <Text style={GlobalStyles.title}>Add Vehicle</Text>

        {error && <Text style={GlobalStyles.errorText}>{error}</Text>}

        <View style={GlobalStyles.form}>
          <Text style={GlobalStyles.label}>NUMBER PLATE</Text>
          <TextInput
            style={GlobalStyles.input}
            value={numberPlate}
            onChangeText={setNumberPlate}
            placeholder="Enter vehicle's number plate"
            placeholderTextColor="#aaa"
          />

          <Text style={GlobalStyles.label}>CAPACITY</Text>
          <TextInput
            style={GlobalStyles.input}
            value={capacity}
            onChangeText={setCapacity}
            keyboardType="numeric"
            placeholder="Enter vehicle's capacity"
            placeholderTextColor="#aaa"
          />

          <Text style={GlobalStyles.label}>DISABILITY SEATS</Text>
          <TextInput
            style={GlobalStyles.input}
            value={disabilitySeats}
            onChangeText={setDisabilitySeats}
            keyboardType="numeric"
            placeholder="Enter vehicle's disability seats"
            placeholderTextColor="#aaa"
          />

          <TouchableOpacity
            style={GlobalStyles.button}
            onPress={handleRegister}
          >
            <Text style={GlobalStyles.buttonText}>ADD VEHICLE</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Success Modal - Shown after successful vehicle registration */}
      <Modal
        visible={showSuccessModal}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setShowSuccessModal(false)}
      >
        <View style={SuccessModalStyles.centeredView}>
          <View style={SuccessModalStyles.successModalView}>
            <View style={SuccessModalStyles.successIconContainer}>
              <Ionicons name="checkmark-circle" size={60} color={COLORS.SUCCESS} />
            </View>
            <Text style={SuccessModalStyles.successModalTitle}>Success!</Text>
            <Text style={SuccessModalStyles.successModalText}>
              Vehicle has been added successfully.
            </Text>
            <TouchableOpacity
              style={SuccessModalStyles.successModalButton}
              onPress={() => setShowSuccessModal(false)}
            >
              <Text style={SuccessModalStyles.successModalButtonText}>OK</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

export default RegisterVehicle;