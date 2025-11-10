/**
 * Reusable components for displaying detailed information in list views
 * Used by multiple screens like ViewDrivers, ViewVehicles, etc.
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import GlobalStyles, { COLORS, SPACING, FONT_SIZES } from '../GlobalStyles';

// Props for the DetailRow component
interface DetailRowProps {
  label: string;
  value: string | number;
}

/**
 * DetailRow Component
 * 
 * Displays a label-value pair in a horizontal layout
 * Used in various detail cards throughout the app
 */
export const DetailRow: React.FC<DetailRowProps> = ({ label, value }) => {
  return (
    <View style={GlobalStyles.detailRow}>
      <Text style={GlobalStyles.detailLabel}>{label}:</Text>
      <Text style={GlobalStyles.detailValue}>{value}</Text>
    </View>
  );
};

// Props for the DriverCard component
interface DriverCardProps {
  name: string;
  email: string;
  age: number;
  employmentType: string;
  salary: number;
  onDelete?: () => void;
  showDeleteButton?: boolean;
}

/**
 * DriverCard Component
 * 
 * Displays comprehensive information about a driver
 * Used in the ViewDrivers screen
 */
export const DriverCard: React.FC<DriverCardProps> = ({
  name,
  email,
  age,
  employmentType,
  salary,
  onDelete,
  showDeleteButton = false,
}) => {
  return (
    <View style={styles.card}>
      <DetailRow label="Name" value={name} />
      <DetailRow label="Email" value={email} />
      <DetailRow label="Age" value={age} />
      <DetailRow label="Employment Type" value={employmentType} />
      <DetailRow label="Salary" value={`$${salary} per annum`} />

      {showDeleteButton && onDelete && (
        <TouchableOpacity
          style={GlobalStyles.deleteButton}
          onPress={onDelete}
        >
          <Text style={GlobalStyles.deleteButtonText}>Delete Driver</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

// Props for the VehicleCard component
interface VehicleCardProps {
  licensePlate: string;
  capacity: number;
  disabilitySeats: number;
  onDelete?: () => void;
  showDeleteButton?: boolean;
}

/**
 * VehicleCard Component
 * 
 * Displays information about a vehicle
 * Used in the ViewVehicles screen
 */
export const VehicleCard: React.FC<VehicleCardProps> = ({
  licensePlate,
  capacity,
  disabilitySeats,
  onDelete,
  showDeleteButton = false,
}) => {
  return (
    <View style={styles.card}>
      <DetailRow label="Number Plate" value={licensePlate} />
      <DetailRow label="Capacity" value={capacity} />
      <DetailRow label="Disability Seats" value={disabilitySeats} />

      {showDeleteButton && onDelete && (
        <TouchableOpacity
          style={GlobalStyles.deleteButton}
          onPress={onDelete}
        >
          <Text style={GlobalStyles.deleteButtonText}>Delete Vehicle</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

// Component-specific styles
const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.CARD,
    borderRadius: 12,
    padding: SPACING.LARGE,
    marginBottom: SPACING.LARGE,
    elevation: 3,
    shadowColor: COLORS.TEXT_DARK,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
});

export default {
  DetailRow,
  DriverCard,
  VehicleCard,
};