import calendar
import shutil
import re

from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta

import settings
import localdatabasemanager

import logging
from pathlib import Path

log = logging.getLogger(Path(__file__).name)


# Klasse, die eine TCP Verbindung managed
class RequestHandler(BaseHTTPRequestHandler):
    # class RequestHandler(SimpleHTTPRequestHandler):
    # Objekte
    loc_db_mngr = None

    # HTTP Methode um Internetseitenquelltext zu bekommen:
    def do_GET(self):
        # Stelle Verbindung mit lokaler Datenbank her, um Statistiken auslesen zu können
        self.loc_db_mngr = localdatabasemanager.LocalDataBaseManager()
        if self.loc_db_mngr.connect(settings.local_db_path) is None:
            self.send_error(500, "Konnte keine Verbindung mit der lokalen Datenbank herstellen!")
            return

        # Standard HTTP Sende-Status
        html_status: int = 200
        html_bytes: bytes
        content_type: str = "text/html"
        sub_paths = self.path.split("/")

        try:

            ####
            # Homepage
            ####
            if self.checkPathIsNotValid(sub_paths, 1):
                html_bytes = self.getFileText("../web/html/index.html")

            ####
            # CSS
            ####
            elif sub_paths[1] == "css":
                content_type = 'text/css'
                if self.checkPathIsNotValid(sub_paths, 2):
                    html_status, html_bytes = self.getPageNotFound()

                elif sub_paths[2] == "style.css":
                    html_bytes = self.getFileText("../web/css/style.css")

                else:
                    html_status, html_bytes = self.getPageNotFound()

            ####
            # Java Skript
            ####
            elif sub_paths[1] == "js":
                content_type = 'text/javascript'
                if self.checkPathIsNotValid(sub_paths, 2):
                    html_status, html_bytes = self.getPageNotFound()

                elif sub_paths[2] == "script.js":
                    html_bytes = self.getFileText("../web/scripts/script.js")

                else:
                    html_status, html_bytes = self.getPageNotFound()

            ####
            # Images
            ####
            elif sub_paths[1] == "favicon.ico":
                content_type = 'image/x-icon'
                html_bytes = self.getFileBytes("../images/favicon.ico")

            elif sub_paths[1] == "images":
                content_type = 'image/png'

                if self.checkPathIsNotValid(sub_paths, 2):
                    html_status, html_bytes = self.getPageNotFound()

                elif sub_paths[2] == "favicon.ico":
                    content_type = 'image/x-icon'
                    html_bytes = self.getFileBytes("../images/favicon.ico")

                elif sub_paths[2] == "background.png":
                    html_bytes = self.getFileBytes("../images/background.jpg")

                else:
                    html_status, html_bytes = self.getPageNotFound()

            ####
            # Downloads
            ####
            elif sub_paths[1] == "download":
                content_type = 'text/x-please-download-me'

                if self.checkPathIsNotValid(sub_paths, 2):
                    html_status, html_bytes = self.getPageNotFound()

                elif sub_paths[2] == "Logfile.txt":
                    html_bytes = self.getFileText(settings.log_file_path)

                else:
                    html_status, html_bytes = self.getPageNotFound()

            ####
            # Internetseiten
            ####
            elif sub_paths[1] == "html":

                if self.checkPathIsNotValid(sub_paths, 2):
                    html_status, html_bytes = self.getPageNotFound()

                elif sub_paths[2] == "wochenstatus.html":
                    html_bytes = self.getWochenStatusPage()

                elif sub_paths[2] == "wochenstatus-kategorie.html":
                    html_bytes = self.getWochenStatusKategoriePage()

                elif sub_paths[2] == "wochenstatus-hersteller.html":
                    html_bytes = self.getWochenStatusHerstellerPage()

                elif sub_paths[2] == "monatsstatus.html":
                    html_bytes = self.getMonatsStatusPage()

                elif sub_paths[2] == "monatsstatus-hersteller.html":
                    html_bytes = self.getMonatsKategorieStatusPage()

                elif sub_paths[2] == "monatsstatus-kategorie.html":
                    html_bytes = self.getMonatsHerstellerStatusPage()

                elif sub_paths[2] == "jahresstatus.html":
                    html_bytes = self.getJahresStatusPage()

                elif sub_paths[2] == "jahresstatus-kategorie.html":
                    html_bytes = self.getJahresKategorieStatusPage()

                elif sub_paths[2] == "jahresstatus-hersteller.html":
                    html_bytes = self.getJahresHerstellerStatusPage()

                elif sub_paths[2] == "tabelle":
                    if self.checkPathIsNotValid(sub_paths, 3) or not sub_paths[3].isdigit():
                        html_status, html_bytes = self.getPageNotFound()

                    else:
                        html_bytes = self.getTabellenPage(sub_paths[3])

                elif sub_paths[2] == "settings.html":
                    html_bytes = self.getSettingsPage()

                elif sub_paths[2] == "log.html":
                    html_bytes = self.getLogPage()

                else:
                    html_status, html_bytes = self.getPageNotFound()

            else:
                html_status, html_bytes = self.getPageNotFound()

            if len(html_bytes) == 0:
                html_status, html_bytes = self.getPageNotFound()

            ####
            # Send Header
            ####
            self.send_response(html_status)
            self.send_header('content-type', content_type)
            self.end_headers()

            ####
            # Send Data
            ####
            # Write Funktion in eigenem try-catch statement, um Html-Fehler senden zu können, wenn im SQL Teil
            # etwas fehlschlägt!
            try:
                self.wfile.write(html_bytes)
            except Exception as exc:
                log.warning("> Es ist ein Fehler im RequestHandler aufgetreten: write() failed: {0}".format(exc))
                self.loc_db_mngr = None
                return

        ####
        # Catch Code / SQL - Exceptions
        ####
        except Exception as exc:
            log.error("> Es ist ein Fehler im RequestHandler aufgetreten: {0}".format(exc))

            # Write Funktion in eigenem try-catch statement, um Html-Fehler senden zu können, wenn im SQL Teil
            # etwas fehlschlägt!
            try:
                self.send_error(500, "Ein unerwartetes Problem ist aufgetreten!")
            except Exception as exc:
                log.warning("> Es ist ein Fehler im RequestHandler aufgetreten: write() failed: {0}".format(exc))
                return

        self.loc_db_mngr = None
        return

    @staticmethod
    def checkPathIsNotValid(subpaths, index) -> bool:
        return subpaths is None or len(subpaths) <= index or subpaths[index] is None or subpaths[index] == ""

    @staticmethod
    def getFileBytes(path) -> bytes:
        # Open the file, read bytes, return bytes
        with open(path, 'rb') as file:
            bts = file.read()
        return bts

    @staticmethod
    def getFileText(path) -> bytes:
        # Open the file, read bytes, return bytes
        with open(path, 'rt') as file:
            bts = file.read()
        return bts.encode("utf-8")

    def getPageNotFound(self) -> (int, bytes):
        log.debug("> WARNUNG: Seite nicht gefunden: {0}".format(self.path))
        return 404, open("../web/html/404.html", "r").read().encode()

    def getWochenStatusPage(self) -> bytes:
        # Lade HTML TEMPLATE für Wochenstatus mit Javascript Chart
        html_string = self.getFileText("../web/html/wochenstatus.html")
        scan_list = [0] * 7
        weekday = datetime.today().weekday()
        for day in range(0, weekday + 1):
            current_day = datetime.today().date() - timedelta(days=day)
            buf = self.loc_db_mngr.count_scans_at_date(current_day)
            if buf is not None:
                scan_list[weekday - day] = buf[0][0]
        return html_string.replace("%DATA_DATA_SET_1%".encode(), str(scan_list).encode())

    def getWochenStatusKategoriePage(self) -> bytes:
        # Lade HTML TEMPLATE für Wochenstatus mit Javascript Chart
        html_string = open("../web/html/wochenstatus-kategorie.html", "r").read()
        replace_str: str = ""
        weekday = datetime.today().weekday()

        kategorie_list = self.loc_db_mngr.getKategorieList()

        for i in range(0, len(kategorie_list)):
            if kategorie_list[i] is None:
                continue
            elif kategorie_list[i][0] is None:
                kategorie = "Unbekannt"
            else:
                kategorie = kategorie_list[i][0]

            scan_list = [0] * 7
            for day in range(0, weekday + 1):
                current_day = datetime.today().date() - timedelta(days=day)
                buf = self.loc_db_mngr.count_scans_at_date_where_kategorie_is(current_day, kategorie)
                if buf is not None:
                    scan_list[weekday - day] = buf[0][0]
            if replace_str != "":
                replace_str += ","
            replace_str += "{\r\n" \
                           + "     label: '" + kategorie + "',\r\n" \
                           + "     data: " + str(scan_list) + ",\r\n" \
                           + "     backgroundColor: [\r\n" \
                           + "         'rgba(" + str((i * 50) % 200) + ", " + \
                           str((i * 100) % 200) + ", " + \
                           str((i * 150) % 200) + ", 0.2)'\r\n" \
                           + "     ],\r\n" \
                           + "    borderColor: [\r\n" \
                           + "         'rgba(" + str((i * 50) % 200) + ", " + \
                           str((i * 100) % 200) + ", " + \
                           str((i * 150) % 200) + ", 1)'\r\n" \
                           + "     ],\r\n" \
                           + "     borderWidth: 2\r\n" \
                           + "}"

        html_string = html_string.replace("%DATA_DATA_SETS%", replace_str)
        return html_string.encode()

    def getWochenStatusHerstellerPage(self) -> bytes:
        # Lade HTML TEMPLATE für Wochenstatus mit Javascript Chart
        html_string = open("../web/html/wochenstatus-hersteller.html", "r").read()
        replace_str: str = ""
        weekday = datetime.today().weekday()

        herstellerlist = self.loc_db_mngr.getHerstellerList()

        for i in range(0, len(herstellerlist)):
            if herstellerlist[i] is None:
                continue
            elif herstellerlist[i][0] is None:
                hersteller = "Unbekannt"
            else:
                hersteller = herstellerlist[i][0]

            scan_list = [0] * 7
            for day in range(0, weekday + 1):
                current_day = datetime.today().date() - timedelta(days=day)
                buf = self.loc_db_mngr.count_scans_at_date_where_hersteller_is(current_day,
                                                                               hersteller)
                if buf is not None:
                    scan_list[weekday - day] = buf[0][0]
            if replace_str != "":
                replace_str += ","
            replace_str += "{\r\n" \
                           + "     label: '" + hersteller + "',\r\n" \
                           + "     data: " + str(scan_list) + ",\r\n" \
                           + "     backgroundColor: [\r\n" \
                           + "         'rgba(" + str((i * 50) % 200) + ", " + \
                           str((i * 100) % 200) + ", " + \
                           str((i * 150) % 200) + ", 0.2)'\r\n" \
                           + "     ],\r\n" \
                           + "    borderColor: [\r\n" \
                           + "         'rgba(" + str((i * 50) % 200) + ", " + \
                           str((i * 100) % 200) + ", " + \
                           str((i * 150) % 200) + ", 1)'\r\n" \
                           + "     ],\r\n" \
                           + "     borderWidth: 2\r\n" \
                           + "}"

        html_string = html_string.replace("%DATA_DATA_SETS%", replace_str)
        return html_string.encode()

    def getMonatsStatusPage(self) -> bytes:

        # Lade HTML TEMPLATE für Monatsstatus mit Javascript Chart
        html_string = open("../web/html/monatsstatus.html", "r").read()
        now = datetime.now()
        days_of_month = calendar.monthrange(now.year, now.month)[1]
        day_of_month = int(now.strftime("%d")) - 1

        scan_list = [0] * days_of_month
        for day in range(0, day_of_month + 1):
            current_day = datetime.today().date() - timedelta(days=day)
            scan_list[day_of_month - day] = self.loc_db_mngr.count_scans_at_date(current_day)[0][0]
        html_string = html_string.replace("%DATA_DATA_SET_1%", str(scan_list))

        label_list = [""] * days_of_month
        for i in range(0, days_of_month):
            label_list[i] = str(i + 1) + "."
        html_string = html_string.replace("%DATA_LABEL_SET_1%", str(label_list))
        return html_string.encode()

    def getMonatsKategorieStatusPage(self) -> bytes:

        # Lade HTML TEMPLATE für Wochenstatus mit Javascript Chart
        html_string = open("../web/html/monatsstatus-kategorie.html", "r").read()

        now = datetime.now()
        days_of_month = calendar.monthrange(now.year, now.month)[1]
        day_of_month = int(now.strftime("%d")) - 1

        replace_str: str = ""
        kategorie_list = self.loc_db_mngr.getKategorieList()

        for i in range(0, len(kategorie_list)):
            if kategorie_list[i] is None:
                continue
            elif kategorie_list[i][0] is None:
                kategorie = "Unbekannt"
            else:
                kategorie = kategorie_list[i][0]

            scan_list = [0] * days_of_month
            for day in range(0, day_of_month + 1):
                current_day = datetime.today().date() - timedelta(days=day)
                buf = self.loc_db_mngr.count_scans_at_date_where_kategorie_is(current_day, kategorie)
                if buf is not None:
                    scan_list[day_of_month - day] = buf[0][0]

            if replace_str != "":
                replace_str += ","
            replace_str += "{\r\n" \
                           + "     label: '" + kategorie + "',\r\n" \
                           + "     data: " + str(scan_list) + ",\r\n" \
                           + "     backgroundColor: [\r\n" \
                           + "         'rgba(" + str((i * 50) % 200) + ", " + \
                           str((i * 100) % 200) + ", " + \
                           str((i * 150) % 200) + ", 0.2)'\r\n" \
                           + "     ],\r\n" \
                           + "    borderColor: [\r\n" \
                           + "         'rgba(" + str((i * 50) % 200) + ", " + \
                           str((i * 100) % 200) + ", " + \
                           str((i * 150) % 200) + ", 1)'\r\n" \
                           + "     ],\r\n" \
                           + "     borderWidth: 2\r\n" \
                           + "}"

        html_string = html_string.replace("%DATA_DATA_SETS%", replace_str)

        label_list = [""] * days_of_month
        for i in range(0, days_of_month):
            label_list[i] = str(i + 1) + "."
        html_string = html_string.replace("%DATA_LABEL_SET%", str(label_list))
        return html_string.encode()

    def getMonatsHerstellerStatusPage(self) -> bytes:

        # Lade HTML TEMPLATE für Wochenstatus mit Javascript Chart
        html_string = open("../web/html/monatsstatus-hersteller.html", "r").read()

        now = datetime.now()
        days_of_month = calendar.monthrange(now.year, now.month)[1]
        day_of_month = int(now.strftime("%d")) - 1

        replace_str: str = ""
        herstellerlist = self.loc_db_mngr.getHerstellerList()

        for i in range(0, len(herstellerlist)):
            if herstellerlist[i] is None:
                continue
            elif herstellerlist[i][0] is None:
                hersteller = "Unbekannt"
            else:
                hersteller = herstellerlist[i][0]

            scan_list = [0] * days_of_month
            for day in range(0, day_of_month + 1):
                current_day = datetime.today().date() - timedelta(days=day)
                buf = self.loc_db_mngr.count_scans_at_date_where_hersteller_is(current_day, hersteller)
                if buf is not None:
                    scan_list[day_of_month - day] = buf[0][0]

            if replace_str != "":
                replace_str += ","
            replace_str += "{\r\n" \
                           + "     label: '" + hersteller + "',\r\n" \
                           + "     data: " + str(scan_list) + ",\r\n" \
                           + "     backgroundColor: [\r\n" \
                           + "         'rgba(" + str((i * 50) % 200) + ", " + \
                           str((i * 100) % 200) + ", " + \
                           str((i * 150) % 200) + ", 0.2)'\r\n" \
                           + "     ],\r\n" \
                           + "    borderColor: [\r\n" \
                           + "         'rgba(" + str((i * 50) % 200) + ", " + \
                           str((i * 100) % 200) + ", " + \
                           str((i * 150) % 200) + ", 1)'\r\n" \
                           + "     ],\r\n" \
                           + "     borderWidth: 2\r\n" \
                           + "}"

        html_string = html_string.replace("%DATA_DATA_SETS%", replace_str)

        label_list = [""] * days_of_month
        for i in range(0, days_of_month):
            label_list[i] = str(i + 1) + "."
        html_string = html_string.replace("%DATA_LABEL_SET%", str(label_list))
        return html_string.encode()

    def getJahresStatusPage(self) -> bytes:

        # Lade HTML TEMPLATE für Jahresstatus mit Javascript Chart
        html_string = open("../web/html/jahresstatus.html", "r").read()
        scan_list = [0] * 12
        s_list = self.loc_db_mngr.get_all_scans()
        current_year = datetime.now().year

        for m in range(1, 13):
            for scan in s_list:
                scan_d = datetime.fromisoformat(scan[1])
                if scan_d.year == current_year and scan_d.month == m:
                    scan_list[m - 1] += 1
        html_string = html_string.replace("%DATA_DATA_SET_1%", str(scan_list))
        return html_string.encode()

    def getJahresKategorieStatusPage(self) -> bytes:

        # Lade HTML TEMPLATE für Jahresstatus mit Javascript Chart
        html_string = open("../web/html/jahresstatus-kategorie.html", "r").read()
        replace_str: str = ""
        current_year = datetime.now().year

        s_list = self.loc_db_mngr.get_all_scans()
        kategorie_list = self.loc_db_mngr.getKategorieList()
        for i in range(0, len(kategorie_list)):
            if kategorie_list[i] is None:
                continue
            elif kategorie_list[i][0] is None:
                kategorie = "Unbekannt"
            else:
                kategorie = kategorie_list[i][0]

            ####
            # DRINGEND MIT SQL STATEMENT SCHNELLER MACHEN!!!!!!
            ####
            scan_list = [0] * 12
            for m in range(1, 13):
                for scan in s_list:
                    scan_d = datetime.fromisoformat(scan[1])
                    if scan_d.year == current_year and scan_d.month == m:
                        if scan[5] is None and kategorie == "Unbekannt":
                            scan_list[m - 1] += 1
                        elif scan[6] == kategorie:
                            scan_list[m - 1] += 1

            if replace_str != "":
                replace_str += ","
            replace_str += "{\r\n" \
                           + "     label: '" + kategorie + "',\r\n" \
                           + "     data: " + str(scan_list) + ",\r\n" \
                           + "     backgroundColor: [\r\n" \
                           + "         'rgba(" + str((i * 50) % 200) + ", " + \
                           str((i * 100) % 200) + ", " + \
                           str((i * 150) % 200) + ", 0.2)'\r\n" \
                           + "     ],\r\n" \
                           + "    borderColor: [\r\n" \
                           + "         'rgba(" + str((i * 50) % 200) + ", " + \
                           str((i * 100) % 200) + ", " + \
                           str((i * 150) % 200) + ", 1)'\r\n" \
                           + "     ],\r\n" \
                           + "     borderWidth: 2\r\n" \
                           + "}"

        html_string = html_string.replace("%DATA_DATA_SETS%", replace_str)
        return html_string.encode()

    def getJahresHerstellerStatusPage(self) -> bytes:

        # Lade HTML TEMPLATE für Jahresstatus mit Javascript Chart
        html_string = open("../web/html/jahresstatus-hersteller.html", "r").read()
        replace_str: str = ""
        current_year = datetime.now().year

        s_list = self.loc_db_mngr.get_all_scans()
        herstellerlist = self.loc_db_mngr.getHerstellerList()
        for i in range(0, len(herstellerlist)):
            if herstellerlist[i] is None:
                continue
            elif herstellerlist[i][0] is None:
                hersteller = "Unbekannt"
            else:
                hersteller = herstellerlist[i][0]

            ####
            # DRINGEND MIT SQL STATEMENT SCHNELLER MACHEN!!!!!!
            ####
            scan_list = [0] * 12
            for m in range(1, 13):
                for scan in s_list:
                    scan_d = datetime.fromisoformat(scan[1])
                    if scan_d.year == current_year and scan_d.month == m:
                        if scan[5] is None and hersteller == "Unbekannt":
                            scan_list[m - 1] += 1
                        elif scan[5] == hersteller:
                            scan_list[m - 1] += 1

            if replace_str != "":
                replace_str += ","
            replace_str += "{\r\n" \
                           + "     label: '" + hersteller + "',\r\n" \
                           + "     data: " + str(scan_list) + ",\r\n" \
                           + "     backgroundColor: [\r\n" \
                           + "         'rgba(" + str((i * 50) % 200) + ", " + \
                           str((i * 100) % 200) + ", " + \
                           str((i * 150) % 200) + ", 0.2)'\r\n" \
                           + "     ],\r\n" \
                           + "    borderColor: [\r\n" \
                           + "         'rgba(" + str((i * 50) % 200) + ", " + \
                           str((i * 100) % 200) + ", " + \
                           str((i * 150) % 200) + ", 1)'\r\n" \
                           + "     ],\r\n" \
                           + "     borderWidth: 2\r\n" \
                           + "}"

        html_string = html_string.replace("%DATA_DATA_SETS%", replace_str)
        return html_string.encode()

    def getTabellenPage(self, page_num) -> bytes:
        html_string = self.getFileText("../web/html/tabelle.html").decode()
        page: int = int(page_num)
        page_count: int = int(self.loc_db_mngr.getItemCount() / settings.item_count_on_web_server_list)

        if page < 0 or page > page_count:
            page = page_count

        html_string = html_string.replace("%LAST%", str(page_count))
        html_string = html_string.replace("%CURRENT%", str(page))

        if page == page_count:
            html_string = html_string.replace("%NEXT%\">></a>", "%NEXT%\"></a>")
            html_string = html_string.replace("%NEXT%", str(page))
        else:
            html_string = html_string.replace("%NEXT%", str(page + 1))
        if page == 0:
            html_string = html_string.replace("%BACK%\"><</a>", "%BACK%\"></a>")
            html_string = html_string.replace("%BACK%", str("0"))
        else:
            html_string = html_string.replace("%BACK%", str(page - 1))

        s_list = self.loc_db_mngr.getRange(settings.item_count_on_web_server_list * page,
                                           settings.item_count_on_web_server_list)
        send_data = ""
        for scan in s_list:
            send_data += """<tr>\n
                                                        <td>{0}</td>\n
                                                        <td>{1}</td>\n
                                                        <td>{2}</td>\n
                                                        <td>{3}</td>\n
                                                        <td>{4}</td>\n
                                                        <td>{5}</td>\n
                                                        <td>{6}</td>\n
                                                </tr>\n""".format(scan[0], scan[1], scan[2], scan[3], scan[4], scan[5],
                                                                  scan[6])
        return html_string.replace("%LINES%", send_data).encode()

    def getSettingsPage(self) -> bytes:
        html_bytes = self.getFileText("../web/html/settings.html")
        return self.replaceVarsInSettingsHtml(html_bytes.decode()).encode()

    @staticmethod
    def getLogPage() -> bytes:
        html_string = open("../web/html/log.html", "r").read()
        text: str = ""
        with open(settings.log_file_path, "r") as file:
            last: str = ""
            for line in file:
                text += "<p "
                if "DEBUG:" in line:
                    last = "name=\"debug\" style=\"display: none; color: gray\""
                    text += last
                elif "INFO:" in line:
                    last = "name=\"info\" style=\"color: black;\""
                    text += last
                elif "WARNING:" in line:
                    last = "name=\"warning\" style=\"color: orange;\""
                    text += last
                elif "ERROR:" in line:
                    last = "name=\"error\" style=\"color: red;\""
                    text += last
                elif "CRITICAL:" in line:
                    last = "name=\"critical\" style=\"color: red;\""
                    text += last
                elif "-----------------------------------------------------" in line:
                    last = ""
                else:
                    text += last
                text += ">" + line.rstrip() + "</p>\n"
        return html_string.replace("%DATA%", text).encode()

    @staticmethod
    def replaceVarsInSettingsHtml(html: str) -> str:
        html = html.replace("%anzeigezeit_Hersteller_value%", str(settings.SHOW_PRODUCER_INFOS_TIME))
        html = html.replace("%anzeigezeit_value%", str(settings.SHOW_TIME))
        html = html.replace("%changeAdvertiseTime_value%", str(settings.CHANGE_ADVERTISE_TIME))

        for i in range(1, 5):
            html = html.replace("%STATUS" + str(i) + "%", "")
        return html

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        html_string: str = ""
        html_status: int = 200

        self.loc_db_mngr = localdatabasemanager.LocalDataBaseManager()
        self.loc_db_mngr.connect(settings.local_db_path)

        try:
            if self.path == "/html/log.html":
                log.debug("> Try to clear log...")

                if "password=" + settings.clear_log_file_pw + "&" in str(post_data):
                    if settings.log_file_delete_mode == "RENAME":
                        shutil.copyfile(settings.log_file_path, settings.log_file_path.replace(".log", "") + "_backup_"
                                        + datetime.now().strftime("%m-%d-%Y_%H-%M-%S") + ".log")

                        fo = open(settings.log_file_path, "w")
                        fo.truncate()
                        fo.close()

                        log.info("    -> Log renamed")

                        self.do_GET()
                        return
                    elif settings.log_file_delete_mode == "DELETE":
                        fo = open(settings.log_file_path, "w")
                        fo.truncate()
                        fo.close()

                        log.info("    -> Log deleted")

                        self.do_GET()
                        return
                    else:
                        log.error("   -> Fehler: Unbekannter log_file_delete_mode: {0}"
                                  .format(settings.log_file_delete_mode))
                        self.do_GET()
                        return
                else:
                    log.warning("   -> Clear/Delete failed: Wrong password: ".format(str(post_data)))
                    html_string = open("../web/html/tabelle-falsches-pw.html", "r").read()

            elif self.path == "/html/settings.html":
                if str(post_data.decode()) == "ReloadAdvertiseListButton=Neu+laden":
                    settings.want_reload_advertise = True
                    log.info("> Reload Advertise List")
                    self.do_GET()
                    return
                else:
                    data = re.split('&|='.encode(), post_data)
                    admin: bool = False

                    if "adminPW".encode() in data and data.index("adminPW".encode()) < (len(data) - 1):
                        if data[data.index("adminPW".encode()) + 1].decode() == settings.clear_log_file_pw:
                            admin = True
                        else:
                            log.warning(" > Falsches Passwort in Webeinstellungen: {0}".
                                        format(data[data.index("adminPW".encode()) + 1].decode()))
                    else:
                        log.error(" > Kein Passwort in Webeinstellungen Postanfrage!.")

                    for i in range(0, len(data), 2):

                        if i == len(data) - 1 or data[i].decode() == "adminPW":
                            continue

                        elif data[i].decode() == "anzeigezeit_value":
                            # post_data.startswith("anzeigezeit_value=".encode("utf-8"))
                            html_string = open("../web/html/settings.html", "r").read()

                            if not admin:
                                html_string = html_string.replace("%anzeigezeit_value%", str(settings.SHOW_TIME))
                                html_string = html_string.replace("%STATUS1%",
                                                                  "<font color='red'>Aktualisierung fehlgeschlagen! "
                                                                  "Falsches Admin Passwort</font>")
                            elif data[i + 1].isdigit():
                                time = int(data[i + 1])
                                self.loc_db_mngr.setDelayTime("ARTIKEL", time)
                                settings.SHOW_TIME = time
                                html_string = html_string.replace("%anzeigezeit_value%", str(settings.SHOW_TIME))
                                html_string = html_string.replace("%STATUS1%",
                                                                  "<font color='green'>Erfolgreich aktualisiert!</font>"
                                                                  "")
                                log.info("> Aktualisiere Artikel Information Anzeigezeit zu: {0} Sekunden.".
                                         format(settings.SHOW_TIME))

                            else:
                                html_string = html_string.replace("%anzeigezeit_value%", str(settings.SHOW_TIME))
                                html_string = html_string.replace("%STATUS1%",
                                                                  "<font color='red'>Aktualisierung fehlgeschlagen! "
                                                                  "Keine Zahl?</font>")
                            html_string = self.replaceVarsInSettingsHtml(html_string)

                        elif data[i].decode() == "anzeigezeit_Hersteller_value":
                            # post_data.startswith("anzeigezeit_Hersteller_value=".encode("utf-8")):
                            html_string = open("../web/html/settings.html", "r").read()

                            if not admin:
                                html_string = html_string.replace("%anzeigezeit_Hersteller_value%",
                                                                  str(settings.SHOW_TIME))
                                html_string = html_string.replace("%STATUS2%",
                                                                  "<font color='red'>Aktualisierung fehlgeschlagen! "
                                                                  "Falsches Admin Passwort</font>")
                            elif data[i + 1].isdigit():
                                time = int(data[i + 1])
                                self.loc_db_mngr.setDelayTime("HERSTELLER", time)
                                settings.SHOW_PRODUCER_INFOS_TIME = time
                                html_string = html_string.replace("%anzeigezeit_Hersteller_value%",
                                                                  str(settings.SHOW_PRODUCER_INFOS_TIME))
                                html_string = html_string.replace("%STATUS2%",
                                                                  "<font color='green'>Erfolgreich aktualisiert!</font>"
                                                                  "")
                                log.info("> Aktualisiere Hersteller Informationen Anzeigezeit zu: {0} Sekunden.".
                                         format(settings.SHOW_PRODUCER_INFOS_TIME))
                            else:
                                html_string = html_string.replace("%anzeigezeit_Hersteller_value%",
                                                                  str(settings.SHOW_PRODUCER_INFOS_TIME))
                                html_string = html_string.replace("%STATUS2%",
                                                                  "<font color='red'>Aktualisierung fehlgeschlagen! "
                                                                  "Keine Zahl?</font>")
                            html_string = self.replaceVarsInSettingsHtml(html_string)

                        elif data[i].decode() == "changeAdvertiseTime_value":
                            # post_data.startswith("changeAdvertiseTime_value=".encode("utf-8")):
                            html_string = open("../web/html/settings.html", "r").read()

                            if not admin:
                                html_string = html_string.replace("%anzeigezeit_Hersteller_value%",
                                                                  str(settings.SHOW_TIME))
                                html_string = html_string.replace("%STATUS3%",
                                                                  "<font color='red'>Aktualisierung fehlgeschlagen! "
                                                                  "Falsches Admin Passwort</font>")
                            elif data[i + 1].isdigit():
                                time = int(data[i + 1])
                                self.loc_db_mngr.setDelayTime("CHANGE_ADVERTISE", time)
                                settings.CHANGE_ADVERTISE_TIME = time
                                print(time)
                                html_string = html_string.replace("%anzeigezeit_Hersteller_value%",
                                                                  str(settings.CHANGE_ADVERTISE_TIME))
                                html_string = html_string.replace("%STATUS3%",
                                                                  "<font color='green'>Erfolgreich aktualisiert!</font>"
                                                                  "")
                                log.info(
                                    "> Aktualisiere Wechselzeit zwischen Startseite und Werbung Seite zu: {0}"
                                    " Sekunden.".
                                    format(settings.CHANGE_ADVERTISE_TIME))
                            else:
                                html_string = html_string.replace("%anzeigezeit_Hersteller_value%",
                                                                  str(settings.CHANGE_ADVERTISE_TIME))
                                html_string = html_string.replace("%STATUS3%",
                                                                  "<font color='red'>Aktualisierung fehlgeschlagen! "
                                                                  "Keine Zahl?</font>")
                            html_string = self.replaceVarsInSettingsHtml(html_string)

                        elif data[i].decode() == "changePasswordNewPW_value":
                            # post_data.startswith("changeAdvertiseTime_value=".encode("utf-8")):
                            html_string = open("../web/html/settings.html", "r").read()

                            if not admin:
                                html_string = html_string.replace("%STATUS4%",
                                                                  "<font color='red'>Aktualisierung fehlgeschlagen! "
                                                                  "Falsches Admin Passwort</font>")
                            else:
                                self.loc_db_mngr.setPassword("ADMIN", data[i + 1].decode())
                                settings.clear_log_file_pw = data[i + 1].decode()

                                html_string = html_string.replace("%STATUS4%",
                                                                  "<font color='green'>Erfolgreich aktualisiert!</font>"
                                                                  "")
                                log.info("> Ändere das Admin Passwort")
                            html_string = self.replaceVarsInSettingsHtml(html_string)
                        else:
                            log.warning("> Unbekannter POST: {0}".format(str(post_data)))
                            html_string = open("../web/html/404.html", "r").read()
                            html_status = 404

            else:
                log.debug("> WARNUNG: Post Seite nicht gefunden: {0}".format(self.path))

                html_string = open("../web/html/404.html", "r").read()
                html_status = 404

            if html_string == "":
                log.warning("> Unbearbeiteter POST: {0}".format(str(post_data)))
                html_string = open("../web/html/404.html", "r").read()
                html_status = 404

            self.send_response(html_status)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

            # Write Funktion in eigenem try-catch statement, um Html-Fehler senden zu können, wenn im SQL Teil
            # etwas fehlschlägt!
            try:
                self.wfile.write(html_string.encode("utf-8"))
            except Exception as exc:
                log.warning("> Es ist ein Fehler im RequestHandler aufgetreten: write() failed: {0}".format(exc))
                self.loc_db_mngr = None
                return

        except Exception as exc:
            log.error("> Es ist ein Fehler im RequestHandler aufgetreten: {0}".format(exc))

            # Write Funktion in eigenem try-catch statement, um Html-Fehler senden zu können, wenn im SQL Teil
            # etwas fehlschlägt!
            try:
                self.send_error(500, "Ein unerwartetes Problem ist aufgetreten!")
            except Exception as exc:
                log.warning("> Es ist ein Fehler im RequestHandler aufgetreten: write() failed: {0}".format(exc))
                return

        self.loc_db_mngr = None
        return
