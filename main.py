import sys
import mapplication
import mainwindow

from http.server import ThreadingHTTPServer, HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
from threading import Thread


from PySide2.QtCore import QObject, Signal, Slot

m_app = None
m_win = None


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.path)
        match self.path:
            case "/monatsst.html":
                try:
                    html = open("./html/monatsst.html", "r")
                except Exception as exc:
                    print('critical error occurred: {0}. Please save your data and restart application'.format(exc))
                    return

                self.send_response(200)
                self.send_header('content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html.read().encode("utf-8"))
            case "/wochenst.html":
                try:
                    html = open("./html/test.html", "r")
                except Exception as exc:
                    print('critical error occurred: {0}. Please save your data and restart application'.format(exc))
                    return

                self.send_response(200)
                self.send_header('content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html.read().encode("utf-8"))
            case "/":
                try:
                    html = open("./html/main.html", "r")
                except Exception as exc:
                    print('critical error occurred: {0}. Please save your data and restart application'.format(exc))
                    return

                self.send_response(200)
                self.send_header('content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html.read().encode("utf-8"))
            case _:
                try:
                    html = open("./html/404.html", "r")
                except Exception as exc:
                    print('critical error occurred: {0}. Please save your data and restart application'.format(exc))
                    return

                self.send_response(404)
                self.send_header('content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html.read().encode("utf-8"))



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
    sys.exit(ret)
