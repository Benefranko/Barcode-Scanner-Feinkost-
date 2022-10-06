#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

echo "Benutzer: $SUDO_USER"
echo " -> $SUDO_USER sollte kein Admin sein! ( Ausführen dieses Skripts mit sudo )"
for ((i=5; i>0; i--)); do echo -ne "\r$i"; sleep 1; done
echo -e "\n"


if [ -d "/home/$SUDO_USER/Barcode-Scanner-Feinkost-" ]; then
  echo -e "Es existiert bereits der Ordner '/home/${SUDO_USER}/Barcode-Scanner-Feinkost-' -> Bereits installiert? \n->Abbruch"
  # exit
fi

echo "Wechsle das Verzeichnis zu: '/home/${SUDO_USER}/'..."
cd "/home/${SUDO_USER}/" || exit

echo "Lade das Projekt herunter..."
if git clone "https://github.com/Benefranko/Barcode-Scanner-Feinkost-.git"; then
    echo -e "    -> OK\n"
else
    echo "    -> FAILED --> EXIT()"
    exit
fi


echo "Kopiere die Constants-Datei (/home/${SUDO_USER}/Barcode-Scanner-Feinkost-/src/constants.py-template.txt --> /home/${SUDO_USER}/Barcode-Scanner-Feinkost-/src/constants.py)..."

if cp "/home/${SUDO_USER}/Barcode-Scanner-Feinkost-/src/constants.py-template.txt" "/home/${SUDO_USER}/Barcode-Scanner-Feinkost-/src/constants.py"; then
   echo "Öffne die Starteinstellungsdatei für Änderungen..."
   for ((i=10; i>0; i--)); do echo "$i"; sleep 1; done
   nano "/home/${SUDO_USER}/Barcode-Scanner-Feinkost-/src/constants.py"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi

echo "Installiere die Abhängigkeiten..."

# Abhängigkeiten Installation:
echo "Installiere Python3..."
if sudo apt install python3; then
  echo -e "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi


echo "Installiere Driver..."
if sudo apt install tdsodbc freetds-dev freetds-bin unixodbc-dev; then
  echo -e "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi


echo "Erstelle Driver File..."
# Save driver Location for Driver Loader

if sudo tee "/etc/odbcinst.ini" "[FreeTDS]
Description=FreeTDS Driver
Driver=/usr/lib/arm-linux-gnueabihf/odbc/libtdsodbc.so
Setup=/usr/lib/arm-linux-gnueabihf/odbc/libtdsS.so"
then
  echo -e "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi


echo "Installiere Driver Loader..."
# 2. Driver Loader, 3. Graphics, 4. Python-modules:
if sudo apt install python3-pyodbc; then
  echo -e "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi


echo "Installiere Qt-Bibliotheken"
if sudo apt install python3-PySide2.*; then
  echo -e "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi


echo "Installiere Enum Bibliothek"
if sudo apt install python-enum34; then
    echo -e "    -> OK\n"
else
    echo "    -> FAILED --> EXIT()"
    exit
fi

print "sudo cat /etc/sudoers"
sudo cat /etc/sudoers


echo "Aktiviere Feature Herunterfahren und Neustarten über Webserver..."
# Aktiviere Herunterfahren & Neustarten über Web
if [[ "$(cat "/etc/sudoers")" != *"user_name ALL=(ALL) NOPASSWD: /sbin/reboot, /sbin/shutdown"* ]]; then
  if sudo tee -a "user_name ALL=(ALL) NOPASSWD: /sbin/reboot, /sbin/shutdown" >> "/etc/sudoers"; then
    echo -e "    -> OK\n"
  else
    echo "    -> FAILED --> EXIT()"
    exit
  fi
fi


print "sudo cat /etc/sudoers"
sudo cat /etc/sudoers


# Autostart:
echo "Aktiviere Autostart..."

tee /home/${SUDO_USER}/.config/autostart/feinkostbarcodescanner.desktop"
[Desktop Entry]
Name=FeinkostBarcodeScanner
Type=Application
Exec=/usr/bin/python /home/${SUDO_USER}/FeinkostBarcodeScanner/src/main.py
Terminal=false"
echo -e "    -> OK\n"

echo -e "\nFINISHED SUCCESSFULLY"