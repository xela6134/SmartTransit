import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../App';
import Header from '../components/LogoHeader';
import axios from 'axios';
import config from '../config';
import { useAuth } from '../context/AuthContext';

type PastBookingsScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'PastBookings'>;

interface PastBookingsProps {
  navigation: PastBookingsScreenNavigationProp;
}

interface Booking {
  ride_id: number;
  start_location: number;
  end_location: number;
  ride_duration: number;
  ride_status: string;
}

const PastBookings: React.FC<PastBookingsProps> = ({ navigation }) => {
  const { accessToken } = useAuth();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBookings();
  }, []);

  // Fetch the bookings
  const fetchBookings = async () => {
    try {
      const response = await axios.get(`${config.apiUrl}/booking/view`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (response.status === 200) {
        setBookings(response.data.bookings || []);
      }
    } catch (err: any) {
      console.error('Error fetching bookings:', err);
      setError(err.response?.data?.error || 'Failed to fetch bookings');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <Header onBackPress={() => navigation.goBack()} />
        <Text style={styles.title}>Past Bookings</Text>
        <ActivityIndicator size="large" color="#1A237E" style={styles.loader} />
      </View>
    );
  }  

  return (
    <View style={styles.container}>
      <Header onBackPress={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.title}>Past Bookings</Text>
        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}
        {bookings.filter((booking) => booking.ride_status === 'C').length === 0 ? (
          <View style={styles.noBookingsContainer}>
            <Text style={styles.noBookingsText}>No previous bookings found!</Text>
          </View>
        ) : (
          bookings
            .filter((booking) => booking.ride_status === 'C')
            .map((booking, index) => (
            <View key={index} style={styles.bookingCard}>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>From:</Text>
                <Text style={styles.detailValue}>{booking.start_location}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>To:</Text>
                <Text style={styles.detailValue}>{booking.end_location}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Duration:</Text>
                <Text style={styles.detailValue}>{booking.ride_duration} min</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Status:</Text>
                <Text style={styles.detailValue}>Completed</Text>
              </View>
            </View>
          ))
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9f9f9',
    padding: 20,
  },
  scrollContent: {
    paddingBottom: 20,
  },
  centerContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: '#333',
    textAlign: 'center',
    marginVertical: 20,
  },
  bookingCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 15,
  },
  detailLabel: {
    color: '#666',
    fontSize: 14,
  },
  detailValue: {
    fontWeight: '600',
    fontSize: 14,
    textAlign: 'right',
  },
  errorContainer: {
    backgroundColor: '#FFEBEE',
    padding: 10,
    borderRadius: 8,
    marginBottom: 20,
  },
  errorText: {
    color: '#D32F2F',
    textAlign: 'center',
  },
  loadingText: {
    marginTop: 10,
    color: '#1A237E',
    fontSize: 16,
  },
  noBookingsContainer: {
    padding: 20,
    alignItems: 'center',
  },
  noBookingsText: {
    fontSize: 18,
    color: '#666',
    textAlign: 'center',
  },
  activeStatus: {
    color: '#4CAF50',
  },
  inactiveStatus: {
    color: '#9E9E9E',
  },
  deleteButton: {
    backgroundColor: '#FF5252',
    borderRadius: 8,
    paddingVertical: 10,
    marginTop: 10,
    alignItems: 'center',
  },
  deleteButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  loader: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },  
});

export default PastBookings;
