import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StripeProvider } from '@stripe/stripe-react-native';
import SignIn from './screens/SignInPage';
import Register from './screens/RegisterPage';
import ForgotPassword from './screens/ForgotPassword';
import ResetPassword from './screens/ResetPassword';
import Homepage from './screens/Homepage';
import ProfilePage from './screens/ProfilePage';
import { AuthProvider } from './context/AuthContext';
import BookingPage from "./screens/BookingPage";
import PastBookings from "./screens/PastBookings";
import AdminPage from "./screens/Admin/Admin";
import RegisterDriver from './screens/Admin/RegisterDriver';
import ReportGenerator from './screens/Admin/ReportGenerator';
import RegisterVehicle from './screens/Admin/RegisterVehicle';
import DriverLogin from "./screens/Driver/DriverLogin"
import DriverDashboard from "./screens/Driver/DriverDashboard"

import ViewDrivers from './screens/Admin/ViewDriver';
import CurrentBookings from "./screens/CurrentBookings";
import PaymentScreen from "./screens/PaymentScreen";
import ViewVehicles from './screens/Admin/ViewVehicles';
import AddLocation from './screens/Admin/AddLocation';
import AdminViewLocations from './screens/Admin/ViewLocations';
import config from './config';

export type RootStackParamList = {
  Home: undefined;
  SignIn: undefined;
  Register: undefined;
  Booking: undefined;
  Payment: { rideId: number };
  PastBookings: undefined;
  CurrentBookings: undefined;
  Profile: undefined;
  Admin: undefined;
  RegisterDriver: undefined;
  ReportGenerator: undefined;
  RegisterVehicle: undefined;
  DriverLogin: undefined;
  DriverDashboard: undefined;
  ViewDrivers: undefined;
  ViewVehicles: undefined;
  AddLocation: undefined;
  AdminViewLocations: undefined;
  ForgotPassword: undefined;
  ResetPassword: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

const App: React.FC = () => {
  return (
    <AuthProvider>
      <StripeProvider publishableKey={config.publishable_key}>
        <NavigationContainer>
          <Stack.Navigator initialRouteName="Home">
            <Stack.Screen name="Home" component={Homepage} options={{ headerShown: false }} />
            <Stack.Screen name="SignIn" component={SignIn} options={{ headerShown: false }} />
            <Stack.Screen name="Register" component={Register} options={{ headerShown: false }} />
            <Stack.Screen name="ForgotPassword" component={ForgotPassword} options={{ headerShown: false }} />
            <Stack.Screen name="ResetPassword" component={ResetPassword} options={{ headerShown: false }} />
            <Stack.Screen name="Booking" component={BookingPage} options={{ headerShown: false }} />
            <Stack.Screen name="Payment" component={PaymentScreen} options={{ headerShown: false }} />
            <Stack.Screen name="PastBookings" component={PastBookings} options={{ headerShown: false }} />
            <Stack.Screen name="CurrentBookings" component={CurrentBookings} options={{ headerShown: false }} />
            <Stack.Screen name="Profile" component={ProfilePage} options={{ headerShown: false }} />
            <Stack.Screen name="Admin" component={AdminPage} options={{ headerShown: false }} />
            <Stack.Screen name="RegisterDriver" component={RegisterDriver} options={{ headerShown: false }} />
            <Stack.Screen name="ReportGenerator" component={ReportGenerator} options={{ headerShown: false }} />
            <Stack.Screen name="RegisterVehicle" component={RegisterVehicle} options={{ headerShown: false }} />
            <Stack.Screen name="DriverLogin" component={DriverLogin} options={{ headerShown: false }} />
            <Stack.Screen name="DriverDashboard" component={DriverDashboard} options={{ headerShown: false }} />
            <Stack.Screen name="ViewDrivers" component={ViewDrivers} options={{ headerShown: false }} />
            <Stack.Screen name="ViewVehicles" component={ViewVehicles} options={{ headerShown: false }} />
            <Stack.Screen name="AddLocation" component={AddLocation} options={{ headerShown: false }} />
            <Stack.Screen name="AdminViewLocations" component={AdminViewLocations} options={{ headerShown: false }} />
          </Stack.Navigator>
        </NavigationContainer>
      </StripeProvider>
    </AuthProvider>
  );
};

export default App;
