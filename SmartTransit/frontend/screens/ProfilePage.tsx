import React, { useEffect, useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ActivityIndicator, 
  ScrollView, 
  TouchableOpacity, 
  Modal, 
  TextInput, 
  Switch
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import config from '../config';
import { useAuth } from '../context/AuthContext';
import Header from '../components/LogoHeader';
import Footer from '../components/Footer';

interface Profile {
  name: string;
  email: string;
  age?: number;
  phone_number?: string;
  disability?: boolean;
}

const ProfilePage: React.FC = () => {
  const { accessToken } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState<boolean>(false);
  const [showVerifyModal, setShowVerifyModal] = useState<boolean>(false);
  const [verifyPasswordInput, setVerifyPasswordInput] = useState<string>('');
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [editName, setEditName] = useState<string>('');
  const [editEmail, setEditEmail] = useState<string>('');
  const [editAge, setEditAge] = useState<string>('');
  const [editPhone, setEditPhone] = useState<string>('');
  const [editDisability, setEditDisability] = useState<boolean>(false);
  const [editPassword, setEditPassword] = useState<string>('');
  const [showPassword, setShowPassword] = useState<boolean>(false);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await axios.get(`${config.apiUrl}/auth/profile`, {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
          },
        });
        setProfile(response.data);
        // Set default values for the edit form
        setEditName(response.data.name);
        setEditEmail(response.data.email);
        setEditAge(response.data.age ? String(response.data.age) : '');
        setEditPhone(response.data.phone_number || '');
        setEditDisability(response.data.disability === 1);
        setError(null);
      } catch (err: any) {
        console.error("Error fetching profile:", err);
        setError(err.response?.data?.error || "Failed to fetch profile");
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [accessToken]);

  // Start the edit process by showing the verify password modal
  const handleEditPress = () => {
    setShowVerifyModal(true);
    setVerifyPasswordInput('');
    setVerifyError(null);
  };

  // Verify the entered password
  const handleVerifyPassword = async () => {
    try {
      const response = await axios.post(
        `${config.apiUrl}/auth/verify_password`,
        { password: verifyPasswordInput },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
          },
        }
      );
      if (response.status === 200) {
        // Password verified, enable edit mode and close modal
        setEditMode(true);
        setShowVerifyModal(false);
      }
    } catch (err: any) {
      console.error("Password verification failed:", err);
      setVerifyError(err.response?.data?.error || "Verification failed");
    }
  };

  const handleSaveChanges = async () => {
    try {
      const payload = {
        name: editName,
        email: editEmail,
        password: editPassword,   // only change password if user typed one
        age: editAge ? parseInt(editAge, 10) : null,
        phone_number: editPhone,
        disability: editDisability ? 1 : 0,
      };
  
      const response = await axios.patch(`${config.apiUrl}/settings/profile/edit`, payload, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
      });
  
      if (response.status === 200) {
        setProfile(response.data);
        setEditMode(false);
        setEditPassword('');
      }
    } catch (err: any) {
      console.error("Error updating profile:", err);
      setError(err.response?.data?.error || "Failed to update profile");
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#1A237E" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Header />
      <ScrollView>
        <ScrollView style={styles.card}>
          {!editMode ? (
            <>
              <Text style={styles.title}>My Profile</Text>
              {profile && (
                <>
                  <View style={styles.detailRow}>
                    <Text style={styles.label}>FULL NAME</Text>
                    <Text style={styles.value}>{profile.name}</Text>
                  </View>
                  <View style={styles.detailRow}>
                    <Text style={styles.label}>EMAIL ADDRESS</Text>
                    <Text style={styles.value}>{profile.email}</Text>
                  </View>
                  {profile.age !== undefined && (
                    <View style={styles.detailRow}>
                      <Text style={styles.label}>AGE</Text>
                      <Text style={styles.value}>{profile.age}</Text>
                    </View>
                  )}
                  {profile.phone_number && (
                    <View style={styles.detailRow}>
                      <Text style={styles.label}>PHONE NUMBER</Text>
                      <Text style={styles.value}>{profile.phone_number}</Text>
                    </View>
                  )}
                  {profile.disability !== undefined && (
                    <View style={styles.detailRow}>
                      <Text style={styles.label}>DISABILITY</Text>
                      <Text style={styles.value}>{profile.disability === true ? 'Yes' : 'No'}</Text>
                    </View>
                  )}
                </>
              )}
              <TouchableOpacity style={styles.button} onPress={handleEditPress}>
                <Text style={styles.buttonText}>Edit Profile</Text>
              </TouchableOpacity>
            </>
          ) : (
            <>
              <Text style={styles.title}>Edit Profile</Text>
              <View style={styles.form}>
                <Text style={styles.label}>FULL NAME</Text>
                <TextInput 
                  style={styles.input}
                  value={editName}
                  onChangeText={setEditName}
                  placeholder={profile?.name}
                />

                <Text style={styles.label}>EMAIL ADDRESS</Text>
                <TextInput 
                  style={styles.input}
                  value={editEmail}
                  onChangeText={setEditEmail}
                  placeholder={profile?.email}
                  autoCapitalize="none"
                  keyboardType="email-address"
                />

                <Text style={styles.label}>PASSWORD</Text>
                <View style={styles.passwordContainer}>
                  <TextInput
                    style={[styles.input, styles.passwordInput]}
                    value={editPassword}
                    onChangeText={setEditPassword}
                    secureTextEntry={!showPassword}
                    placeholder="Enter new password"
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

                <Text style={styles.label}>AGE</Text>
                <TextInput 
                  style={styles.input}
                  value={editAge}
                  onChangeText={setEditAge}
                  placeholder={profile?.age ? String(profile.age) : ''}
                  keyboardType="numeric"
                />

                <Text style={styles.label}>PHONE NUMBER</Text>
                <TextInput 
                  style={styles.input}
                  value={editPhone}
                  onChangeText={setEditPhone}
                  placeholder={profile?.phone_number || ''}
                  keyboardType="phone-pad"
                />

                <Text style={styles.label}>DISABILITY</Text>
                <View style={styles.switchContainer}>
                  <Text style={styles.switchLabel}>{editDisability ? "Yes" : "No"}</Text>
                  <Switch
                    value={editDisability}
                    onValueChange={setEditDisability}
                  />
                </View>

                <TouchableOpacity style={styles.button} onPress={handleSaveChanges}>
                  <Text style={styles.buttonText}>Save Changes</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.button, { backgroundColor: '#777' }]}
                  onPress={() => setEditMode(false)}
                >
                  <Text style={styles.buttonText}>Cancel</Text>
                </TouchableOpacity>
              </View>
            </>
          )}
        </ScrollView>

        {/* Modal for verifying the user's current password */}
        <Modal
          transparent
          visible={showVerifyModal}
          animationType="slide"
          onRequestClose={() => setShowVerifyModal(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Verify Password</Text>
              <TextInput
                style={styles.modalInput}
                value={verifyPasswordInput}
                onChangeText={setVerifyPasswordInput}
                placeholder="Enter your current password"
                secureTextEntry
              />
              {verifyError && <Text style={styles.errorText}>{verifyError}</Text>}
              <TouchableOpacity style={styles.modalButton} onPress={handleVerifyPassword}>
                <Text style={styles.buttonText}>Verify</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.modalButton, styles.cancelButton]} onPress={() => setShowVerifyModal(false)}>
                <Text style={styles.buttonText}>Cancel</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>
      </ScrollView>
      <Footer />
    </View>
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
  form: {
    marginTop: 10,
  },
  detailRow: {
    marginBottom: 15,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  value: {
    fontSize: 16,
    color: '#333',
    marginBottom: 8,
  },
  button: {
    backgroundColor: '#1A237E',
    borderRadius: 12,
    paddingVertical: 15,
    alignItems: 'center',
    marginTop: 15,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
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
  errorText: {
    color: '#D32F2F',
    fontSize: 16,
    textAlign: 'center',
    marginTop: 5,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    width: '80%',
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    elevation: 4,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 15,
    textAlign: 'center',
  },
  modalInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 10,
    marginBottom: 15,
    fontSize: 16,
    color: '#333',
  },
  modalButton: {
    backgroundColor: '#1A237E',
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
    marginBottom: 10,
  },
  cancelButton: {
    backgroundColor: '#777',
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
  switchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  switchLabel: {
    marginRight: 10,
    fontSize: 16,
    color: '#333',
  },
});

export default ProfilePage;
