/**
 * Component for administrators to view all drivers in the system.
 * Displays a list of drivers with their details.
 */
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../App';
import Header from '../../components/LogoHeader';
import axios from 'axios';
import config from '../../config';
import { useAuth } from '../../context/AuthContext';
import GlobalStyles, { COLORS, SPACING } from '../../GlobalStyles';
import { DriverCard } from '../../components/ListCards';


// Type definition for navigation prop
type ViewDriversNavigationProp = NativeStackNavigationProp<RootStackParamList, 'RegisterDriver'>;

interface ViewDriversProps {
  navigation: ViewDriversNavigationProp;
}

type EmploymentType = 'C' | 'P' | 'F';
interface Driver {
  driver_id: number;
  name: string;
  email: string;
  age: number;
  employee_type: EmploymentType;
  driver_salary: number;
  hire_date: string,
}

/**
 * ViewDrivers Component
 * 
 * Displays a list of all drivers in the system with their details
 */
const ViewDrivers: React.FC<ViewDriversProps> = ({ navigation }) => {
  const { accessToken } = useAuth();
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDrivers();
  }, []);

  /**
   * Fetches the list of drivers from the API
   */
  const fetchDrivers = async () => {
    try {
      const response = await axios.get(`${config.apiUrl}/auth/admin/all_drivers`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (response.status === 200) {
        setDrivers(response.data.drivers || []);
      }
    } catch (err: any) {
      console.error('Error fetching drivers:', err);
      setError(err.response?.data?.error || 'Failed to fetch drivers');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Converts employment type code to a readable label
   */
  const getEmploymentLabel = (type: EmploymentType): string => {
    switch (type) {
      case 'C':
        return 'Casual';
      case 'P':
        return 'Part Time';
      case 'F':
        return 'Full Time';
      default:
        return 'Unknown';
    }
  };

  if (loading) {
    return (
      <View style={[GlobalStyles.container, GlobalStyles.centerContainer]}>
        <Header onBackPress={() => navigation.goBack()} />
        <ActivityIndicator size="large" color={COLORS.PRIMARY} />
        <Text style={GlobalStyles.loadingText}>Loading Drivers...</Text>
      </View>
    );
  }

  return (
    <View style={GlobalStyles.container}>
      <Header onBackPress={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={GlobalStyles.scrollContent}>
        <Text style={GlobalStyles.title}>Drivers</Text>

        {/* Display error if any */}
        {error && (
          <View style={GlobalStyles.errorContainer}>
            <Text style={GlobalStyles.errorText}>{error}</Text>
          </View>
        )}

        {/* Display message if no drivers found */}
        {drivers.length === 0 ? (
          <View style={styles.noDriversContainer}>
            <Text style={styles.noDriversText}>No drivers were found!</Text>
          </View>
        ) : (
          drivers.map((driver) => (
            <DriverCard
              key={driver.driver_id}
              name={driver.name}
              email={driver.email}
              age={driver.age}
              employmentType={getEmploymentLabel(driver.employee_type)}
              salary={driver.driver_salary}
            // Uncomment if delete functionality is implemented
            // showDeleteButton={true}
            // onDelete={() => handleDeleteDriver(driver.driver_id)}
            />
          ))
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  noDriversContainer: {
    padding: SPACING.LARGE,
    alignItems: 'center',
  },
  noDriversText: {
    fontSize: 18,
    color: COLORS.TEXT_LIGHT,
    textAlign: 'center',
  },
});

export default ViewDrivers;