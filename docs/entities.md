# Entity Guide 📊

This integration creates a set of entities for each vehicle found in your Geotab account.

## Device Tracker

- **Location**: Real-time GPS coordinates displayed on the map. Includes speed and driving status as attributes.

## Main Sensors

- **Speed**: Current speed in km/h.
- **Odometer**: Total distance traveled in km (meters converted for readability).
- **Fuel Level**: Battery or fuel tank percentage.
- **Last Trip Distance**: Distance in km of the most recent completed journey (filters out zero-distance records).
- **Engine Hours**: Total accumulated engine runtime in hours.

## Binary Sensors

- **Driving**: Active when the vehicle is in motion.
- **Ignition**: Active when the engine is running (derived from real-time DeviceStatusInfo).
- **Active Faults**: Problem state when diagnostic codes are detected. Provides detailed attributes:
  - `fault_count`: Number of active faults
  - `faults_list`: Human-readable list (e.g., "[130] Dispositivo riavviato - alimentazione rimossa")
  - `faults_details`: Structured data including:
    - `code`: Fault code number
    - `diagnostic_id`: Full diagnostic ID
    - `name`: Human-readable fault name
    - `description`: Detailed description when available
    - `timestamp`: When the fault occurred
    - `state`: Fault state (Active, Pending, etc.)
    - `lamp_status`: Severity indicators (Amber Warning, Red Stop, etc.)

## Diagnostic Entities (Hidden by default)

- **Battery Voltage**: Real-time voltage.
- **Tire Pressure (FL, FR, RL, RR)**: Individual tire pressure in PSI.
- **Engine Hours**: Total accumulated engine runtime.
- **Engine Speed (RPM)**: Rotational speed of the engine (0 when ignition off).
- **Accelerator Position**: Pedal position percentage.
- **Coolant Temperature**: Engine coolant temp in Celsius.
- **Last Update**: Timestamp of the last successful data poll.
