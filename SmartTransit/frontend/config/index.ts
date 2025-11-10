import { Platform } from "react-native";
import { NativeModules } from "react-native";

// Replace this with your actual IP address
const LOCAL_IP = "192.168.1.103"; // your laptop IP

const isEmulator = () => {
  const { PlatformConstants } = NativeModules;
  return PlatformConstants && PlatformConstants.Fingerprint
    ? PlatformConstants.Fingerprint.includes("generic")
    : false;
};

// I commented this out because this thing doesn't work on my laptop (by Alex)
// const baseUrl =
//   process.env.REACT_APP_API_URL ||
//   (Platform.OS === "android"
//     ? isEmulator()
//       ? "http://10.0.2.2:8000"
//       : `http://${LOCAL_IP}:8000`
//     : "http://localhost:8000");

const baseUrl =
  process.env.REACT_APP_API_URL ||
  (Platform.OS === "android"
    ? "http://10.0.2.2:8000"
    : "http://192.168.1.106:8000");


const config = {
  apiUrl: baseUrl,
  socketUrl: baseUrl.replace(/^http/, "ws"),
  publishable_key: "pk_test_51R9ob0PnudBET2TRvQR8HYPPlG42nDukwwzRB7bJyuAlJFXOnZMUwDPeAEBSfOJzQ4i0gPi028MqVfk4ZEoh9Jpt009SPoeTSU", // This key is okay to be publicly disclosed
  show_admin_id: 1
};

export default config;