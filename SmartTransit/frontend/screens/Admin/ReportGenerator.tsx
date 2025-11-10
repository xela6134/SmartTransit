/**
 * Stats dashboard providing from admin which allows them to run a report to look at the success of their app
 * Admin can view profits, environmental impact and full history of rides
 */

import type React from "react"
import { useState } from "react"
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, ActivityIndicator, Alert, Platform, Dimensions } from "react-native"
import type { NativeStackNavigationProp } from "@react-navigation/native-stack"
import type { RootStackParamList } from "../../App"
import Header from "../../components/LogoHeader"
import { useAuth } from "../../context/AuthContext"
import axios from "axios"
import config from "../../config"
import DateTimePicker from "@react-native-community/datetimepicker"
import { LineChart, BarChart } from "react-native-chart-kit"

type ReportGeneratorScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, "ReportGenerator">

interface ReportGeneratorProps {
  navigation: ReportGeneratorScreenNavigationProp
}

interface RideReport {
  ride_id: number
  number_passengers: number
  passengers: number[]
  start_location: string
  end_location: string
  ride_duration: number
  profit: number
  ride_date: string
  environmental: number
}


const screenWidth = Dimensions.get("window").width - 40

const chartConfig = {
  backgroundGradientFrom: "#ffffff",
  backgroundGradientTo: "#ffffff",
  color: (opacity = 1) => `rgba(26, 35, 126, ${opacity})`,
  strokeWidth: 2,
  barPercentage: 0.5,
  useShadowColorFromDataset: false,
  decimalPlaces: 0,
  labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
  style: {
    borderRadius: 16
  },
  propsForDots: {
    r: "6",
    strokeWidth: "2",
    stroke: "#1A237E"
  }
}

