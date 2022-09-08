import sys
from requesthandler import RequestHandler
from http.server import ThreadingHTTPServer

from PySide2.QtCore import QThread

import logging
from pathlib import Path

log = logging.getLogger(Path(__file__).name)


# Lokaler einfacher Webserver, um Statistiken zur Nutzung angezeigt zu bekommen
class Server(QThread):
    # Attribute
    listenPort: int = -1
    listenIP: str = ""

    # Objekte
    webserver: ThreadingHTTPServer = None

    # Konstruktor: Erstelle Server
    def __init__(self, l_ip, l_port):
        super().__init__()
        self.listenIP = l_ip
        self.listenPort = l_port

    # Starte Server in extra Thread
    def start_listen(self):
        self.start()

    # Stoppe Server und warte auf Beenden des Threads
    def stop_listen(self):
        log.info("[WEBSERVER]: Stoppe Webserver....")
        if self.webserver:
            self.webserver.shutdown()
        self.wait()

    # Thread - Funktion: Server wartet auf eingehende TCP Verbindungen und erstellt für jede einen
    # Thread mit einem RequestHandler
    def run(self):
        log.info("[WEBSERVER]: Starte Webserver....")
        with ThreadingHTTPServer((self.listenIP, self.listenPort), RequestHandler) as server:
            self.webserver = server
            log.info("[WEBSERVER]: Warte auf Verbindungen....")
            server.serve_forever()
        log.info("[WEBSERVER]: Webserver beendet.")
        return None
