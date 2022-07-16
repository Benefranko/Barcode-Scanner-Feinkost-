import mapplication
import mainwindow
import webserver
import logger
# Für Informationsausgabe

import datetime
import os
import sys

import logging
from pathlib import Path
log = logging.getLogger(Path(__file__).name)

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

# rename or delete logFile: ( RENAME | DELETE ):
log_file_delete_mode: str = "RENAME"


if __name__ == "__main__":
    # Change Working Directory to the one this file is in
    abspath = os.path.abspath(__file__)
    d_name = os.path.dirname(abspath)
    os.chdir(d_name)

    # Tee stderr to log and to console
    logger.setup(log_file_path)

    # Wenn --help aufgerufen wird, gib kurze Information aus
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            log.debug(sys.argv)
            print("Mit diesem Programm sollen Kunden durch das Scannen eines Produkt Bar Codes zusätzliche "
                  "Informationen zu diesem über die JTL-Wawi MS SQL Datenbank bekommen.")
            print("Mit '", sys.argv[0], " -platform off-screen' können sie das Programm ohne Fenster starten")
            exit()

    # Print All Versions and write it also to log
    logger.print_debug_versions()

    # MApplication
    m_app: mapplication = None
    # Lokalen Statistiken Server
    w_server: webserver = None
    # Rückgabewert QApplication
    ret: int = 0

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
    log.info("Programm Stop: {0}\n----------------------------------------------------------------"
             .format(datetime.datetime.now()))

    logger.cleanup()

    print("Programm wird mit Rückgabewert ({0}) beendet.".format(ret))
    sys.exit(ret)
