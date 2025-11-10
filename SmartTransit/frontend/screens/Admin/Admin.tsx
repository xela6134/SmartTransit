/**
 * Main administration dashboard providing access to various management functions.
 * Handles authentication state and provides navigation to all admin features.
 */


import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../App';
import Header from '../../components/LogoHeader';
import { useAuth } from '../../context/AuthContext';
import config from '../../config';
import axios from 'axios';
import GlobalStyles, { COLORS, SPACING } from '../../GlobalStyles';


// Type definition for navigation prop
type AdminScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Admin'>;

interface AdminProps {
  navigation: AdminScreenNavigationProp;
}

/**
 * AdminPage Component
 * 
 * Central administration dashboard with access to all management functions
 * Conditionally renders based on authentication state
 */
const AdminPage: React.FC<AdminProps> = ({ navigation }) => {
  const { isAuthenticated, logout, accessToken } = useAuth();
  const [username, setUsername] = useState<string | null>(null);

  /**
   * Fetch user information
   */
  useEffect(() => {
    const fetchUserStatus = async () => {
      try {
        const response = await axios.get(`${config.apiUrl}/auth/status`, {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
          },
        });
        setUsername(response.data.name);
      } catch (error) {
        setUsername(null);
      }
    };

    if (isAuthenticated) {
      fetchUserStatus();
    }
  }, [isAuthenticated, accessToken]);

  /**
  * Handle user logout
  */
  const handleLogout = async () => {
    await logout();
    setUsername(null);
  };

  /**
   * Render the admin dashboard when authenticated
   */  if (isAuthenticated) {
    return (
      <View style={GlobalStyles.container}>
        <Header onBackPress={() => navigation.navigate('Home')} />

        <ScrollView contentContainerStyle={styles.cardContent}>
          <Text style={GlobalStyles.welcomeText}>
            Welcome, {username ? username : 'User'}!
          </Text>

          {/* Admin navigation buttons */}
          <TouchableOpacity
            style={GlobalStyles.button}
            onPress={() => navigation.navigate('ReportGenerator')}
          >
            <Text style={GlobalStyles.buttonText}>GENERATE REPORT</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={GlobalStyles.button}
            onPress={() => navigation.navigate('RegisterDriver')}
          >
            <Text style={GlobalStyles.buttonText}>REGISTER DRIVER</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={GlobalStyles.button}
            onPress={() => navigation.navigate('ViewDrivers')}
          >
            <Text style={GlobalStyles.buttonText}>VIEW DRIVERS</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={GlobalStyles.button}
            onPress={() => navigation.navigate('RegisterVehicle')}
          >
            <Text style={GlobalStyles.buttonText}>ADD VEHICLE</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={GlobalStyles.button}
            onPress={() => navigation.navigate('ViewVehicles')}
          >
            <Text style={GlobalStyles.buttonText}>VIEW VEHICLES</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={GlobalStyles.button}
            onPress={() => navigation.navigate('AddLocation')}
          >
            <Text style={GlobalStyles.buttonText}>MAKE LOCATION</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={GlobalStyles.button}
            onPress={() => navigation.navigate('AdminViewLocations')}
          >
            <Text style={GlobalStyles.buttonText}>VIEW LOCATIONS</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={GlobalStyles.button}
            onPress={handleLogout}
          >
            <Text style={GlobalStyles.buttonText}>LOGOUT</Text>
          </TouchableOpacity>
        </ScrollView>
      </View>
    );
  }

  /**
   * Render login/register options when not authenticated
   */
  return (
    <View style={GlobalStyles.container}>
      <Header />
      <View style={GlobalStyles.card}>
        <Text style={GlobalStyles.title}>Welcome to SmartTransit</Text>
        <Text style={GlobalStyles.subtitle}>
          Your intelligent transportation companion
        </Text>
        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={GlobalStyles.button}
            onPress={() => navigation.navigate('SignIn')}
          >
            <Text style={GlobalStyles.buttonText}>SIGN IN</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.registerButton}
            onPress={() => navigation.navigate('Register')}
          >
            <Text style={styles.registerButtonText}>CREATE ACCOUNT</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.driverLoginButton}
            onPress={() => navigation.navigate('DriverLogin')}
          >
            <Text style={styles.driverLoginText}>LOGIN FOR DRIVERS</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
};

// Component-specific styles (only styles not in GlobalStyles)
const styles = StyleSheet.create({
  cardContent: {
    backgroundColor: COLORS.CARD,
    borderRadius: 12,
    padding: SPACING.XLARGE,
    marginTop: SPACING.LARGE,
    shadowColor: COLORS.TEXT_DARK,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 4,
    alignItems: 'center',
  },
  buttonContainer: {
    width: '100%',
  },
  registerButton: {
    backgroundColor: COLORS.CARD,
    borderWidth: 2,
    borderColor: COLORS.PRIMARY,
    borderRadius: 12,
    paddingVertical: 15,
    paddingHorizontal: 20,
    marginVertical: SPACING.SMALL,
    width: '100%',
    alignItems: 'center',
  },
  registerButtonText: {
    color: COLORS.PRIMARY,
    fontSize: 16,
    fontWeight: '600',
  },
  driverLoginButton: {
    backgroundColor: '#f5f5f5',
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    paddingVertical: 10,
    marginTop: 20,
    width: '100%',
    alignItems: 'center',
  },
  driverLoginText: {
    color: COLORS.TEXT_MEDIUM,
    fontSize: 14,
    fontWeight: '500',
  },
});

export default AdminPage;
