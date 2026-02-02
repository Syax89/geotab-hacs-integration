# Geotab Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

The Geotab integration for Home Assistant allows you to monitor your Geotab vehicles and devices directly from your Home Assistant instance.

This integration connects to the MyGeotab API to retrieve real-time information about your vehicles, providing entities for location tracking and various vehicle sensors.

## Features

*   **Real-time Location Tracking**: Adds a `device_tracker` entity for each vehicle, allowing you to see its position on the Home Assistant map.
*   **Speed Sensor**: Displays the current speed of each vehicle.
*   **Odometer Sensor**: Displays the total distance traveled by the vehicle.
*   **Easy Configuration**: The integration is easily configured via the Home Assistant user interface.

## Installation

### Method 1: HACS (Recommended)

Currently, this integration is not in the default HACS store. You can add it as a custom repository:

1.  Open HACS and go to `Integrations`.
2.  Click on the three dots in the top right corner and select `Custom repositories`.
3.  Paste the URL of this GitHub repository into the `Repository` field.
4.  Select the `Integration` category and click `Add`.
5.  Search for "Geotab" in the list of integrations and click `Install`.
6.  Restart Home Assistant.

### Method 2: Manual Installation

1.  Download the latest `release` from the repository.
2.  Extract the content and copy the `custom_components/geotab` folder into your Home Assistant's `custom_components` folder. The final path should be `<config>/custom_components/geotab`.
3.  Restart Home Assistant.

## Configuration

Once the integration is installed, you can add it to your Home Assistant configuration:

1.  Go to `Settings` > `Devices & Services`.
2.  Click on `Add Integration` and search for `Geotab`.
3.  Enter your MyGeotab credentials:
    *   **Username (Email)**
    *   **Password**
    *   **Database/Server Name** (usually `my.geotab.com`)
4.  Click `Submit`.

The integration will automatically create a device for each vehicle found in your Geotab account, along with its associated entities.

## Contributions

Contributions are welcome! If you want to improve the integration, please open an issue to discuss your idea or create a pull request.

## License

This project is released under the Apache 2.0 License. See the `LICENSE` file for more details.