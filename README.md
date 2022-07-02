# Barcode-Scanner-Feinkost-

Mit diesem Programm sollen Kunden durch das Scannen eines Produkt Bar Codes zusätzliche Informationen zu diesem bekommen.


# Autostart:
``sudo apt install cron``
Und mit ``crontab -e`` folgendes hinzufügen:

````
@reboot python3.7 /path/to/the/project/main.py
````

# Installlation kurz:
````
sudo wget -qO - https://raw.githubusercontent.com/tvdsluijs/sh-python-installer/main/python.sh | sudo bash -s 3.10.0

sudo apt install tdsodbc freetds-dev freetds-bin unixodbc-dev

sudo echo "[FreeTDS]
Description=FreeTDS Driver
Driver=/usr/lib/arm-linux-gnueabihf/odbc/libtdsodbc.so
Setup=/usr/lib/arm-linux-gnueabihf/odbc/libtdsS.so
TDS_Version = 7.4" >> /etc/odbcinst.ini

sudo apt install python3-pyodbc

sudo apt install *PySide2.*

sudo apt install python-enum34
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



