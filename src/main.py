import mapplication
import mainwindow
import webserver
import logger
# Für Informationsausgabe

import datetime
import os
import sys

import settings as s

import logging
from pathlib import Path
log = logging.getLogger(Path(__file__).name)


if __name__ == "__main__":
    # Change Working Directory to the one this file is in
    abspath = os.path.abspath(__file__)
    d_name = os.path.dirname(abspath)
    os.chdir(d_name)

    # Tee stderr to log and to console
    try:
        logger.setup(s.log_file_path)
    except Exception as e:
        print("Failed to setup Logger: {0}".format(e))
        sys.exit(99)

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
    m_win: mainwindow = None

    try:
        # Starte Lokalen Statistiken Server
        w_server = webserver.Server(s.local_http_server_ip, s.local_http_server_port)
        w_server.start_listen()

        # Erstelle Key Press Event Handler und Ui - MainWindow
        m_app = mapplication.MApplication(sys.argv)
        m_win = mainwindow.MainWindow(s.local_db_path, s.ms_sql_server_ip, s.ms_sql_server_port, s.ui_file_path)

        # connect MApplication ( EventFilter ) with MainWindow( handle_EVENT )
        m_app.newScan.connect(m_win.new_scan)

        # Mache das Fenster sichtbar
        m_win.show()

        # Warte auf exit signal
        ret = m_app.exec_()

        m_win.cleanUp()

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
