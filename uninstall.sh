#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi


# De-Autostart:
echo "Entferne Autostart..."

if rm "/home/${SUDO_USER}/.config/autostart/FeinkostBarcodeScanner.desktop"; then
  echo -e "    -> OK\n"
else
  echo "    -> FAILED"
fi


echo "Entferne Programmdateien..."

if rm -r "/home/${SUDO_USER}/Barcode-Scanner-Feinkost-/"; then
  echo -e "    -> OK\n"
else
  echo "    -> WARNING: FAILED"
fi

echo "Entferne die Abhängigkeiten..."

echo "Entferne Driver..."
if sudo apt remove tdsodbc freetds-dev freetds-bin unixodbc-dev; then
  echo -e "    -> OK\n"
else
  echo "    -> FAILED --> SKIPPING()"
fi

echo "Entferne Driver File..."
# Save driver Location for Driver Loader

if sudo rm "/etc/odbcinst.ini"; then
  echo -e "    -> OK\n"
else
  echo "    -> FAILED"
fi


echo "Entferne Driver Loader..."
# 2. Driver Loader, 3. Graphics, 4. Python-modules:

if sudo apt remove python3-pyodbc; then
  echo -e "    -> OK\n"
else
  echo "    -> FAILED --> SKIPPING()"
fi


echo "Entferne Qt-Bibliotheken"
if sudo apt remove python3-PySide2.*; then
  echo -e "    -> OK\n"
else
  echo "    -> FAILED --> SKIPPING()"
fi


echo "Entferne Enum Bibliothek"
if sudo apt remove python-enum34; then
    echo -e "    -> OK\n"
else
    echo "    -> FAILED --> SKIPPING()"
fi

echo "Deaktiviere Feature Herunterfahren und Neustarten über Webserver..."

if sudo sed -i.bak "/${SUDO_USER} ALL=(ALL) NOPASSWD: /sbin/reboot, /sbin/shutdown/d" "/etc/sudoers"; then
  echo -e "    -> OK\n"
else
  echo "    -> FAILED -> restore..."

fi

echo -e "\nFINISHED"

