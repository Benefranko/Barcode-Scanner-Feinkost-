import sys
import mapplication
import mainwindow

from http.server import ThreadingHTTPServer, HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
from threading import Thread


from PySide2.QtCore import QObject, Signal, Slot


m_win = None


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('content-type', 'text/html')
        self.end_headers()
        if m_win is not None:
            self.wfile.write(
                ("COUNT OF ELEMENTS: " + str(m_win.window.groupBox.layout().count()) + "\r\n   URL:/").encode())
        self.wfile.write(self.path[1:].encode())


def start_web_server(server, arg2):
    server.serve_forever()


if __name__ == "__main__":
    webserver = HTTPServer(('127.0.0.1', 8888), RequestHandler)
    thread = Thread(target=start_web_server, args=(webserver, 0))
    thread.start()

    m_app = mapplication.MApplication([])
    m_win = mainwindow.MainWindow()

    # connect MApplication ( EventFilter ) with MainWindow( handle_EVENT )
    m_app.newScan.connect(m_win.new_scan)

    m_win.show()
    ret = m_app.exec_()

    webserver.shutdown()
    thread.join()
    print("joined")
    sys.exit(ret)
