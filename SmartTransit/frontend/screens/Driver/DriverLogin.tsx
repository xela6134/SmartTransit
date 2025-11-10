/**
 * 
 * This screen allows a driver to sign in to the system
 */

import type React from "react"
import { useState } from "react"
import { View, TextInput, Text, StyleSheet, TouchableOpacity } from "react-native"
import type { NativeStackNavigationProp } from "@react-navigation/native-stack"
import type { RootStackParamList } from "../../App"
import { Ionicons } from "@expo/vector-icons"
import Header from "../../components/LogoHeader"
import axios from "axios"
import config from "../../config"
import { useAuth } from "../../context/AuthContext"
import { GlobalStyles, COLORS, SPACING, FONT_SIZES } from "../../GlobalStyles";


type DriverLoginScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, "DriverLogin">

interface DriverLoginProps {
  navigation: DriverLoginScreenNavigationProp
}

const DriverLogin: React.FC<DriverLoginProps> = ({ navigation }) => {
  const { setAccessToken } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Logging in functionality for the drivers
  const handleLogin = async () => {
    try {
      if (!email || !password) {
        setError("Email and password are required")
        return;
      }

      const response = await axios.post(`${config.apiUrl}/auth/driver/login`, {
        email,
        password,
      });

      // Only edit tokens if response is 200
      if (response.status === 200 && response.data.access_token) {
        await setAccessToken(response.data.access_token);
        setError(null);
        navigation.navigate("DriverDashboard");
      }
    } catch (error: any) {
      if (error.response) {
        setError(error.response.data.error || 'Invalid credentials');
      } else {
        setError('Network error. Please try again.');
      }
    }
  }

  return (
    <View style={styles.container}>
      <Header onBackPress={() => navigation.navigate("Home")} />
      <View style={styles.card}>
        <Text style={styles.title}>Driver Login</Text>
        <Text style={styles.subtitle}>Access your driver account</Text>
        {error && <Text style={styles.errorText}>{error}</Text>}
        <View style={styles.form}>
          <Text style={styles.label}>EMAIL ADDRESS</Text>
          <TextInput
            style={styles.input}
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
            placeholder="Enter your email"
            placeholderTextColor="#aaa"
          />
          <Text style={styles.label}>PASSWORD</Text>
          <View style={styles.passwordContainer}>
            <TextInput
              style={[styles.input, styles.passwordInput]}
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
              placeholder="Enter your password"
              placeholderTextColor="#aaa"
            />
            <TouchableOpacity style={styles.eyeIcon} onPress={() => setShowPassword(!showPassword)}>
              <Ionicons name={showPassword ? "eye" : "eye-off"} size={24} color="#333" />
            </TouchableOpacity>
          </View>
          <TouchableOpacity style={styles.button} onPress={handleLogin}>
            <Text style={styles.buttonText}>LOGIN</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f9f9f9",
    padding: 20,
  },
  card: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 30,
    marginTop: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 4,
  },
  title: {
    fontSize: 26,
    fontWeight: "700",
    color: "#333",
    textAlign: "center",
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: "#777",
    textAlign: "center",
    marginBottom: 20,
  },
  errorText: {
    color: "#FF0000",
    textAlign: "center",
    marginBottom: 10,
  },
  form: {
    marginTop: 10,
  },
  label: {
    fontSize: 14,
    fontWeight: "600",
    color: "#333",
    marginBottom: 8,
  },
  input: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    fontSize: 16,
    color: "#333",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  passwordContainer: {
    position: "relative",
  },
  passwordInput: {
    paddingRight: 50,
  },
  eyeIcon: {
    position: "absolute",
    right: 16,
    top: 12,
  },
  button: {
    backgroundColor: "#1A237E",
    borderRadius: 12,
    paddingVertical: 15,
    alignItems: "center",
    marginBottom: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 3,
    elevation: 2,
  },
  buttonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
})

export default DriverLogin