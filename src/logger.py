from PySide2 import QtCore
import pyodbc
import sys
import os
import sqlite3
import logging
import constants as consts
import datetime

import updater


from pathlib import Path

log = logging.getLogger(Path(__file__).name)

# Global!!
glob_updater = updater.Updater()


def setup(log_file_path: str, dirPath: str):
    # Setup Logfile Path
    logging.basicConfig(filename=log_file_path, level=logging.DEBUG, format='%(asctime)s: ( Thread: %(thread)d | '
                        'File: %(name)s ): %(levelname)s: %(message)s', datefmt='%d-%b-%y %H:%M:%S')

    # Leite ganzen stderr output in Logger um
    sys.stderr = LoggerWriter(logging.getLogger().error)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    # init git path:
    global glob_updater
    glob_updater.setPath(dirPath)


def cleanup():
    sys.stderr = sys.__stderr__


def print_debug_versions():
    # Log....
    log.info("-------------------Programm Start: {0}-------------------".format(datetime.datetime.now()))

    if glob_updater:
        ver = glob_updater.getCurrentVersion()
    else:
        ver = "UNKNOWN"

    log.debug("{0}[ Programm Version: {1} ]\n [ Python Version: {2} ]\n"
              "[ Qt Version: {3} ] [ PyODBC Version: {4} ] [ SQL Lite3 Version: {5} ]\n"
              "[ Unterstützte MS ODBC Driver Version: {6} ] [ Unterstützte FreeTDS Driver Version: {7} {8} ]\n"
              "[ Arbeitsverzeichnis: {9} ] [UPDATE VERFÜGBAR: {10}] [NEUSTE VERSION: {11}]".
              format("", ver, sys.version, QtCore.qVersion(),
                     pyodbc.version, sqlite3.version, consts.SQL_DRIVER_USED_VERSION_MS_DRIVER,
                     consts.SQL_DRIVER_USED_VERSION_FreeTDS, consts.SQL_DRIVER_USED_VERSION_FreeTDS_VERSION,
                     os.path.abspath("./"), glob_updater.isUpdateAvailable(),
                     glob_updater.getNewestVersion()))
    # Infoausgabe
    # print("------------------------------------------------------------------")
    # print("Programm Start: ", datetime.datetime.now())
    # print("Programm Version: ", s.PROGRAMM_VERSION)
    # print("Python Version: ", sys.version)
    # print("Qt Version: ", QtCore.qVersion())
    # print("PyODBC Version: ", pyodbc.version)
    # # print("SQL Lite3 Version: ", sqlite3.version)
    # print("Unterstützte MS ODBC Driver Version: ", s.SQL_DRIVER_USED_VERSION_MS_DRIVER)
    # print("Unterstützte FreeTDS Driver Version: ", s.SQL_DRIVER_USED_VERSION_FreeTDS, " ",
    #       s.SQL_DRIVER_USED_VERSION_FreeTDS_VERSION)
    # print("Arbeitsverzeichnis: ", os.path.abspath("./"))
    print("--------------------------------------------------------------------------------\n")


class LoggerWriter:
    level = None

    def __init__(self, level):
        self.level = level

    def write(self, message: str):
        message = message.rstrip()
        if message != "\n" and message != "":
            # print(message)
            if "] \"GET /" not in message and "] \"POST /" not in message:
                self.level(message)

    # def flush(self):
    #     self.level(sys.stderr)
