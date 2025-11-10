/**
 * This file contains shared styles used across multiple components in the application.
 * Centralizing styles improves consistency and makes maintenance easier.
 */

import { StyleSheet } from 'react-native';

// Color palette for the application
export const COLORS = {
  PRIMARY: '#1A237E',
  SUCCESS: '#4CAF50',
  ERROR: '#D32F2F',
  ERROR_LIGHT: '#FFEBEE',
  ERROR_BUTTON: '#FF5252',
  DELETE_RED: '#B71C1C',
  TEXT_DARK: '#333',
  TEXT_MEDIUM: '#555',
  TEXT_LIGHT: '#666',
  TEXT_VERY_LIGHT: '#777',
  TEXT_WHITE: '#fff',
  BORDER: '#ddd',
  BORDER_LIGHT: '#eee',
  BACKGROUND: '#f9f9f9',
  CARD: '#fff',
  BUTTON_DISABLED: '#ccc',
};

// Common sizes and spacing
export const SPACING = {
  SMALL: 8,
  MEDIUM: 16,
  LARGE: 20,
  XLARGE: 30,
};

// Font sizes standardized across the app
export const FONT_SIZES = {
  SMALL: 14,
  MEDIUM: 16,
  LARGE: 18,
  XLARGE: 22,
  TITLE: 26,
  WELCOME: 28,
};

// Common style patterns used across components
export const GlobalStyles = StyleSheet.create({
  // Container styles
  container: {
    flex: 1,
    backgroundColor: COLORS.BACKGROUND,
    padding: SPACING.LARGE,
  },

  centerContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },

  scrollContent: {
    paddingBottom: SPACING.LARGE,
  },

  // Card styles
  card: {
    backgroundColor: COLORS.CARD,
    borderRadius: 12,
    padding: SPACING.XLARGE,
    marginTop: SPACING.LARGE,
    elevation: 4,
    shadowColor: COLORS.TEXT_DARK,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },

  // Typography styles
  title: {
    fontSize: FONT_SIZES.TITLE,
    fontWeight: '700',
    color: COLORS.TEXT_DARK,
    textAlign: 'center',
    marginBottom: SPACING.MEDIUM,
  },

  subtitle: {
    fontSize: FONT_SIZES.MEDIUM,
    color: COLORS.TEXT_VERY_LIGHT,
    textAlign: 'center',
    marginBottom: SPACING.XLARGE,
  },

  welcomeText: {
    fontSize: FONT_SIZES.WELCOME,
    fontWeight: '700',
    color: COLORS.TEXT_DARK,
    marginBottom: 25,
  },

  label: {
    fontSize: FONT_SIZES.SMALL,
    fontWeight: '600',
    color: COLORS.TEXT_DARK,
    marginBottom: SPACING.SMALL,
  },

  errorText: {
    color: COLORS.ERROR,
    textAlign: 'center',
    marginBottom: SPACING.MEDIUM,
  },

  loadingText: {
    marginTop: SPACING.MEDIUM,
    color: COLORS.PRIMARY,
    fontSize: FONT_SIZES.MEDIUM,
  },

  // Form styles
  form: {
    marginTop: SPACING.MEDIUM,
  },

  input: {
    backgroundColor: COLORS.CARD,
    borderWidth: 1,
    borderColor: COLORS.BORDER,
    borderRadius: 8,
    padding: 12,
    marginBottom: SPACING.MEDIUM,
    fontSize: FONT_SIZES.MEDIUM,
    color: COLORS.TEXT_DARK,
  },

  // Button styles
  button: {
    backgroundColor: COLORS.PRIMARY,
    borderRadius: 12,
    paddingVertical: 15,
    alignItems: 'center',
    marginVertical: SPACING.SMALL,
    elevation: 2,
    shadowColor: COLORS.TEXT_DARK,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 3,
    width: '100%',
  },

  buttonText: {
    color: COLORS.TEXT_WHITE,
    fontSize: FONT_SIZES.MEDIUM,
    fontWeight: '600',
  },

  deleteButton: {
    backgroundColor: COLORS.DELETE_RED,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 11,
    marginTop: SPACING.MEDIUM,
    alignItems: 'center',
  },

  deleteButtonText: {
    color: COLORS.TEXT_WHITE,
    fontSize: FONT_SIZES.SMALL,
    fontWeight: '600',
  },

  // List item styles
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 15,
  },

  detailLabel: {
    color: COLORS.TEXT_LIGHT,
    fontSize: FONT_SIZES.SMALL,
  },

  detailValue: {
    fontWeight: '600',
    fontSize: FONT_SIZES.SMALL,
    textAlign: 'right',
  },

  // Error container
  errorContainer: {
    backgroundColor: COLORS.ERROR_LIGHT,
    padding: SPACING.MEDIUM,
    borderRadius: 8,
    marginBottom: SPACING.LARGE,
  },

  // Modal styles
  modalOverlay: {
    flex: 1,
    justifyContent: 'center',
    backgroundColor: 'rgba(0,0,0,0.4)',
  },

  modalBox: {
    backgroundColor: COLORS.CARD,
    borderRadius: 20,
    padding: 25,
    marginHorizontal: 30,
    elevation: 5,
  },

  modalTitle: {
    fontSize: FONT_SIZES.XLARGE,
    fontWeight: '700',
    marginBottom: SPACING.MEDIUM,
    color: COLORS.TEXT_DARK,
    textAlign: 'center',
  },

  modalText: {
    fontSize: FONT_SIZES.MEDIUM,
    color: COLORS.TEXT_MEDIUM,
    textAlign: 'center',
    marginBottom: SPACING.LARGE,
  },

  modalButtonGroup: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },

  modalButton: {
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
  },

  modalButtonText: {
    color: COLORS.TEXT_WHITE,
    fontWeight: '600',
    textAlign: 'center',
  },
});

// Common success modal styles
export const SuccessModalStyles = StyleSheet.create({
  centeredView: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0,0,0,0.5)',
  },

  successModalView: {
    margin: 20,
    backgroundColor: COLORS.CARD,
    borderRadius: 20,
    padding: 35,
    alignItems: 'center',
    shadowColor: COLORS.TEXT_DARK,
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
    width: '80%',
    maxWidth: 400,
    alignSelf: 'center',
  },

  successIconContainer: {
    marginBottom: 20,
  },

  successModalTitle: {
    fontSize: FONT_SIZES.XLARGE,
    fontWeight: 'bold',
    color: COLORS.TEXT_DARK,
    marginBottom: SPACING.MEDIUM,
  },

  successModalText: {
    fontSize: FONT_SIZES.MEDIUM,
    color: COLORS.TEXT_LIGHT,
    textAlign: 'center',
    marginBottom: SPACING.LARGE,
  },

  successModalButton: {
    backgroundColor: COLORS.PRIMARY,
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 30,
    elevation: 2,
  },

  successModalButtonText: {
    color: COLORS.TEXT_WHITE,
    fontWeight: 'bold',
    textAlign: 'center',
    fontSize: FONT_SIZES.MEDIUM,
  },
});

export default GlobalStyles;