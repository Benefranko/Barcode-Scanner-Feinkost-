import sys
import calendar

from http.server import ThreadingHTTPServer, HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
from threading import Thread

import main
import localdatabasemanager


# Lokaler einfacher Webserver, um Statistiken zur Nutzung angezeigt zu bekommen
class Server:

    # Attribute
    listenPort: str = ""
    listenIP: int = -1

    # Objekte
    webserver: HTTPServer = None
    thread: Thread = None

    # Konstruktor: Erstelle Server
    def __init__(self, l_ip, l_port):
        self.listenIP = l_ip
        self.listenPort = l_port
        try:
            self.webserver = ThreadingHTTPServer((l_ip, l_port), RequestHandler)
            self.thread = Thread(target=self.run_web_server, args=())
        except Exception as exc:
            print(exc)
            sys.exit(12)

    # Starte Server in extra Thread
    def start_listen(self):
        self.thread.start()

    # Stoppe Server und warte auf Beenden des Threads
    def stop_listen(self):
        self.webserver.shutdown()
        self.thread.join(3)

    # Thread - Funktion: Server wartet auf eingehende TCP Verbindungen und erstellt für jede einen
    # Thread mit einem RequestHandler
    def run_web_server(self):
        self.webserver.serve_forever()


# Klasse, die eine TCP Verbindung managed
class RequestHandler(BaseHTTPRequestHandler):

    # Objekte
    loc_db_mngr = None

    # HTTP Methode um Internetseitenquelltext zu bekommen:
    def do_GET(self):
        # Stelle Verbindung mit lokaler Datenbank her, um Statistiken auslesen zu können
        self.loc_db_mngr = localdatabasemanager.LocalDataBaseManager()
        self.loc_db_mngr.connect(main.local_db_path)

        # Standard HTTP Sende-Status
        html_status = 200
        try:
            # Je nach URL Pfad / je nach aufgerufener Internetseite:
            sub_paths = self.path.split("/")
            if sub_paths is not None and len(sub_paths) > 1:
                if sub_paths[1] == "monatsstatus.html":
                    # Lade HTML TEMPLATE für Monatsstatus mit Javascript Chart
                    html = open("../html/monatsstatus.html", "r").read()
                    now = datetime.now()
                    days_of_month = calendar.monthrange(now.year, now.month)[1]
                    day_of_month = int(now.strftime("%d"))

                    scan_list = [0] * days_of_month
                    for day in range(0, day_of_month + 1):
                        current_day = datetime.today().date() - timedelta(days=day)
                        scan_list[day_of_month - day] = self.loc_db_mngr.count_scans_at_date(current_day)[0][0]
                    html = html.replace("%DATA_DATA_SET_1%", str(scan_list))

                    label_list = [""] * days_of_month
                    for i in range(0, days_of_month):
                        label_list[i] = str(i + 1) + "."
                    html = html.replace("%DATA_LABEL_SET_1%", str(label_list))

                elif sub_paths[1] ==  "wochenstatus.html":
                    # Lade HTML TEMPLATE für Wochenstatus mit Javascript Chart
                    html = open("../html/wochenstatus.html", "r").read()
                    scan_list = [0] * 7
                    weekday = datetime.today().weekday()
                    for day in range(0, weekday + 1):
                        current_day = datetime.today().date() - timedelta(days=day)
                        buf = self.loc_db_mngr.count_scans_at_date(current_day)
                        if buf is not None:
                            scan_list[weekday - day] = buf[0][0]
                    html = html.replace("%DATA_DATA_SET_1%", str(scan_list))

                elif sub_paths[1] ==  "jahresstatus.html":
                    # Lade HTML TEMPLATE für Jahresstatus mit Javascript Chart
                    html = open("../html/jahresstatus.html", "r").read()
                    scan_list = [0] * 12
                    s_list = self.loc_db_mngr.get_all_scans()
                    current_year = datetime.now().year

                    for m in range(1, 13):
                        for scan in s_list:
                            scan_d = datetime.fromisoformat(scan[1])
                            if scan_d.year == current_year and scan_d.month == m:
                                scan_list[m-1] += 1
                    html = html.replace("%DATA_DATA_SET_1%", str(scan_list))

                # Erweiterbar mit tabelle/INDEX, mit immer nur 100 Items auf einer seite mit nächster
                #  seite und 1 seite zurück gg. mit POST die anzahl umstellbar machen!
                elif sub_paths[1] ==  "tabelle":
                    if len(sub_paths) < 3 or not sub_paths[2].isdigit():
                        html = open("../html/404.html", "r").read()
                        html_status = 404
                    else:
                        html = open("../html/tabelle.html", "r").read()
                        page: int = int(sub_paths[2])
                        page_count: int = int(self.loc_db_mngr.getItemCount() /
                                              main.item_count_on_web_server_list)
                        html = html.replace("%LAST%", str(page_count))
                        html = html.replace("%CURRENT%", str(page))

                        if page == page_count:
                            html = html.replace("%NEXT%\">></a>", "%NEXT%\"></a>")
                            html = html.replace("%NEXT%", str(page))
                        else:
                            html = html.replace("%NEXT%", str(page + 1))
                        if page == 0:
                            html = html.replace("%BACK%\"><</a>", "%BACK%\"></a>")
                            html = html.replace("%BACK%", str())
                        else:
                            html = html.replace("%BACK%", str(page - 1))

                        s_list = self.loc_db_mngr.getRange(main.item_count_on_web_server_list * page,
                                                           main.item_count_on_web_server_list)
                        send_data = ""
                        for scan in s_list:
                            send_data += """<tr>\n
                                                <td>{0}</td>\n
                                                <td>{1}</td>\n
                                                <td>{2}</td>\n
                                                <td>{3}</td>\n
                                                <td>{4}</td>\n
                                        </tr>\n""".format(scan[0], scan[1], scan[2], scan[3], scan[4])
                        html = html.replace("%LINES%", send_data)
                elif sub_paths[1] ==  "":
                    html = open("../html/main.html", "r").read()
                else:
                    html = open("../html/404.html", "r").read()
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
            self.wfile.write("<h1>Ein unerwartetes Problem ist aufgetreten!</h1>".encode("utf-8"))

        self.loc_db_mngr = None
        return
