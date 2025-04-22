# 🛒 Feinkost Barcode Scanner

![GitHub License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-red.svg)

> A sophisticated barcode scanning solution for retail customers to access detailed product information from the JTL Wawi inventory management system.

<div align="center">
    <img src="https://github.com/Benefranko/Barcode-Scanner-Feinkost-/blob/main/doc/Screenshots/screenshot-startpage.PNG" width="300" alt="Start Page">
    <img src="https://github.com/Benefranko/Barcode-Scanner-Feinkost-/blob/main/doc/Screenshots/screenshot-test-article.PNG" width="300" alt="Article View">
    <img src="https://github.com/Benefranko/Barcode-Scanner-Feinkost-/blob/main/doc/Screenshots/screenshot-test-advertice.PNG" width="300" alt="Advertisement View">
</div>

## 📋 Table of Contents

- [Features](#-features)
- [System Requirements](#-system-requirements)
- [Installation](#-installation)
  - [Quick Installation](#quick-installation)
  - [Manual Installation](#manual-installation)
- [Configuration](#-configuration)
- [Dependencies](#-dependencies)
- [Updating](#-updating)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

## ✨ Features

- **Instant Product Information**: Scan barcodes to retrieve detailed product data
- **JTL Wawi Integration**: Direct connection to your existing inventory system
- **User-Friendly Interface**: Clean, intuitive UI for customer self-service
- **Raspberry Pi Optimized**: Designed to run smoothly on Raspberry Pi devices
- **Remote Management**: Shutdown and restart capabilities via web interface

## 💻 System Requirements

- Raspberry Pi (tested on Raspberry Pi 4)
- Raspbian/Raspberry Pi OS
- Python 3.7 (recommended)
- Barcode scanner (USB connection)
- Internet connectivity to JTL Wawi database

## 🚀 Installation

### Quick Installation

We provide an automated installer script for easy setup:

```bash
wget -O /tmp/fkbc_install.sh https://raw.githubusercontent.com/M4RKUS28/FeinkostBarcodeScannerInstaller/main/install.sh
sudo chmod +x /tmp/fkbc_install.sh
sudo /tmp/fkbc_install.sh
```

To uninstall:

```bash
wget -O /tmp/fkbc_uninstall.sh https://raw.githubusercontent.com/M4RKUS28/FeinkostBarcodeScannerInstaller/main/uninstall.sh
sudo chmod +x /tmp/fkbc_uninstall.sh
sudo /tmp/fkbc_uninstall.sh
```

### Manual Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Benefranko/Barcode-Scanner-Feinkost-.git
   cd Barcode-Scanner-Feinkost-
   ```

2. **Install dependencies**:
   ```bash
   # Install MS SQL Driver
   sudo apt install tdsodbc freetds-dev freetds-bin unixodbc-dev
   
   # Install Python dependencies
   sudo apt install python3-pyodbc python3-PySide2.*
   ```

3. **Configure the ODBC driver**:
   ```bash
   sudo tee -a "/etc/odbcinst.ini" << EOF
   [FreeTDS]
   Description=FreeTDS Driver
   Driver=/usr/lib/arm-linux-gnueabihf/odbc/libtdsodbc.so
   Setup=/usr/lib/arm-linux-gnueabihf/odbc/libtdsS.so
   EOF
   ```

4. **Setup autostart**:
   ```bash
   mkdir -p /home/pi/.config/autostart
   tee /home/pi/.config/autostart/feinkostbarcodescanner.desktop << EOF
   [Desktop Entry]
   Name=FeinkostBarcodeScanner
   Type=Application
   Exec=/usr/bin/python /home/pi/FeinkostBarcodeScanner/src/main.py
   Terminal=false
   EOF
   ```

5. **Enable shutdown and restart via web interface**:
   ```bash
   sudo visudo
   ```
   Add the following line (replace `pi` with your username if different):
   ```
   pi ALL=(ALL) NOPASSWD: /sbin/reboot, /sbin/shutdown
   ```

## ⚙️ Configuration

1. Rename the template configuration file:
   ```bash
   cp src/constants.py-template.txt src/constants.py
   ```

2. Edit the configuration file to set your preferences:
   ```bash
   nano src/constants.py
   ```

**Important**: The `constants.py` file is ignored during updates. When performing a major update (first version number change), you must manually download the new template file and transfer your settings.

## 📦 Dependencies

The application requires the following components:

| Component | Purpose | Package Name |
|-----------|---------|--------------|
| FreeTDS | MS SQL Driver | `tdsodbc`, `freetds-dev`, `freetds-bin` |
| UnixODBC | ODBC Driver Manager | `unixodbc-dev` |
| PyODBC | Python ODBC Interface | `python3-pyodbc` |
| PySide2 | GUI Framework | `python3-PySide2.*` |

## 🔄 Updating

To update the application:

1. Back up your `constants.py` file
2. Pull the latest changes from the repository
3. Check if `constants.py-template.txt` has been updated
4. If needed, merge your settings with the new template

## ❓ Troubleshooting

### Common Issues

- **Database Connection Errors**: Verify your ODBC configuration and database credentials
- **Driver Not Found**: Check that FreeTDS is properly installed and configured
- **UI Not Loading**: Ensure PySide2 packages are correctly installed

For more detailed information, check the application logs.

## 📄 License

This project is released under the MIT License. See the LICENSE file for details.

---

<div align="center">
    <strong>Developed for Innkaufhaus | © 2025</strong>
</div>
