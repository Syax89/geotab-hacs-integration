# Geotab Integration for Home Assistant (unofficial)

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
![GitHub Release](https://img.shields.io/github/v/release/Syax89/geotab-hacs-integration?style=for-the-badge)
![License](https://img.shields.io/github/license/Syax89/geotab-hacs-integration?style=for-the-badge)

Monitor your Geotab vehicles and devices directly from Home Assistant. This integration connects to the MyGeotab API to retrieve real-time location and comprehensive diagnostic data.

---

## ✨ Features

*   **🛰️ Real-time Location Tracking**: Dedicated `device_tracker` entity for every vehicle.
*   **📊 Comprehensive Sensors**: 
    *   **Driving Dynamics**: Speed (km/h) and Odometer (km).
    *   **Battery & Fuel**: Real-time voltage and fuel level percentage.
    *   **Tires**: Individual pressure monitoring for all four tires (PSI).
    *   **Diagnostics**: Engine Speed (RPM), Coolant Temp, Engine Hours, and Accelerator Position.
*   **🚨 Binary Sensors**:
    *   **Driving Status**: Instant feedback on vehicle movement.
    *   **Active Faults**: Detects diagnostic trouble codes (DTCs) and issues.
    *   **Safety & Status**: Door Ajar and Seatbelt status (disabled by default).
*   **🛡️ Security & Privacy**:
    *   **Data Masking**: Account emails are hidden from public UI views.
    *   **Resilience**: Graceful error handling and automated recovery (UpdateFailed support).
    *   **API Protection**: Built-in rate limit protection (min 30s interval).
*   **🌍 Multi-language**: Full support for **English** and **Italian**.

## 🚀 Installation

### Method 1: HACS (Recommended)

This integration is available as a **Custom Repository**:

1.  Open **HACS** > `Integrations`.
2.  Click the three dots (top right) > `Custom repositories`.
3.  Paste the URL: `https://github.com/Syax89/geotab-hacs-integration`
4.  Select Category: `Integration` and click `Add`.
5.  Search for "Geotab" and click `Install`.
6.  **Restart Home Assistant**.

### Method 2: Manual

1.  Download the [latest release](https://github.com/Syax89/geotab-hacs-integration/releases).
2.  Copy the `custom_components/geotab` folder into your HA `<config>/custom_components/` directory.
3.  **Restart Home Assistant**.

## ⚙️ Configuration

1.  Go to `Settings` > `Devices & Services`.
2.  Click `Add Integration` > Search for **Geotab**.
3.  Enter your credentials:
    *   **Username**: Your MyGeotab email.
    *   **Password**: Your MyGeotab password.
    *   **Database**: Your Geotab database name (e.g., `my.geotab.com/your_db`).
    *   **Scan Interval**: Update frequency (minimum 30 seconds).

> [!TIP]
> You can update the **Scan Interval** anytime by clicking the **Configure** (gear icon) button on the integration card.

## 🤝 Contributions

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## ⚖️ License

Released under the **Apache 2.0 License**. See [LICENSE](LICENSE) for details.

---
*Disclaimer: This is an unofficial integration and is not affiliated with or endorsed by Geotab Inc.*
