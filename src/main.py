import sys
import mapplication
import mainwindow
import webserver

from http.server import HTTPServer
from threading import Thread


def start_web_server(server, arg2):
    server.serve_forever()


if __name__ == "__main__":

    webserver = HTTPServer(('127.0.0.1', 8888), webserver.RequestHandler)
    thread = Thread(target=start_web_server, args=(webserver, 0))
    thread.start()

    m_app = mapplication.MApplication([])
    m_win = mainwindow.MainWindow("./sqlLiteDB.db")

    # connect MApplication ( EventFilter ) with MainWindow( handle_EVENT )
    m_app.newScan.connect(m_win.new_scan)

    m_win.show()
    ret = m_app.exec_()

    webserver.shutdown()
    thread.join()
    sys.exit(ret)
