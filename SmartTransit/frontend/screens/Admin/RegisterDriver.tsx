/**
 * 
 * This screen allows administrators to register new drivers to the system.
 */

import React, { useState } from 'react';
import { View, TextInput, Text, StyleSheet, TouchableOpacity, ScrollView, Modal, FlatList, SafeAreaView, Platform } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../App';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/LogoHeader';
import axios from 'axios';
import config from '../../config';
import DateTimePicker from '@react-native-community/datetimepicker';
import { useAuth } from '../../context/AuthContext';
import GlobalStyles, { SuccessModalStyles } from '../../GlobalStyles';

type RegisterDriverNavigationProp = NativeStackNavigationProp<RootStackParamList, 'RegisterDriver'>;

interface RegisterDriverProps {
  navigation: RegisterDriverNavigationProp;
}

const RegisterDriver: React.FC<RegisterDriverProps> = ({ navigation }) => {
  const { accessToken } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [age, setAge] = useState('');
  const [driverType, setDriverType] = useState('');
  const [driverTypeLabel, setDriverTypeLabel] = useState('Select employment type');
  const [salary, setSalary] = useState('');
  const [hireDate, setHireDate] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showDriverTypeModal, setShowDriverTypeModal] = useState(false);
  const [datePickerDate, setDatePickerDate] = useState(new Date());
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  const employmentTypes = [
    { label: 'Casual', value: 'C' },
    { label: 'Part Time', value: 'P' },
    { label: 'Full Time', value: 'F' },
  ];

  // Main registering functionality
  // Handles input validation & backend calls
  const handleRegister = async () => {
    try {
      if (!name || !email || !password || !confirmPassword || !age || !driverType
        || !salary || !hireDate
      ) {
        setError('All fields are required');
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match');
        return;
      }

      const payload = {
        name,
        email,
        password,
        age: parseInt(age, 10),
        employee_type: driverType,
        driver_salary: parseInt(salary, 10),
        hire_date: hireDate,
      };

      const response = await axios.post(`${config.apiUrl}/auth/admin/register_driver`, payload, {
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

  const onDateChange = (event: any, selectedDate: Date | undefined) => {
    const currentDate = selectedDate || datePickerDate;

    // For iOS, no need to immediately close the picker
    if (Platform.OS === 'android') {
      setShowDatePicker(false);
    }

    setDatePickerDate(currentDate);
    setHireDate(currentDate.toLocaleDateString());
  };

  // Different selection menus
  const selectDriverType = (item: { label: string, value: string }) => {
    setDriverType(item.value);
    setDriverTypeLabel(item.label);
    setShowDriverTypeModal(false);
  };

  const openDriverTypeDropdown = () => {
    setShowDriverTypeModal(true);
  };

  const openDatePicker = () => {
    setShowDatePicker(true);
  };

  // Function to confirm iOS date selection
  const confirmIOSDate = () => {
    setShowDatePicker(false);
  };

  return (
    <ScrollView style={styles.container}>
      <Header onBackPress={() => navigation.goBack()} />
      <View style={styles.card}>
        <Text style={styles.title}>Add Driver</Text>

        {error && <Text style={styles.errorText}>{error}</Text>}

        <View style={styles.form}>
          <Text style={styles.label}>FULL NAME</Text>
          <TextInput
            style={styles.input}
            value={name}
            onChangeText={setName}
            placeholder="Enter driver's full name"
            placeholderTextColor="#aaa"
          />

          <Text style={styles.label}>EMAIL ADDRESS</Text>
          <TextInput
            style={styles.input}
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
            placeholder="Enter driver's email"
            placeholderTextColor="#aaa"
          />

          <Text style={styles.label}>PASSWORD</Text>
          <View style={styles.passwordContainer}>
            <TextInput
              style={[styles.input, styles.passwordInput]}
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
              placeholder="Create a password for driver"
              placeholderTextColor="#aaa"
            />
            <TouchableOpacity
              style={styles.eyeIcon}
              onPress={() => setShowPassword(!showPassword)}
            >
              <Ionicons
                name={showPassword ? "eye" : "eye-off"}
                size={24}
                color="#333"
              />
            </TouchableOpacity>
          </View>

          <Text style={styles.label}>CONFIRM PASSWORD</Text>
          <TextInput
            style={styles.input}
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            secureTextEntry={!showPassword}
            placeholder="Confirm driver's password"
            placeholderTextColor="#aaa"
          />

          <Text style={styles.label}>AGE</Text>
          <TextInput
            style={styles.input}
            value={age}
            onChangeText={setAge}
            keyboardType="numeric"
            placeholder="Enter driver's age"
            placeholderTextColor="#aaa"
          />

          <Text style={styles.label}>EMPLOYMENT TYPE</Text>
          <TouchableOpacity
            style={styles.selectButton}
            onPress={openDriverTypeDropdown}
            activeOpacity={0.7}
          >
            <Text style={driverType ? styles.selectButtonText : styles.selectButtonPlaceholder}>
              {driverTypeLabel}
            </Text>
            <Ionicons name="chevron-down" size={20} color="#777" />
          </TouchableOpacity>

          <Text style={styles.label}>SALARY</Text>
          <TextInput
            style={styles.input}
            value={salary}
            onChangeText={setSalary}
            keyboardType="numeric"
            placeholder="Enter driver's salary"
            placeholderTextColor="#aaa"
          />

          <Text style={styles.label}>HIRE DATE</Text>
          <TouchableOpacity
            style={styles.selectButton}
            onPress={openDatePicker}
            activeOpacity={0.7}
          >
            <Text style={hireDate ? styles.selectButtonText : styles.selectButtonPlaceholder}>
              {hireDate || 'Select Hire Date'}
            </Text>
            <Ionicons name="calendar-outline" size={20} color="#777" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.button}
            onPress={handleRegister}
          >
            <Text style={styles.buttonText}>CREATE DRIVER'S ACCOUNT</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Employment Type Dropdown Modal */}
      <Modal
        visible={showDriverTypeModal}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setShowDriverTypeModal(false)}
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Select Employment Type</Text>
            <TouchableOpacity onPress={() => setShowDriverTypeModal(false)}>
              <Ionicons name="close" size={24} color="#333" />
            </TouchableOpacity>
          </View>
          <FlatList
            data={employmentTypes}
            keyExtractor={(item) => item.value}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={styles.modalItem}
                onPress={() => selectDriverType(item)}
              >
                <Text style={styles.modalItemText}>{item.label}</Text>
                {item.value === driverType && (
                  <Ionicons name="checkmark" size={20} color="#1A237E" />
                )}
              </TouchableOpacity>
            )}
            style={styles.modalList}
          />
        </SafeAreaView>
      </Modal>

      {/* Date Picker for iOS */}
      {Platform.OS === 'ios' && showDatePicker && (
        <Modal
          transparent={true}
          animationType="slide"
          visible={showDatePicker}
          onRequestClose={() => setShowDatePicker(false)}
        >
          <View style={styles.centeredView}>
            <View style={styles.datePickerModalView}>
              <View style={styles.datePickerHeader}>
                <TouchableOpacity onPress={() => setShowDatePicker(false)}>
                  <Text style={styles.datePickerCancelText}>Cancel</Text>
                </TouchableOpacity>
                <Text style={styles.datePickerHeaderText}>Select Date</Text>
                <TouchableOpacity onPress={confirmIOSDate}>
                  <Text style={styles.datePickerDoneText}>Done</Text>
                </TouchableOpacity>
              </View>
              <DateTimePicker
                value={datePickerDate}
                mode="date"
                display="spinner"
                onChange={onDateChange}
                style={styles.datePicker}
              />
            </View>
          </View>
        </Modal>
      )}

      {/* Date Picker for Android */}
      {Platform.OS === 'android' && showDatePicker && (
        <DateTimePicker
          value={datePickerDate}
          mode="date"
          display="default"
          onChange={onDateChange}
        />
      )}
      {/* Success Modal */}
      <Modal
        visible={showSuccessModal}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setShowSuccessModal(false)}
      >
        <View style={styles.centeredView}>
          <View style={styles.successModalView}>
            <View style={styles.successIconContainer}>
              <Ionicons name="checkmark-circle" size={60} color="#4CAF50" />
            </View>
            <Text style={styles.successModalTitle}>Success!</Text>
            <Text style={styles.successModalText}>
              Driver account has been created successfully.
            </Text>
            <TouchableOpacity
              style={styles.successModalButton}
              onPress={() => setShowSuccessModal(false)}
            >
              <Text style={styles.successModalButtonText}>OK</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9f9f9',
    padding: 20,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 30,
    marginTop: 20,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: '#333',
    textAlign: 'center',
    marginBottom: 8,
  },
  errorText: {
    color: '#FF0000',
    textAlign: 'center',
    marginBottom: 10,
  },
  form: {
    marginTop: 10,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    fontSize: 16,
    color: '#333',
  },
  passwordContainer: {
    position: 'relative',
  },
  passwordInput: {
    paddingRight: 50,
  },
  eyeIcon: {
    position: 'absolute',
    right: 16,
    top: 12,
  },
  selectButton: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  selectButtonText: {
    fontSize: 16,
    color: '#333',
  },
  selectButtonPlaceholder: {
    fontSize: 16,
    color: '#aaa',
  },
  button: {
    backgroundColor: '#1A237E',
    borderRadius: 12,
    paddingVertical: 15,
    alignItems: 'center',
    marginVertical: 10,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 3,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'white',
    marginTop: 50,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  modalList: {
    flex: 1,
  },
  modalItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  modalItemText: {
    fontSize: 16,
    color: '#333',
  },
  centeredView: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  datePickerModalView: {
    backgroundColor: 'white',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  datePickerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  datePickerHeaderText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  datePickerCancelText: {
    fontSize: 16,
    color: '#777',
  },
  datePickerDoneText: {
    fontSize: 16,
    color: '#1A237E',
    fontWeight: '600',
  },
  datePicker: {
    height: 200,
  },
  successModalView: {
    margin: 20,
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 35,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
    width: '80%',
    maxWidth: 400,
    alignSelf: 'center',
  },
  successIconContainer: {
    marginBottom: 20,
  },
  successModalTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  successModalText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  successModalButton: {
    backgroundColor: '#1A237E',
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 30,
    elevation: 2,
  },
  successModalButtonText: {
    color: 'white',
    fontWeight: 'bold',
    textAlign: 'center',
    fontSize: 16,
  },
});

export default RegisterDriver;