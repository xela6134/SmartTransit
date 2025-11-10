import React, { createContext, useState, useContext, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import config from '../config';

interface AuthContextType {
  isAuthenticated: boolean;
  accessToken: string | null;
  setAccessToken: (token: string | null) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Main code for providing auth
 * - Logging in
 * - Logging out
 * - Token storage
 */
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [accessToken, setAccessTokenState] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check for stored token on app load
    const loadToken = async () => {
      try {
        const token = await AsyncStorage.getItem('access_token');
        if (token) {
          setAccessTokenState(token);
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error('Error loading token:', error);
      }
    };
    loadToken();
  }, []);

  const setAccessToken = async (token: string | null) => {
    try {
      if (token) {
        await AsyncStorage.setItem('access_token', token);
        setAccessTokenState(token);
        setIsAuthenticated(true);
      } else {
        await AsyncStorage.removeItem('access_token');
        setAccessTokenState(null);
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Error setting token:', error);
    }
  };

  const logout = async () => {
    try {
      const response = await axios.post(
        `${config.apiUrl}/auth/logout`,
        {},
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
          },
        }
      );
  
      if (response.status !== 200) {
        console.error('Logout failed:', response.data);
      }
    } catch (error) {
      console.error('Error during logout:', error);
    } finally {
      // Clear the token regardless of the outcome
      await setAccessToken(null);
    }
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, accessToken, setAccessToken, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
