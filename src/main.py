import mapplication
import mainwindow
import webserver
import logger
# Für Informationsausgabe

import datetime
import os
import sys
import timeit

from PySide2.QtWidgets import QApplication, QWidget

import constants as consts
import updater


import logging
from pathlib import Path
log = logging.getLogger(Path(__file__).name)


if __name__ == "__main__":
    # Change Working Directory to the one this file is in
    abspath = os.path.abspath(__file__)
    d_name = os.path.dirname(abspath)
    os.chdir(d_name)

    u = updater.Updater(None, d_name)


    # u.get_most_recent_git_tag()
    sys.exit(0)

    # Tee stderr to log and to console
    try:
        logger.setup(consts.log_file_path)
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

    # STarte MApplication
    try:
        # Starte Lokalen Statistiken Server
        if not mapplication.MApplication.instance():
            m_app = mapplication.MApplication(sys.argv)
        else:
            m_app = mapplication.QApplication.instance()

    except Exception as exc:
        log.critical("\nError: Critical: failed to Start MApplication! {0}".format(exc))
        sys.exit(1231)

    # Start webserver!
    try:
        # Starte Lokalen Statistiken Server
        w_server = webserver.Server(consts.local_http_server_ip, consts.local_http_server_port)
        w_server.finished.connect(m_app.webserver_finished)
        w_server.start_listen()

    except Exception as exc:
        log.critical("\nError: Critical: failed to Start Webserver! {0}".format(exc))
        sys.exit(1212)

    for index in range(1, 10):
        start = timeit.default_timer()

        try:
            # Erstelle Key Press Event Handler und Ui - MainWindow
            m_win = mainwindow.MainWindow(consts.local_db_path, consts.ui_file_path)
            # connect MApplication ( EventFilter ) with MainWindow( handle_EVENT )
            m_app.newScan.connect(m_win.new_scan)
            # Mache das Fenster sichtbar
            m_win.show()
            # Warte auf exit signal
            ret = m_app.exec_()
            # Beende alle SQL Verbindungen
            m_win.cleanUp()

        except Exception as exc:
            log.critical("\nError: Critical: {0}".format(exc))
            if ret == 0:
                ret = -1

        if ret == 0:
            break
        else:
            try:
                m_app.newScan.disconnect()
            except Exception as ex:
                print("DISCONNECT failed:", ex)
            m_win = None
            end = timeit.default_timer()
            if end - start > 360:
                index = 1
            log.critical("Die GUI ist zum {0}. mal abgestürzt. Fehlercode: {1}".format(index, ret))
            if index < 10:
                log.critical("Versuche die GUI neu zu starten....")
            else:
                log.critical("Maximale Anzahl an Neustartversuchen erreicht! Zeige Black-Screen!")

    # Wenn maximale Anzahl an Neustartversuchen erreicht wurde, zeige Black-Screen!
    if ret != 0:
        try:
            # Ignore Key Input!:
            m_app.ignore_key_input = True

            # Create a Qt widget, which will be our window.
            m_win = QWidget()
            m_win.setStyleSheet("background: black; ")
            screenSize = QApplication.screens()[len(QApplication.screens()) - 1].availableGeometry()
            m_win.setGeometry(screenSize)
            m_win.showFullScreen()
            m_win.show()
            # Start the event loop.
            m_app.exec_()
        except Exception as exc:
            log.critical("\nError in BLACK-SCREEN: {0}".format(exc))

    try:
        w_server.finished.disconnect()
    except Exception as ex:
        print("DISCONNECT failed:", ex)
    m_win = None
    m_app = None

    # Stoppe lokalen Server und beende das Programm
    w_server.stop_listen()
    log.info("-> exit({0}) -> Programm Stop um: {1}"
             "\n--------------------------------------------------------------------------------"
             .format(ret, datetime.datetime.now()))

    logger.cleanup()
    sys.exit(ret)
