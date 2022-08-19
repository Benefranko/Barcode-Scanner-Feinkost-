import sys
from requesthandler import RequestHandler
from http.server import ThreadingHTTPServer
from threading import Thread

import logging
from pathlib import Path

log = logging.getLogger(Path(__file__).name)


# Lokaler einfacher Webserver, um Statistiken zur Nutzung angezeigt zu bekommen
class Server:
    # Attribute
    listenPort: int = -1
    listenIP: str = ""

    # Objekte
    webserver: ThreadingHTTPServer = None
    thread: Thread = None

    # Konstruktor: Erstelle Server
    def __init__(self, l_ip, l_port):
        self.listenIP = l_ip
        self.listenPort = l_port
        try:
            self.thread = Thread(target=self.run_web_server, args=())
        except Exception as exc:
            log.critical("> Webserver erstellen ist fehlgeschlagen: {0}".format(exc))
            sys.exit(12)

    # Starte Server in extra Thread
    def start_listen(self):
        self.thread.start()

    # Stoppe Server und warte auf Beenden des Threads
    def stop_listen(self):
        if self.webserver:
            self.webserver.shutdown()
        self.thread.join(10)

    # Thread - Funktion: Server wartet auf eingehende TCP Verbindungen und erstellt für jede einen
    # Thread mit einem RequestHandler
    def run_web_server(self):
        with ThreadingHTTPServer((self.listenIP, self.listenPort), RequestHandler) as server:
            self.webserver = server
            server.serve_forever()
        return None
