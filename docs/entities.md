# Entity Guide 📊

This integration creates a set of entities for each vehicle found in your Geotab account.

## Device Tracker
- **Location**: Real-time GPS coordinates displayed on the map. Includes speed and driving status as attributes.

## Main Sensors
- **Speed**: Current speed in km/h.
- **Odometer**: Total distance traveled in km.
- **Fuel Level**: Battery or fuel tank percentage.
- **Last Trip Distance**: Length of the most recent completed journey.

## Binary Sensors
- **Driving**: Active when the vehicle is in motion.
- **Ignition**: Active when the engine is running.
- **Active Faults**: Problem state if diagnostic codes are detected.

## Diagnostic Entities (Hidden by default in main view)
- **Battery Voltage**: Real-time voltage.
- **Tire Pressure (FL, FR, RL, RR)**: Individual tire pressure in PSI.
- **Engine Hours**: Total accumulated engine runtime.
- **Engine Speed (RPM)**: Rotational speed of the engine.
- **Last Update**: Timestamp of the last successful data poll.
