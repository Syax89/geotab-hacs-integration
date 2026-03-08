# Geotab Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
![GitHub Release](https://img.shields.io/github/v/release/Syax89/geotab-hacs-integration?style=for-the-badge)
![License](https://img.shields.io/github/license/Syax89/geotab-hacs-integration?style=for-the-badge)

A professional-grade Home Assistant integration for the Geotab fleet management platform. This component facilitates the seamless synchronization of telematics data, providing comprehensive vehicle monitoring, diagnostic analysis, and real-time tracking directly within the Home Assistant ecosystem.

---

## 🛠 Key Capabilities

* **High-Precision Tracking**: Dedicated `device_tracker` entities providing real-time geographical coordinates for all fleet assets.
* **Diagnostic Trouble Codes (DTC)**: Advanced monitoring of active engine faults with detailed reporting on fault codes, human-readable descriptions, and severity indicators (lamp status).
* **Extended Telematics**: Access to over 30 distinct data points per vehicle, including fuel metrics, tire pressures, and engine health parameters.
* **Historical Aggregation**: Built-in calculation of daily, weekly, and monthly trip statistics, including distance covered and idle time analysis.
* **Internationalization**: Full localization support for English, Italian, German, Spanish, French, Dutch, and Portuguese.

---

## 📊 Data Points & Sensor Organization

Entities are logically categorized to ensure a streamlined user interface and efficient data management:

### Primary Status
* **Odometer**: Total cumulative distance.
* **Fuel Level**: Real-time percentage of remaining fuel.

### Performance & Driving
* **Real-time Velocity**: Current speed in km/h.
* **Fuel Rate**: Instantaneous fuel consumption (L/h).

### Engine Health & Diagnostics
* **Powertrain Metrics**: Engine Speed (RPM), Engine Load, and total Engine Hours.
* **Thermal Management**: Coolant, Oil, and Transmission fluid temperatures.
* **Electrical System**: Real-time battery voltage monitoring.

### Chassis & Environment
* **Tire Pressure Monitoring (TPMS)**: Individual pressure readings for all four wheels (PSI).
* **Environmental Data**: Ambient air temperature.
* **Control Surfaces**: Accelerator and throttle position percentages.

### Trip Statistics
* **Aggregated Metrics**: Daily, weekly, and monthly distance tracking.
* **Operational Analysis**: Trip counts and weekly idle time reports.
* **Last Journey**: Comprehensive data on the most recently completed trip.

---

## 🚀 Installation & Deployment

### Recommended: HACS Deployment

1. Navigate to **HACS** > **Integrations**.
2. Select the overflow menu (three dots) and choose **Custom repositories**.
3. Input the following URL: `https://github.com/Syax89/geotab-hacs-integration`
4. Set the category to **Integration** and click **Add**.
5. Search for **Geotab**, select **Install**, and subsequently **Restart Home Assistant**.

### Manual Deployment

1. Obtain the latest release archive from the [Releases page](https://github.com/Syax89/geotab-hacs-integration/releases).
2. Extract the `custom_components/geotab` directory into your Home Assistant `/config/custom_components/` path.
3. **Restart Home Assistant**.

---

## ⚙️ Configuration

1. Access **Settings** > **Devices & Services**.
2. Select **Add Integration** and search for **Geotab**.
3. Provide the required authentication and connectivity parameters:
   * **Username**: Authorized MyGeotab account email.
   * **Password**: Associated account password.
   * **Database**: Target Geotab database identifier (e.g., `my.geotab.com/database_id`).
   * **Scan Interval**: Frequency of API polling (Minimum: 30 seconds).

*Note: Integration parameters can be modified post-installation via the **Configure** interface.*

---

## 🛡️ Technical Integrity & Security

* **API Optimization**: Utilizes an asynchronous architecture to minimize blocking calls and optimize performance during high-volume data retrieval.
* **Resilience**: Features a robust circuit breaker mechanism and automated error recovery to handle API outages or connectivity fluctuations gracefully.
* **Privacy**: Implements data masking protocols for sensitive account information within the public-facing user interface.

---

## 📖 Further Documentation

For comprehensive technical specifications, automation templates, and advanced troubleshooting, please refer to the [Documentation folder](docs/).

---

## ⚖️ License & Disclaimer

Distributed under the **MIT License**. Refer to the [LICENSE](LICENSE) file for the full legal text.

*Disclaimer: This project is an independent, community-driven integration and is neither affiliated with nor endorsed by Geotab Inc.*
