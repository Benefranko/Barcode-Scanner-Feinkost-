# Barcode-Scanner-Feinkost-

Mit diesem Programm sollen Kunden durch das Scannen eines Produkt Bar Codes zusätzliche Informationen zu diesem bekommen.


# Autostart mit Cronjobs:
``sudo apt install cron``
Und mit ``crontab -e`` folgendes hinzufügen:

````
@reboot python3.7 /path/to/the/project/main.py
````
# Autostart mit Systemd:

Erstellen sie die Datei ``/etc/systemd/system/feinkostBarcodeScanner.service``
mit folgendem Inhalt:
````
[Unit]
Description=Feinkost Barcode Scanner
After=network.target

[Service]
Type=oneshot
ExecStart=/full/path/to/the/project/main.py
User=pi

[Install]
WantedBy=multi-user.target

````

und aktivieren sie den Dienst mit: \
``sudo systemctl daemon-reload`` \
``sudo systemctl enable feinkostBarcodeScanner``

Der User (pi) sollte dabei keine Adminrechte haben!

# Installlation kurz:
````
#Driver
sudo apt install tdsodbc freetds-dev freetds-bin unixodbc-dev

# Save driver Location for Driver Loader
sudo tee -a "/etc/odbcinst.ini" "[FreeTDS]
Description=FreeTDS Driver
Driver=/usr/lib/arm-linux-gnueabihf/odbc/libtdsodbc.so
Setup=/usr/lib/arm-linux-gnueabihf/odbc/libtdsS.so"

#Driver Loader & Graphics
sudo apt install python3-pyodbc python3-PySide2.* python-enum34
````


# Dependencies
Da es viele Pakete nur in älteren Version gibt, wird Python 3.7 empfohlen

### Installation:
````
````

## MS SQL Open Source Driver:

``sudo apt install freetds-dev freetds-bin unixodbc-dev tdsodbc``

Getestet mit: \
tdsodbc/oldstable,now 1.00.104-1+deb10u1 armhf \
ODBC driver for connecting to MS SQL and Sybase SQL servers 

### Einrichten des Drivers nach der Installation:
[Connect to MSSQL using FreeTDS / ODBC in Python. - Github](https://gist.github.com/rduplain/1293636#file-readme-md) \
[What's causing 'unable to connect to data source' for pyodbc? - Stackoverflow](https://stackoverflow.com/questions/9723656/whats-causing-unable-to-connect-to-data-source-for-pyodbc)

Mit `` sudo nano /etc/odbcinst.ini`` folgenden Text einfügen:

einfügen und ggf. Pfade ändern (manchmal auch unter /usr/lib/odbc/):
````
[FreeTDS]
Description=FreeTDS Driver
Driver=/usr/lib/arm-linux-gnueabihf/odbc/libtdsodbc.so
Setup=/usr/lib/arm-linux-gnueabihf/odbc/libtdsS.so
````

Dadurch kann pyodbc den Driver finden. Weitere Informationen unter \
[FreeTDS.support.Microsoft](https://www.freetds.org/faq.html#Does.FreeTDS.support.Microsoft.servers) \
bzw. Informationen zur Protokollversion unter \
[ChoosingTdsProtocol](https://www.freetds.org/userguide/ChoosingTdsProtocol.html)


## Oder Driver offiziell von Mircosoft
( Kein Support für ArmV8-Architektur! )

[Microsoft Download Seite zu odbc-driver-for-sql](https://docs.microsoft.com/de-de/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver16)

## Zum Laden des Datenbank Drivers:

``sudo apt install python3-pyodbc``

Getestet mit: \
python3-pyodbc/oldstable,now 4.0.22-1+b1 armhf \
Python3 module for ODBC database access 


## Für die Grafik: PyQt bzw. hier Pyside2 Bibliotheken:

``sudo apt install python3-PySide2.*``

## Weitere Python Module:
``sudo apt install python-enum34``



