import sys
import mapplication
import mainwindow
import localdatabasemanager

from http.server import ThreadingHTTPServer, HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
from threading import Thread

from datetime import datetime, timedelta
import calendar

from PySide2.QtCore import QObject, Signal, Slot

m_app = None
m_win = None


class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        loc_db_mngr = localdatabasemanager.LocalDataBaseManager()
        loc_db_mngr.connect("./sqlLiteDB.db")
        html_status = 200
        try:
            match self.path:
                case "/monatsst.html":
                    html = open("./html/monatsst.html", "r").read()
                    now = datetime.now()
                    days_of_month = calendar.monthrange(now.year, now.month)[1]
                    day_of_month = int(now.strftime("%d"))

                    scan_list = [0] * days_of_month
                    for day in range(0, day_of_month + 1):
                        current_day = datetime.today().date() - timedelta(days=day)
                        scan_list[day_of_month - day] = loc_db_mngr.count_scans_at_date(current_day)[0][0]
                    html = html.replace("%DATA_DATASET_1%", str(scan_list))

                    label_list = [""] * days_of_month
                    for i in range(0, days_of_month):
                        label_list[i] = str(i + 1) + "."
                    html = html.replace("%DATA_LABELSET_1%", str(label_list))

                case "/wochenst.html":
                    html = open("./html/wochenst.html", "r").read()
                    scan_list = [0] * 7
                    weekday = datetime.today().weekday()
                    for day in range(0, weekday + 1):
                        current_day = datetime.today().date() - timedelta(days=day)
                        scan_list[weekday - day] = loc_db_mngr.count_scans_at_date(current_day)[0][0]
                    html = html.replace("%DATA_DATASET_1%", str(scan_list))

                case "/jahresst.html":
                    html = open("./html/jahresst.html", "r").read()
                case "/":
                    html = open("./html/main.html", "r").read()
                case _:
                    html = open("./html/404.html", "r").read()
                    html_status = 404

            self.send_response(html_status)
            self.send_header('content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        except Exception as exc:
            print('critical error occurred: {0}. Please save your data and restart application'.format(exc))
            self.send_response(500)
            self.send_header('content-type', 'text/html')
            self.end_headers()
            self.wfile.write(("<h1>Ein unerwartetes Problem ist aufgetreten!</h1>").encode("utf-8"))
        return


def start_web_server(server, arg2):
    server.serve_forever()


if __name__ == "__main__":

    webserver = HTTPServer(('127.0.0.1', 8888), RequestHandler)
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
