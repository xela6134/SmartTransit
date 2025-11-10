import React from 'react';
import { View, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface HeaderProps {
  onBackPress?: () => void;
}

// Header including the back button
const Header: React.FC<HeaderProps> = ({ onBackPress }) => {
  return (
    <View style={styles.header}>
      {onBackPress && (
        <TouchableOpacity style={styles.backButton} onPress={onBackPress}>
          <Ionicons name="arrow-back" size={24} color="black" />
        </TouchableOpacity>
      )}
      <Image
        source={require('../assets/logo-no-background.png')}
        style={styles.logo}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  header: {
    height: 180,
    justifyContent: 'flex-end',
    alignItems: 'center',
    position: 'relative',
  },
  logo: {
    width: 120,
    height: 89,
  },
  backButton: {
    position: 'absolute',
    top: 91,
    left: 20,
  },
});

export default Header;
