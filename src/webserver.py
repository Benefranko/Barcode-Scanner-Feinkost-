from http.server import ThreadingHTTPServer, HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
import localdatabasemanager
from datetime import datetime, timedelta
import calendar


class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        loc_db_mngr = localdatabasemanager.LocalDataBaseManager()
        loc_db_mngr.connect("./sqlLiteDB.db")
        html_status = 200
        try:
            match self.path:
                case "/monatsst.html":
                    html = open("../html/monatsst.html", "r").read()
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
                    html = open("../html/wochenst.html", "r").read()
                    scan_list = [0] * 7
                    weekday = datetime.today().weekday()
                    for day in range(0, weekday + 1):
                        current_day = datetime.today().date() - timedelta(days=day)
                        buf = loc_db_mngr.count_scans_at_date(current_day)
                        if buf is not None:
                            scan_list[weekday - day] = buf[0][0]
                    html = html.replace("%DATA_DATASET_1%", str(scan_list))

                case "/jahresst.html":
                    html = open("../html/jahresst.html", "r").read()
                    scan_list = [0] * 12
                    s_list = loc_db_mngr.get_all_scans()
                    current_year = datetime.now().year

                    for m in range(0, 12):
                        for scan in s_list:
                            scan_d = datetime.fromisoformat(scan[1])
                            if scan_d.year == current_year and scan_d.month == m:
                                scan_list[m] += 1
                    html = html.replace("%DATA_DATASET_1%", str(scan_list))
                case "/tabelle.html":
                    html = open("../html/tabelle.html", "r").read()
                    s_list = loc_db_mngr.get_all_scans()
                    sendData = ""
                    for scan in s_list:
                        sendData += """<tr>\n
                                            <td>{0}</td>\n
                                            <td>{1}</td>\n
                                            <td>{2}</td>\n
                                            <td>{3}</td>\n
                                            <td>{4}</td>\n
                                    </tr>\n""".format(scan[0], scan[1], scan[2], scan[3], scan[4])
                    html = html.replace("%LINES%", sendData)
                case "/":
                    html = open("../html/main.html", "r").read()
                case _:
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
            self.wfile.write(("<h1>Ein unerwartetes Problem ist aufgetreten!</h1>").encode("utf-8"))
        return


