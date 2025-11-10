// PaymentScreen.tsx
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Button, Alert, Pressable } from 'react-native';
import { useStripe } from '@stripe/stripe-react-native';
import axios from 'axios';
import config from '../config';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../App';
import { useAuth } from '../context/AuthContext';

type PaymentScreenProps = NativeStackScreenProps<RootStackParamList, 'Payment'>;

const PaymentScreen: React.FC<PaymentScreenProps> = ({ route, navigation }) => {
  const { rideId } = route.params!;
  const { accessToken } = useAuth();
  const { initPaymentSheet, presentPaymentSheet } = useStripe(); // Payment form is not created by us - we are using Stripe's given libraries
  const [loading, setLoading] = useState(false);

  // Fetch the PaymentIntent client secret from backend
  const fetchPaymentSheetParams = async () => {
    try {
      const response = await axios.post(
        `${config.apiUrl}/payment/create-intent`,
        { ride_id: rideId },
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
      const { clientSecret } = response.data;
      return { clientSecret };
    } catch (err: any) {
      Alert.alert(
        "Error fetching payment intent",
        err.response?.data?.error || err.message
      );
      throw err;
    }
  };

  // Initialize the PaymentSheet with the client secret from backend
  const initialisePaymentSheet = async () => {
    try {
      const { clientSecret } = await fetchPaymentSheetParams();
      const { error } = await initPaymentSheet({
        merchantDisplayName: "SmartTransit",
        paymentIntentClientSecret: clientSecret,
        allowsDelayedPaymentMethods: true, 
        defaultBillingDetails: {
          name: 'Jane Doe',
        },
      });
      if (!error) {
        setLoading(true);
      } else {
        Alert.alert("PaymentSheet Initialization Error", error.message);
      }
    } catch (error) {
      console.error("Error during PaymentSheet initialization", error);
    }
  };

  // Present the PaymentSheet when the user taps Checkout
  const openPaymentSheet = async () => {
    try {
      const { error } = await presentPaymentSheet();
      if (error) {
        Alert.alert(`Error code: ${error.code}`, error.message);
        console.error("presentPaymentSheet error:", error);
      } else {
        Alert.alert('Success', 'Your order is confirmed!');
        navigation.navigate('Home');
      }
    } catch (err) {
      console.error("Error presenting PaymentSheet:", err);
      Alert.alert("Payment error", "An unexpected error occurred");
    }
  };

  useEffect(() => {
    initialisePaymentSheet();
  }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Confirm Payment</Text>
      <Pressable
        style={({ pressed }) => [
          styles.button,
          !loading && styles.buttonDisabled,
          pressed && styles.buttonPressed
        ]}
        onPress={openPaymentSheet}
        disabled={!loading}
      >
        <Text style={styles.buttonText}>Checkout</Text>
      </Pressable>

      <Pressable
        style={({ pressed }) => [styles.outlinedButton, pressed && styles.buttonPressed]}
        onPress={() => navigation.navigate("Home")}
      >
        <Text style={styles.outlinedText}>Go to Home</Text>
      </Pressable>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 16 },
  title: { fontSize: 24, marginBottom: 20 },
  button: {
    backgroundColor: '#1A237E',
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 10,
    marginVertical: 10,
    width: '100%',
    alignItems: 'center',
  },
  buttonDisabled: {
    backgroundColor: '#9FA8DA',
  },
  buttonPressed: {
    opacity: 0.8,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  outlinedButton: {
    borderColor: '#1A237E',
    borderWidth: 2,
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 10,
    marginTop: 10,
    width: '100%',
    alignItems: 'center',
  },
  outlinedText: {
    color: '#1A237E',
    fontSize: 16,
    fontWeight: '600',
  }, 
});

export default PaymentScreen;
