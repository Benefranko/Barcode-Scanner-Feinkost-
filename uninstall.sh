#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi



# De-Autostart:
echo "Entferne Autostart..."

rm "/home/${USER}/.config/autostart/feinkostbarcodescanner.desktop"
if [ $? -eq 0 ]; then
  echo "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi


echo "Entferne Programmdateien..."
rm -r "/home/${USER}/Barcode-Scanner-Feinkost-/"
if [ $? -eq 0 ]; then
  echo "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi

echo "Entferne die Abhängigkeiten..."

echo "Entferne Driver..."
sudo apt remove tdsodbc freetds-dev freetds-bin unixodbc-dev
if [ $? -eq 0 ]; then
  echo "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi

echo "Entferne Driver File..."
# Save driver Location for Driver Loader
sudo rm "/etc/odbcinst.ini"
if [ $? -eq 0 ]; then
  echo "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi


echo "Entferne Driver Loader..."
# 2. Driver Loader, 3. Graphics, 4. Python-modules:
sudo apt remove python3-pyodbc
if [ $? -eq 0 ]; then
  echo "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi


echo "Entferne Qt-Bibliotheken"
sudo apt remove python3-PySide2.*
if [ $? -eq 0 ]; then
  echo "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi


echo "Entferne Enum Bibliothek"
sudo apt remove python-enum34
if [ $? -eq 0 ]; then
    echo "    -> OK\n"
else
    echo "    -> FAILED --> EXIT()"
    exit
fi


echo "Deaktiviere Feature Herunterfahren und Neustarten über Webserver..."
sed -i 'user_name ALL=(ALL) NOPASSWD: /sbin/reboot, /sbin/shutdown' "/etc/sudoers"

if [ $? -eq 0 ]; then
  echo "    -> OK\n"
else
  echo "    -> FAILED --> EXIT()"
  exit
fi


echo "\nFINISHED SUCCESSFULLY"

