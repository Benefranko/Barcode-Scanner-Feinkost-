#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi


#echo "Deaktiviere Feature Herunterfahren und Neustarten über Webserver..."

#if text="$(sudo cat "/etc/sudoers" | grep -v "${SUDO_USER} ALL=(ALL) NOPASSWD: /sbin/reboot, /sbin/shutdown" )"; then

#  [ -e "/etc/sudoers.bak" ] && sudo rm "/etc/sudoers.bak" && echo "Lösche altes Backup"
#  if sudo mv "/etc/sudoers" "/etc/sudoers.bak"; then
#      if echo "$text" | sudo tee "/etc/sudoers"; then
#        echo -e "    -> OK\n"
#      else
#            echo "    -> FAILED to write new file -> restore..."
#            [ -e "/etc/sudoers" ] && sudo rm "/etc/sudoers"
#            sudo mv "/etc/sudoers.bak" "/etc/sudoers"
#      fi
#  else
#    echo "    -> FAILED to create backup -> restore..."
#    [ -e "/etc/sudoers" ] && sudo rm "/etc/sudoers"
#    sudo mv "/etc/sudoers.bak" "/etc/sudoers"
#  fi#

#else
#  echo "    -> FAILED grep failed skipp"
#fi

exit


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

if text=$(sudo grep -v "${SUDO_USER}\ ALL=(ALL)\ NOPASSWD:\ /sbin/reboot,\ /sbin/shutdown" "/etc/sudoers"); then
  print "$text"
  sleep 10
  [ -e "/etc/sudoers.bak" ] && sudo rm "/etc/sudoers.bak" && echo "Lösche altes Backup"
  if mv "/etc/sudoers" "/etc/sudoers.bak"; then
      if echo "$text" | sudo tee "/etc/sudoers"; then
        echo -e "    -> OK\n"
      else
            echo "    -> FAILED to write new file -> restore..."
            [ -e "/etc/sudoers" ] && sudo rm "/etc/sudoers"
            mv "/etc/sudoers.bak" "/etc/sudoers"
      fi
  else
    echo "    -> FAILED to create backup -> restore..."
    [ -e "/etc/sudoers" ] && sudo rm "/etc/sudoers"
    mv "/etc/sudoers.bak" "/etc/sudoers"
  fi

else
  echo "    -> FAILED grep failed skipp"
fi

echo -e "\nFINISHED"

