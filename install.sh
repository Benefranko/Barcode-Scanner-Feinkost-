#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

echo "Benutzer: $SUDO_USER"
echo " -> $SUDO_USER sollte kein Admin sein! ( Ausführen dieses Skripts mit sudo )"

echo "Wechsle das Verzeichnis zu: '/home/${SUDO_USER}/'..."
cd "/home/${SUDO_USER}/"

if [ -d "/home/${USER}/Barcode-Scanner-Feinkost-" ]; then
  echo "Es existiert bereits der Ordner '/home/${SUDO_USER}/Barcode-Scanner-Feinkost-' -> Bereits installiert? \n->Abbruch"
  exit
fi

if [ -d "/home/${USER}/Barcode-Scanner-Feinkost-" ]; then
  echo "Es existiert bereits der Ordner '/home/${USER}/Barcode-Scanner-Feinkost-' -> Bereits installiert? \n->Abbruch"
  exit
fi

echo "Lade das Projekt herunter..."
git clone "https://github.com/Benefranko/Barcode-Scanner-Feinkost-.git"
if [ $? -eq 0 ]; then
  echo "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi



echo "Kopiere die Constants-Datei..."
cp "/home/${USER}/Barcode-Scanner-Feinkost-/src/constants.py-template.txt" "/home/${USER}/Barcode-Scanner-Feinkost-/src/constants.py"

echo "Öffne die Starteinstellungsdatei für Änderungen..."
echo "3"
sleep 1
echo "2"
sleep 1
echo "1"
sleep 1
nano "/home/${USER}/Barcode-Scanner-Feinkost-/src/constants.py"

echo "Installiere die Abhängigkeiten..."

# Abhängigkeiten Installation:
echo "Installiere Python3..."
sudo apt install python3
if [ $? -eq 0 ]; then
  echo "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi


echo "Installiere Driver..."
sudo apt install tdsodbc freetds-dev freetds-bin unixodbc-dev
if [ $? -eq 0 ]; then
  echo "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi


echo "Erstelle Driver File..."
# Save driver Location for Driver Loader
sudo tee "/etc/odbcinst.ini" "[FreeTDS]
Description=FreeTDS Driver
Driver=/usr/lib/arm-linux-gnueabihf/odbc/libtdsodbc.so
Setup=/usr/lib/arm-linux-gnueabihf/odbc/libtdsS.so"
if [ $? -eq 0 ]; then
  echo "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi


echo "Installiere Driver Loader..."
# 2. Driver Loader, 3. Graphics, 4. Python-modules:
sudo apt install python3-pyodbc
if [ $? -eq 0 ]; then
  echo "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi


echo "Installiere Qt-Bibliotheken"
sudo apt install python3-PySide2.*
if [ $? -eq 0 ]; then
  echo "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi


echo "Installiere Enum Bibliothek"
sudo apt install python-enum34
if [ $? -eq 0 ]; then
    echo "    -> OK\n"
else
    echo "    -> FAILED --> EXIT()"
    exit
fi


echo "Aktiviere Feature Herunterfahren und Neustarten über Webserver..."
# Aktiviere Herunterfahren & Neustarten über Web
if [ -z "$(cat "/etc/sudoers" | grep "user_name ALL=(ALL) NOPASSWD: /sbin/reboot, /sbin/shutdown")" ]; then
    sudo echo "user_name ALL=(ALL) NOPASSWD: /sbin/reboot, /sbin/shutdown" >> "/etc/sudoers"
fi
if [ $? -eq 0 ]; then
  echo "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi


# Autostart:
echo "Aktiviere Autostart..."

tee /home/${USER}/.config/autostart/feinkostbarcodescanner.desktop"
[Desktop Entry]
Name=FeinkostBarcodeScanner
Type=Application
Exec=/usr/bin/python /home/${USER}/FeinkostBarcodeScanner/src/main.py
Terminal=false"
echo "    -> OK\n"

echo "\nFINISHED SUCCESSFULLY"