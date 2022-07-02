from PySide2 import QtCore
import pyodbc
import sys
import os
import sqlite3
import logging
import main


from pathlib import Path
log = logging.getLogger(Path(__file__).name)


def setup(log_file_path: str):
    # Setup Logfile Path
    logging.basicConfig(filename=log_file_path, level=logging.DEBUG, format='%(asctime)s: ( Thread: %(thread)d | '
                        'File: %(name)s ): %(levelname)s: %(message)s', datefmt='%d-%b-%y %H:%M:%S')

    # sys.stderr.write = logger.error
    sys.stderr = LoggerWriter(logging.getLogger().error)


def print_debug_versions():
    # Log....
    log.info("-------------------Programm Start: {0}-------------------".format(main.datetime.datetime.now()))

    log.debug("{0}[ Programm Version: {1} ] [ Python Version: {2} ] [ Qt Version: {3} ] "
              "[ PyODBC Version: {4} ] [ SQL Lite3 Version: {5} ] [ Unterstützte MS ODBC Driver Version: {6} ] "
              "[ Unterstützte FreeTDS Driver Version: {7} {8} ] "
              "[ Arbeitsverzeichnis: {9} ]".
              format("", main.PROGRAMM_VERSION, sys.version, QtCore.qVersion(),
                     pyodbc.version, sqlite3.version, main.SQL_DRIVER_USED_VERSION_MS_DRIVER,
                     main.SQL_DRIVER_USED_VERSION_FreeTDS, main.SQL_DRIVER_USED_VERSION_FreeTDS_VERSION,
                     os.path.abspath("./")))
    # Infoausgabe
    print("------------------------------------------------------------------")
    print("Programm Start: ", main.datetime.datetime.now())
    print("Programm Version: ", main.PROGRAMM_VERSION)
    print("Python Version: ", sys.version)
    print("Qt Version: ", QtCore.qVersion())
    print("PyODBC Version: ", pyodbc.version)
    print("SQL Lite3 Version: ", sqlite3.version)
    print("Unterstützte MS ODBC Driver Version: ", main.SQL_DRIVER_USED_VERSION_MS_DRIVER)
    print("Unterstützte FreeTDS Driver Version: ", main.SQL_DRIVER_USED_VERSION_FreeTDS, " ",
          main.SQL_DRIVER_USED_VERSION_FreeTDS_VERSION)
    print("Arbeitsverzeichnis: ", os.path.abspath("./"))
    print("------------------------------------------------------------------")


class LoggerWriter:
    level = None

    def __init__(self, level):
        self.level = level

    def write(self, message: str):
        message = message.rstrip()
        if message != "\n" and message != "":
            print(message)
            if "] \"GET /" not in message:
                self.level(message)

    # def flush(self):
    #     self.level(sys.stderr)
