import sys
import mapplication
import mainwindow
import webserver

# Für Informationsausgabe
from PySide2 import QtCore
import pyodbc
import sqlite3
import datetime
import os
import logging as log


# Einstellungen

# Programm Version
PROGRAMM_VERSION: str = "0.9.1"

SQL_DRIVER_USED_VERSION_MS_DRIVER: str = "{ODBC Driver 18 for SQL Server}"
SQL_DRIVER_USED_VERSION_FreeTDS: str = "{FreeTDS}"
SQL_DRIVER_USED_VERSION_FreeTDS_VERSION: str = "7.4"

# Pfad zu lokaler Datenbank, die zum Speichern der Statistiken der Nutzung, sowie der Bewertung dient
local_db_path: str = "./sqlLiteDB.db"
# MS SQL Server mit Daten zu Produkten
ms_sql_server_ip: str = "home.obermui.de"
# MS SQL Server Port
ms_sql_server_port: int = 18769

# Lokaler HTTP SERVER LISTEN IP
local_http_server_ip: str = "0.0.0.0"
# Lokaler HTTP SERVER LISTEN Port
local_http_server_port: int = 8888

# Pfad zu Qt-Designer Formulardatei: Die Grafik wurde nämlich mithilfe des Qt Creators erstellt.
ui_file_path: str = "../src/form_ALT.ui"

# Anzahl der Elemente auf einer Internetseite beim Webserver
item_count_on_web_server_list: int = 100

# Pfad zur Logdatei
log_file_path: str = './../Dokumentation/feinkostBarcodeScannerLog.log'


if __name__ == "__main__":
    # Change Working Directory to the one this file is in
    abspath = os.path.abspath(__file__)
    d_name = os.path.dirname(abspath)
    os.chdir(d_name)

    # Setup Logfile Path
    log.basicConfig(filename=log_file_path, level=log.DEBUG,
                    format='%(asctime)s: %(levelname)s: %(message)s', datefmt='%d-%b-%y %H:%M:%S')

    # Wenn --help aufgerufen wird, gib kurze Information aus
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            log.debug(sys.argv)
            print("Mit diesem Programm sollen Kunden durch das Scannen eines Produkt Bar Codes zusätzliche "
                  "Informationen zu diesem über die JTL-Wawi MS SQL Datenbank bekommen.")
            print("Mit '", sys.argv[0], " -platform offscreen' können sie das Programm ohne Fenster starten")
            exit()

    # Log....
    log.debug("\n\n------------------------------------------------------------------\n")
    log.debug("Programm Start: {0}".format(datetime.datetime.now()))
    log.debug("Programm Version: {0}".format(PROGRAMM_VERSION))
    log.debug("Python Version: {0}".format(sys.version))
    log.debug("Qt Version: {0}".format(QtCore.qVersion()))
    log.debug("PyODBC Version: {0}".format(pyodbc.version))
    log.debug("SQL Lite3 Version: {0}".format(sqlite3.version))
    log.debug("Unterstützte MS ODBC Driver Version: {0}".format(SQL_DRIVER_USED_VERSION_MS_DRIVER))
    log.debug("Unterstützte FreeTDS Driver Version: {0} {1}".format(SQL_DRIVER_USED_VERSION_FreeTDS,
              SQL_DRIVER_USED_VERSION_FreeTDS_VERSION))
    log.debug("Arbeitsverzeichnis: {0}".format(os.path.abspath("./")))

    # Infoausgabe
    print("------------------------------------------------------------------")
    print("Programm Start: ", datetime.datetime.now())
    print("Programm Version: ", PROGRAMM_VERSION)
    print("Python Version: ", sys.version)
    print("Qt Version: ", QtCore.qVersion())
    print("PyODBC Version: ", pyodbc.version)
    print("SQL Lite3 Version: ", sqlite3.version)
    print("Unterstützte MS ODBC Driver Version: ", SQL_DRIVER_USED_VERSION_MS_DRIVER)
    print("Unterstützte FreeTDS Driver Version: ", SQL_DRIVER_USED_VERSION_FreeTDS, " ",
          SQL_DRIVER_USED_VERSION_FreeTDS_VERSION)
    print("Arbeitsverzeichnis: ", os.path.abspath("./"))
    print("------------------------------------------------------------------")

    # MApplication
    m_app = None
    # Lokalen Statistiken Server
    w_server = None
    # Rückgabewert QApplication
    ret = None

    try:
        # Starte Lokalen Statistiken Server
        w_server = webserver.Server(local_http_server_ip, local_http_server_port)
        w_server.start_listen()

        # Erstelle Key Press Event Handler und Ui - MainWindow
        m_app = mapplication.MApplication(sys.argv)
        m_win = mainwindow.MainWindow(local_db_path, ms_sql_server_ip, ms_sql_server_port, ui_file_path)

        # connect MApplication ( EventFilter ) with MainWindow( handle_EVENT )
        m_app.newScan.connect(m_win.new_scan)

        # Mache das Fenster sichtbar
        m_win.show()

        # Warte auf exit signal
        ret = m_app.exec_()

    except Exception as exc:
        print("\nError: Critical: ", exc)
        log.critical(exc)


    # Stoppe lokalen Server und beende das Programm
    w_server.stop_listen()
    sys.exit(ret)