const ReportGenerator: React.FC<ReportGeneratorProps> = ({ navigation }) => {
  const { accessToken } = useAuth()
  const [startDate, setStartDate] = useState<Date>(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)) // Default to 30 days ago
  const [endDate, setEndDate] = useState<Date>(new Date(Date.now() - 24 * 60 * 60 * 1000)) // default to 1 day ago
  const [showStartDatePicker, setShowStartDatePicker] = useState<boolean>(false)
  const [showEndDatePicker, setShowEndDatePicker] = useState<boolean>(false)
  const [loading, setLoading] = useState<boolean>(false)
  const [reportData, setReportData] = useState<RideReport[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<string>("profit")

  // Selecting starting date
  const onStartDateChange = (event: any, selectedDate?: Date) => {
    const currentDate = selectedDate || startDate
    setShowStartDatePicker(Platform.OS === "ios")
    setStartDate(currentDate)
  }

  // Selecting stop date
  const onEndDateChange = (event: any, selectedDate?: Date) => {
    const currentDate = selectedDate || endDate
    setShowEndDatePicker(Platform.OS === "ios")
    setEndDate(currentDate)
  }

  // Formatting dates
  const formatDate = (date: Date): string => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, "0")
    const day = String(date.getDate()).padStart(2, "0")
    return `${year}-${month}-${day}`
  }

  const formatDisplayDate = (dateString: string): string => {
    const date = new Date(dateString)
    return date.toLocaleDateString()
  }

  // Main report generation functionality
  // Handles input validation & backend calls
  const generateReport = async () => {
    if (endDate < startDate) {
      Alert.alert("Invalid Date Range", "End date must be after start date")
      return
    }

    const today = new Date()
    today.setHours(0, 0, 0, 0)

    if (startDate > today || endDate > today) {
      Alert.alert("Invalid Date Range", "Cannot generate reports for future dates")
      return
    }

    setLoading(true)
    setError(null)
    setReportData(null)

    try {
      const response = await axios.put(
        `${config.apiUrl}/report/generate`,
        {
          date_range: [formatDate(startDate), formatDate(endDate)]
        },
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
            "Content-Type": "application/json",
          }
        }
      )

      if (response.status === 200) {
        setReportData(response.data.report)
      }
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to generate report")
    } finally {
      setLoading(false)
    }
  }

  // Calculate the accumulated values to display at the top (next 5 functions)
  const calculateTotalProfit = (): number => {
    if (!reportData) return 0
    return reportData.reduce((sum, ride) => sum + ride.profit, 0)
  }

  const calculateTotalPassengers = (): number => {
    if (!reportData) return 0
    return reportData.reduce((sum, ride) => sum + ride.number_passengers, 0)
  }

  const calculateTotalEnvironmentalSavings = (): number => {
    if (!reportData) return 0
    return reportData.reduce((sum, ride) => sum + ride.environmental, 0)
  }

  const calculateAverageProfit = (): number => {
    if (!reportData || reportData.length === 0) return 0
    return calculateTotalProfit() / reportData.length
  }

  const calculateAveragePassengers = (): number => {
    if (!reportData || reportData.length === 0) return 0
    return calculateTotalPassengers() / reportData.length
  }

  // Visually generate the data to be shown in the chart
  // Parses reportData to different fields and return necessary data
  const prepareChartData = () => {
    if (!reportData || reportData.length === 0) return null

    const dateMap = new Map<string, { profit: number, passengers: number, environmental: number, count: number }>();

    reportData.forEach(ride => {
      let dateKey = '';

      const dateObj = new Date(ride.ride_date);

      dateKey = dateObj.toISOString().split('T')[0];

      if (!dateMap.has(dateKey)) {
        dateMap.set(dateKey, { profit: 0, passengers: 0, environmental: 0, count: 0 });
      }

      const current = dateMap.get(dateKey)!;
      current.profit += ride.profit;
      current.passengers += ride.number_passengers;
      current.environmental += ride.environmental;
      current.count += 1;
      dateMap.set(dateKey, current);

    });

    const sortedDates = Array.from(dateMap.keys()).sort();

    const profitData = {
      labels: sortedDates.map(date => {
        const parts = date.split('-') // "2025-04-15"
        const formatted = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]))
        return formatted.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
      }),
      datasets: [
        {
          data: sortedDates.map(date => dateMap.get(date)!.profit),
          color: (opacity = 1) => `rgba(26, 35, 126, ${opacity})`,
          strokeWidth: 2
        }
      ],
      legend: ["Profit ($)"]
    }

    const passengersData = {
      labels: sortedDates.map(date => {
        const parts = date.split('-')
        const formatted = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]))
        return formatted.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
      }),
      datasets: [
        {
          data: sortedDates.map(date => dateMap.get(date)!.passengers),
          color: (opacity = 1) => `rgba(22, 194, 192, ${opacity})`,
        }
      ],
      legend: ["Passengers"]
    }

    const environmentalData = {
      labels: sortedDates.map(date => {
        const parts = date.split('-')
        const formatted = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]))
        return formatted.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
      }),
      datasets: [
        {
          data: sortedDates.map(date => dateMap.get(date)!.environmental),
          color: (opacity = 1) => `rgba(76, 175, 80, ${opacity})`,
          strokeWidth: 2
        }
      ],
      legend: ["CO₂ Saved (kg)"]
    }

    return {
      profitData,
      passengersData,
      environmentalData
    }
  }

  const chartData = reportData ? prepareChartData() : null

  const renderTabContent = () => {
    if (!reportData || !chartData) return null

    switch (activeTab) {
      case "profit":
        return (
          <View>
            <View style={styles.chartContainer}>
              <Text style={styles.chartTitle}>Profit Trend</Text>
              <LineChart
                data={chartData.profitData}
                width={screenWidth}
                height={220}
                chartConfig={chartConfig}
                bezier
                style={styles.chart}
              />
            </View>

            <View style={styles.metricsContainer}>
              <View style={styles.metricCard}>
                <Text style={styles.metricValue}>${calculateTotalProfit().toFixed(2)}</Text>
                <Text style={styles.metricLabel}>Total Profit</Text>
              </View>
              <View style={styles.metricCard}>
                <Text style={styles.metricValue}>{reportData.length}</Text>
                <Text style={styles.metricLabel}>Total Rides</Text>
              </View>
              <View style={styles.metricCard}>
                <Text style={styles.metricValue}>{calculateTotalPassengers()}</Text>
                <Text style={styles.metricLabel}>Passengers</Text>
              </View>
            </View>
          </View>
        )

      case "passengers":
        return (
          <View>
            <View style={styles.chartContainer}>
              <Text style={styles.chartTitle}>Passenger Counts</Text>
              <BarChart
                data={chartData.passengersData}
                width={screenWidth}
                height={220}
                chartConfig={{
                  ...chartConfig,
                  color: (opacity = 1) => `rgba(22, 194, 192, ${opacity})`
                }}
                style={styles.chart}
                verticalLabelRotation={30}
                yAxisLabel=""
                yAxisSuffix=""
              />
            </View>

            <View style={styles.metricsContainer}>
              <View style={styles.metricCard}>
                <Text style={styles.metricValue}>{calculateTotalPassengers()}</Text>
                <Text style={styles.metricLabel}>Total Passengers</Text>
              </View>
              <View style={styles.metricCard}>
                <Text style={styles.metricValue}>{calculateAveragePassengers().toFixed(1)}</Text>
                <Text style={styles.metricLabel}>Avg. Per Ride</Text>
              </View>
            </View>
          </View>
        )

      case "environment":
        return (
          <View>
            <View style={styles.chartContainer}>
              <Text style={styles.chartTitle}>Environmental Impact</Text>
              <LineChart
                data={chartData.environmentalData}
                width={screenWidth}
                height={220}
                chartConfig={{
                  ...chartConfig,
                  color: (opacity = 1) => `rgba(76, 175, 80, ${opacity})`
                }}
                bezier
                style={styles.chart}
              />
            </View>

            <View style={styles.metricsContainer}>
              <View style={styles.metricCard}>
                <Text style={styles.metricValue}>{calculateTotalEnvironmentalSavings().toFixed(2)}</Text>
                <Text style={styles.metricLabel}>kg CO₂ Saved</Text>
              </View>
            </View>
          </View>
        )

      case "details":
        return (
          <View>
            <Text style={styles.detailsTitle}>Ride Details</Text>
            {reportData.map((ride, index) => (
              <View key={index} style={styles.rideCard}>
                <Text style={styles.rideId}>Ride ID: {ride.ride_id}</Text>
                <View style={styles.rideRow}>
                  <Text style={styles.rideLabel}>Date:</Text>
                  <Text style={styles.rideValue}>{formatDisplayDate(ride.ride_date)}</Text>
                </View>
                <View style={styles.rideRow}>
                  <Text style={styles.rideLabel}>From:</Text>
                  <Text style={styles.rideValue}>{ride.start_location}</Text>
                </View>
                <View style={styles.rideRow}>
                  <Text style={styles.rideLabel}>To:</Text>
                  <Text style={styles.rideValue}>{ride.end_location}</Text>
                </View>
                <View style={styles.rideRow}>
                  <Text style={styles.rideLabel}>Duration:</Text>
                  <Text style={styles.rideValue}>{ride.ride_duration} min</Text>
                </View>
                <View style={styles.rideRow}>
                  <Text style={styles.rideLabel}>Passengers:</Text>
                  <Text style={styles.rideValue}>{ride.number_passengers}</Text>
                </View>
                <View style={styles.rideRow}>
                  <Text style={styles.rideLabel}>Profit:</Text>
                  <Text style={styles.rideValue}>${ride.profit.toFixed(2)}</Text>
                </View>
                <View style={styles.rideRow}>
                  <Text style={styles.rideLabel}>Environmental Impact:</Text>
                  <Text style={styles.rideValue}>{ride.environmental.toFixed(2)} kg CO₂</Text>
                </View>
              </View>
            ))}
          </View>
        )

      default:
        return null
    }
  }

  return (
    <View style={styles.container}>
      <Header onBackPress={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.title}>Analytics Dashboard</Text>
        <Text style={styles.subtitle}>View performance metrics and trends</Text>

        <View style={styles.card}>
          <Text style={styles.label}>DATE RANGE</Text>
          <View style={styles.dateRow}>
            <TouchableOpacity
              style={[styles.dateButton, { flex: 1, marginRight: 5 }]}
              onPress={() => setShowStartDatePicker(true)}
            >
              <Text style={styles.dateButtonText}>{formatDate(startDate)}</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.dateButton, { flex: 1, marginLeft: 5 }]}
              onPress={() => setShowEndDatePicker(true)}
            >
              <Text style={styles.dateButtonText}>{formatDate(endDate)}</Text>
            </TouchableOpacity>
          </View>

          {showStartDatePicker && (
            <DateTimePicker
              value={startDate}
              mode="date"
              display={Platform.OS === "ios" ? "spinner" : "default"}
              onChange={onStartDateChange}
              maximumDate={new Date()}
            />
          )}

          {showEndDatePicker && (
            <DateTimePicker
              value={endDate}
              mode="date"
              display={Platform.OS === "ios" ? "spinner" : "default"}
              onChange={onEndDateChange}
              maximumDate={new Date()}
            />
          )}

          <TouchableOpacity style={styles.generateButton} onPress={generateReport} disabled={loading}>
            <Text style={styles.buttonText}>GENERATE ANALYTICS</Text>
          </TouchableOpacity>
        </View>

        {loading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#1A237E" />
            <Text style={styles.loadingText}>Generating analytics...</Text>
          </View>
        )}

        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {reportData && reportData.length > 0 && (
          <View style={styles.reportContainer}>
            <Text style={styles.reportTitle}>Analytics Results</Text>
            <Text style={styles.reportSubtitle}>
              {formatDate(startDate)} to {formatDate(endDate)}
            </Text>

            <View style={styles.tabContainer}>
              <TouchableOpacity
                style={[styles.tab, activeTab === "profit" && styles.activeTab]}
                onPress={() => setActiveTab("profit")}
              >
                <Text style={[styles.tabText, activeTab === "profit" && styles.activeTabText]}>Profit</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.tab, activeTab === "passengers" && styles.activeTab]}
                onPress={() => setActiveTab("passengers")}
              >
                <Text style={[styles.tabText, activeTab === "passengers" && styles.activeTabText]}>Passengers</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.tab, activeTab === "environment" && styles.activeTab]}
                onPress={() => setActiveTab("environment")}
              >
                <Text style={[styles.tabText, activeTab === "environment" && styles.activeTabText]}>Environment</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.tab, activeTab === "details" && styles.activeTab]}
                onPress={() => setActiveTab("details")}
              >
                <Text style={[styles.tabText, activeTab === "details" && styles.activeTabText]}>Details</Text>
              </TouchableOpacity>
            </View>

            {renderTabContent()}
          </View>
        )}

        {reportData && reportData.length === 0 && (
          <View style={styles.noDataContainer}>
            <Text style={styles.noDataText}>No rides found for the selected date range.</Text>
          </View>
        )}
      </ScrollView>
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f9f9f9",
    padding: 20,
  },
  scrollContent: {
    paddingBottom: 20,
  },
  title: {
    fontSize: 26,
    fontWeight: "700",
    color: "#333",
    textAlign: "center",
    marginTop: 20,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: "#777",
    textAlign: "center",
    marginBottom: 20,
  },
  card: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 20,
    marginVertical: 20,
    elevation: 4,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  label: {
    fontSize: 14,
    fontWeight: "600",
    color: "#333",
    marginBottom: 8,
  },
  dateRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 20,
  },
  dateButton: {
    backgroundColor: "#16C2C0",
    borderRadius: 12,
    padding: 15,
    alignItems: "center",
  },
  dateButtonText: {
    color: "#fff",
    fontSize: 16,
  },
  generateButton: {
    backgroundColor: "#1A237E",
    borderRadius: 12,
    paddingVertical: 15,
    alignItems: "center",
    marginTop: 10,
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 3,
  },
  buttonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  loadingContainer: {
    alignItems: "center",
    marginVertical: 20,
  },
  loadingText: {
    marginTop: 10,
    color: "#1A237E",
    fontSize: 16,
  },
  errorContainer: {
    backgroundColor: "#FFEBEE",
    padding: 10,
    borderRadius: 8,
    marginVertical: 20,
  },
  errorText: {
    color: "#D32F2F",
    textAlign: "center",
  },
  reportContainer: {
    marginTop: 20,
  },
  reportTitle: {
    fontSize: 22,
    fontWeight: "700",
    color: "#333",
    textAlign: "center",
  },
  reportSubtitle: {
    fontSize: 16,
    color: "#777",
    textAlign: "center",
    marginBottom: 20,
  },
  tabContainer: {
    flexDirection: "row",
    backgroundColor: "#fff",
    borderRadius: 12,
    marginBottom: 20,
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: "center",
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: "#1A237E",
  },
  tabText: {
    fontSize: 14,
    color: "#777",
  },
  activeTabText: {
    color: "#1A237E",
    fontWeight: "600",
  },
  chartContainer: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 15,
    marginBottom: 20,
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#333",
    marginBottom: 10,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  metricsContainer: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 20,
  },
  metricCard: {
    flex: 1,
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 15,
    marginHorizontal: 5,
    alignItems: "center",
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  metricValue: {
    fontSize: 14,
    fontWeight: "700",
    color: "#1A237E",
    marginBottom: 5,
    textAlign: "center",
  },
  metricLabel: {
    fontSize: 12,
    color: "#777",
    textAlign: "center",
  },
  detailsTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#333",
    marginBottom: 15,
  },
  rideCard: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 20,
    marginBottom: 15,
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  rideId: {
    fontSize: 16,
    fontWeight: "700",
    color: "#1A237E",
    marginBottom: 15,
    borderBottomWidth: 1,
    borderBottomColor: "#eee",
    paddingBottom: 10,
  },
  rideRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  rideLabel: {
    color: "#666",
    fontSize: 14,
  },
  rideValue: {
    fontWeight: "600",
    fontSize: 14,
    textAlign: "right",
  },
  noDataContainer: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 30,
    marginVertical: 20,
    alignItems: "center",
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  noDataText: {
    fontSize: 16,
    color: "#666",
    textAlign: "center",
  },
})

export default ReportGenerator
