import calendar
import shutil
import random
import os
import string

import urllib.parse

from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta

import constants as consts
import localdatabasemanager

import logging
import logger
from pathlib import Path

from PySide2.QtWidgets import QApplication

log = logging.getLogger(Path(__file__).name)

# Liste aller angemeldeter User
g_logged_in_clients = []


# Klasse, die eine TCP Verbindung managed
class RequestHandler(BaseHTTPRequestHandler):
    # class RequestHandler(SimpleHTTPRequestHandler):
    # Objekte
    loc_db_mngr: localdatabasemanager.LocalDataBaseManager = None

    # HTTP Methode um Internetseitenquelltext zu bekommen:
    def do_GET(self):
        # Stelle Verbindung mit lokaler Datenbank her, um Statistiken auslesen zu können
        self.loc_db_mngr = localdatabasemanager.LocalDataBaseManager()
        if self.loc_db_mngr.connect(consts.local_db_path) is None:
            self.trySendError(500, "Konnte keine Verbindung mit der lokalen Datenbank herstellen!")
            return

        # Standard HTTP Sende-Status
        html_status: int = 200
        content_type: str = "text/html"
        sub_paths = self.path.split("/")
        html_bytes: bytes = "".encode()

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
                elif sub_paths[2] == "sidebar-style.css":
                    html_bytes = self.getFileText("../web/css/sidebar.css")

                else:
                    html_status, html_bytes = self.getPageNotFound()

            ####
            # Java Skript
            ####
            elif sub_paths[1] == "js":
                content_type = 'text/javascript'
                if self.checkPathIsNotValid(sub_paths, 2):
                    html_status, html_bytes = 404, "".encode()

                elif sub_paths[2] == "script.js":
                    html_bytes = self.getFileText("../web/scripts/script.js")

                elif sub_paths[2] == "checkLogin.js":
                    html_bytes = self.getFileText("../web/scripts/checkLogin.js")

                else:
                    html_status, html_bytes = self.getPageNotFound()

            ###
            # API
            ###
            elif sub_paths[1] == "api":
                content_type = 'text/plain'

                if self.checkPathIsNotValid(sub_paths, 2):
                    html_status, html_bytes = 404, "".encode()
                elif sub_paths[2] == "is_auth":
                    if self.checkForLoggedIn():
                        html_bytes = "true".encode()
                    else:
                        html_bytes = "false".encode()
                else:
                    html_status, html_bytes = 404, "".encode()
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

                elif sub_paths[2] == "background.jpg":
                    html_bytes = self.getFileBytes("../images/background.jpg")

                elif sub_paths[2] == "logo.jpg":
                    html_bytes = self.getFileBytes("../images/logo.jpg")

                elif sub_paths[2] == "icon-header.png":
                    html_bytes = self.getFileBytes("../images/icon-header.png")

                elif sub_paths[2] == "user-icon.jpeg":
                    html_bytes = self.getFileBytes("../images/user-icon.jpeg")

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
                    html_bytes = self.getFileText(consts.log_file_path)

                else:
                    html_status, html_bytes = self.getPageNotFound()

            ####
            # Internetseiten
            ####
            elif sub_paths[1] == "html":

                if self.checkPathIsNotValid(sub_paths, 2):
                    html_status, html_bytes = self.getPageNotFound()

                elif not self.checkForLoggedIn():
                    html_bytes = self.getFileText("../web/html/login.html")\
                        .replace("name=\"ziel-link\" value=\"/\"".encode(),
                                 ("name=\"ziel-link\" value=\"" + self.path + "\"").encode())

                elif sub_paths[2] == "logout.html":
                    cookies = SimpleCookie(self.headers.get('Cookie'))
                    login = cookies.get("LOGIN_ID")
                    print("VALUE:", login)
                    print("ALL:", g_logged_in_clients)
                    if login is not None:
                        for loginKey in g_logged_in_clients:
                            if len(loginKey) == 2:
                                if loginKey[0] == str(login.value):
                                    log.debug("CLIENT '{0}' hat sich abgemeldet.".format(loginKey))
                                    g_logged_in_clients.remove(loginKey)
                    html_bytes = self.getFileText("../web/html/logout.html")

                elif sub_paths[2] == "wochenstatus.html":
                    html_bytes = self.getWochenStatusPage([["Alle Artikel"]], None)

                elif sub_paths[2] == "wochenstatus-kategorie.html":
                    html_bytes = self.getWochenStatusPage(self.loc_db_mngr.getKategorieList(), "kategorie")

                elif sub_paths[2] == "wochenstatus-hersteller.html":
                    html_bytes = self.getWochenStatusPage(self.loc_db_mngr.getHerstellerList(), "hersteller")

                elif sub_paths[2] == "monatsstatus.html":
                    html_bytes = self.getMonatsStatusPage([["Alle Artikel"]], None)

                elif sub_paths[2] == "monatsstatus-hersteller.html":
                    html_bytes = self.getMonatsStatusPage(self.loc_db_mngr.getHerstellerList(), "hersteller")

                elif sub_paths[2] == "monatsstatus-kategorie.html":
                    html_bytes = self.getMonatsStatusPage(self.loc_db_mngr.getKategorieList(), "kategorie")

                elif sub_paths[2] == "jahresstatus.html":
                    html_bytes = self.getJahresStatusPage([["Alle Artikel"]], -1)

                elif sub_paths[2] == "jahresstatus-kategorie.html":
                    html_bytes = self.getJahresStatusPage(self.loc_db_mngr.getKategorieList(), 6)

                elif sub_paths[2] == "jahresstatus-hersteller.html":
                    html_bytes = self.getJahresStatusPage(self.loc_db_mngr.getHerstellerList(), 5)

                elif sub_paths[2] == "tabelle":
                    if self.checkPathIsNotValid(sub_paths, 3) or not sub_paths[3].isdigit():
                        html_status, html_bytes = self.getPageNotFound()

                    else:
                        html_bytes = self.getTabellenPage(sub_paths[3])

                elif sub_paths[2] == "settings.html":
                    html_bytes = self.getSettingsPage()

                elif sub_paths[2] == "log.html":
                    html_bytes = self.getLogPage()

                elif sub_paths[2] == "login.html":
                    html_bytes = self.getFileText("../web/html/login.html")

                elif sub_paths[2] == "about.html":
                    html_bytes = self.getFileText("../web/html/about.html")
                    html_bytes = html_bytes.replace("%version%".encode(),
                                                    logger.glob_updater.getCurrentVersion().encode())

                else:
                    html_status, html_bytes = self.getPageNotFound()

            else:
                html_status, html_bytes = self.getPageNotFound()

            if len(html_bytes) == 0:
                html_status, html_bytes = self.getPageNotFound()

            print("LOGGED IN:", self.checkForLoggedIn())

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
                self.loc_db_mngr.disconnect()
                return

        ####
        # Catch Code / SQL - Exceptions
        ####
        except Exception as exc:
            log.error("> Es ist ein Fehler im RequestHandler aufgetreten: {0}".format(exc))
            # Write Funktion in eigenem try-catch statement, um Html-Fehler senden zu können, wenn im SQL Teil
            # etwas fehlschlägt!#
            self.trySendError(500, "Ein unerwartetes Problem ist aufgetreten!")

        self.loc_db_mngr.disconnect()
        return

    @staticmethod
    def checkPathIsNotValid(subpaths, index) -> bool:
        return subpaths is None or len(subpaths) <= index or subpaths[index] is None or subpaths[index] == ""

    def checkForLoggedIn(self) -> bool:
        cookies = SimpleCookie(self.headers.get('Cookie'))
        login = cookies.get("LOGIN_ID")
        if login is None:
            return False
        else:
            for loginKey in g_logged_in_clients:
                if len(loginKey) == 2:
                    # Remove outdated client logins:
                    if (datetime.now() - loginKey[1]).total_seconds() / 60 > consts.auto_logout_time:
                        log.debug("  rm outdated-login: {0}".format(loginKey))
                        g_logged_in_clients.remove(loginKey)
                    elif loginKey[0] == str(login.value):
                        return True
                    else:
                        print(loginKey[0], "!=", login.value)
        return False

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

    @staticmethod
    def getRandomColor() -> str:
        x = random.randint(0, 255)
        y = random.randint(0, 255)
        z = random.randint(0, 255)
        if x + y + z > 600:
            x = 0
        return str(x) + ", " + str(y) + ", " + str(z)

    def getWochenStatusPage(self, group_list, name) -> bytes:
        html_bytes: bytes = self.getFileText("../web/html/statistik-template.html")
        html_bytes = html_bytes.replace("%smalstatistikname%".encode(), "wochenstatus".encode()).\
            replace("%BIGSTATISTIKNAME%".encode(), "Wochenstatistik".encode())\
            .replace("%DATA_LABEL_SET%".encode(), str("weekdaysList").encode())

        replace_str: str = ""
        weekday = datetime.today().weekday()
        for i in range(0, len(group_list)):

            if group_list[i] is None:
                continue
            elif group_list[i][0] is None:
                group = "Unbekannt"
            else:
                group = group_list[i][0]
            scan_list = [0] * 7

            for day in range(0, weekday + 1):
                current_day = datetime.today().date() - timedelta(days=day)
                scan_list[weekday - day] = self.loc_db_mngr.count_scans_at_date_where(current_day, name, group)

            if replace_str != "":
                replace_str += ","
            color = self.getRandomColor()

            replace_str += "{\r\n" \
                           + "borderRadius: 5,\r\n" \
                           + "                    label: '" + group + "',\r\n" \
                           + "                   data: " + str(scan_list) + ",\r\n" \
                           + "                   backgroundColor: [\r\n" \
                           + "                       'rgba(" + color + ", 0.5)'\r\n" \
                           + "                   ],\r\n" \
                           + "                  borderColor: [\r\n" \
                           + "                       'rgba(" + color + ", 1)'\r\n" \
                           + "                   ],\r\n" \
                           + "                   borderWidth: 2\r\n" \
                           + "              }"
        return html_bytes.replace("%DATA_DATA_SETS%".encode(), replace_str.encode())

    def getMonatsStatusPage(self, group_list, name) -> bytes:
        html_bytes: bytes = self.getFileText("../web/html/statistik-template.html")
        html_bytes = html_bytes.replace("%smalstatistikname%".encode(), "monatsstatus".encode())\
            .replace("%BIGSTATISTIKNAME%".encode(), "Monatsstatistik".encode())

        now = datetime.now()
        days_of_month = calendar.monthrange(now.year, now.month)[1]
        day_of_month = int(now.strftime("%d")) - 1
        replace_str: str = ""

        for i in range(0, len(group_list)):
            if group_list[i] is None:
                continue
            elif group_list[i][0] is None:
                group = "Unbekannt"
            else:
                group = group_list[i][0]

            scan_list = [0] * days_of_month
            for day in range(0, day_of_month + 1):
                current_day = datetime.today().date() - timedelta(days=day)
                scan_list[day_of_month - day] = self.loc_db_mngr.count_scans_at_date_where(current_day, name, group)

            if replace_str != "":
                replace_str += ","
            color = self.getRandomColor()

            replace_str += "{\r\n" \
                           + "borderRadius: 5,\r\n" \
                           + "                    label: '" + group + "',\r\n" \
                           + "                   data: " + str(scan_list) + ",\r\n" \
                           + "                   backgroundColor: [\r\n" \
                           + "                       'rgba(" + color + ", 0.5)'\r\n" \
                           + "                   ],\r\n" \
                           + "                  borderColor: [\r\n" \
                           + "                       'rgba(" + color + ", 1)'\r\n" \
                           + "                   ],\r\n" \
                           + "                   borderWidth: 2\r\n" \
                           + "              }"
        html_bytes = html_bytes.replace("%DATA_DATA_SETS%".encode(), replace_str.encode())
        label_list = [""] * days_of_month
        for i in range(0, days_of_month):
            label_list[i] = str(i + 1) + "."
        return html_bytes.replace("%DATA_LABEL_SET%".encode(), str(label_list).encode())

    def getJahresStatusPage(self, group_list, array_index) -> bytes:
        html_bytes: bytes = self.getFileText("../web/html/statistik-template.html")
        html_bytes = html_bytes.replace("%smalstatistikname%".encode(), "jahresstatus".encode()) \
            .replace("%BIGSTATISTIKNAME%".encode(), "Jahresstatistik".encode())\
            .replace("%DATA_LABEL_SET%".encode(), str("monthsList").encode())

        replace_str: str = ""
        current_year = datetime.now().year
        s_list = self.loc_db_mngr.get_all_scans()

        for i in range(0, len(group_list)):
            if group_list[i] is None:
                continue
            elif group_list[i][0] is None:
                group = "Unbekannt"
            else:
                group = group_list[i][0]

            scan_list = [0] * 12
            for m in range(1, 13):
                for scan in s_list:
                    scan_d = datetime.fromisoformat(scan[1])
                    if scan_d.year == current_year and scan_d.month == m:
                        if array_index == -1:
                            scan_list[m - 1] += 1
                        elif scan[array_index] is None and group == "Unbekannt":
                            scan_list[m - 1] += 1
                        elif scan[array_index] == group:
                            scan_list[m - 1] += 1

            if replace_str != "":
                replace_str += ","
            color = self.getRandomColor()
            replace_str += "{\r\n" \
                           + "borderRadius: 5,\r\n" \
                           + "                    label: '" + group + "',\r\n" \
                           + "                   data: " + str(scan_list) + ",\r\n" \
                           + "                   backgroundColor: [\r\n" \
                           + "                       'rgba(" + color + ", 0.5)'\r\n" \
                           + "                   ],\r\n" \
                           + "                  borderColor: [\r\n" \
                           + "                       'rgba(" + color + ", 1)'\r\n" \
                           + "                   ],\r\n" \
                           + "                   borderWidth: 2\r\n" \
                           + "              }"
        return html_bytes.replace("%DATA_DATA_SETS%".encode(), replace_str.encode())

    def getTabellenPage(self, page_num) -> bytes:
        html_string = self.getFileText("../web/html/tabelle.html").decode()
        page: int = int(page_num)
        page_count: int = int(self.loc_db_mngr.getItemCount() / self.loc_db_mngr.getItemCountOnWebTable())

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

        s_list = self.loc_db_mngr.getRange(self.loc_db_mngr.getItemCountOnWebTable() * page,
                                           self.loc_db_mngr.getItemCountOnWebTable())
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
        html = self.getFileText("../web/html/settings.html")
        return self.replaceVarsInSettingsHtml(html)

    @staticmethod
    def getLogPage() -> bytes:
        html_string = open("../web/html/log.html", "r").read()
        text: str = ""
        with open(consts.log_file_path, "r") as file:
            last: str = ""
            line_count: int = 0
            for line in file:
                line_count += 1
                if line_count > 50000:
                    text += "<h3>...</h3>"
                    text += "<h3> Logdatei zu groß! Downloade die Datei für mehr Informationen und leere diese oben!" \
                            "</h3>"
                    break
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

    def trySendError(self, status, msg):
        try:
            self.send_error(status, msg)
        except Exception as exc:
            log.warning("> Es ist ein Fehler im RequestHandler aufgetreten: write() failed: {0}".format(exc))
            return

    def do_POST(self):

        self.loc_db_mngr = localdatabasemanager.LocalDataBaseManager()
        if self.loc_db_mngr.connect(consts.local_db_path) is None:
            log.error("Konnte keine Verbindung mit der lokalen Datenbank herstellen!")
            self.trySendError(500, "Konnte keine Verbindung mit der lokalen Datenbank herstellen!")
            return

        # Standard HTTP Sende-Status
        html_status: int = 200
        html_bytes: bytes = "".encode()
        content_type: str = "text/html"
        sub_paths = self.path.split("/")
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        # Login Cookie data:
        cookie = SimpleCookie()
        do_send_cookie: bool = False

        if content_length <= 0:
            log.warning("POST without data!")
            self.trySendError(411, "Die Anfrage kann ohne ein „Content-Length“-Header-Feld nicht bearbeitet werden,"
                                   " bzw war 0.")
            return

        try:
            ####
            # Create List with Pairs of Data: [ Input1_Name, Input1_Value, Input2_Name, Input2_Value, ... ]
            ####
            data = self.getPosDataList(self.rfile.read(content_length).decode())

            # Check if Path is OK ( and not Startpage )
            if self.checkPathIsNotValid(sub_paths, 1) or sub_paths[1] != "html" \
                    or self.checkPathIsNotValid(sub_paths, 2):
                html_status, html_bytes = self.getPageNotFound()

            elif sub_paths[2] == "login.html":
                if "uname" in data and "psw" and "ziel-link" in data and \
                        self.loc_db_mngr.getAdminPw() == data[data.index("psw") + 1]:
                    # Wenn Passwort richtig ist, erzeuge Login ID für Cookie
                    letters = string.ascii_lowercase
                    result_str = ''.join(random.choice(letters) for i in range(12))
                    id_str = (datetime.now().strftime("%m.%d.%Y-%H:%M:%S") + result_str)
                    g_logged_in_clients.append((id_str, datetime.now()))
                    cookie['LOGIN_ID'] = id_str
                    # Aktiviere "Sende Cookie", damit Login Cookie später gesendet wird (Im "write header" Abschnitt)
                    do_send_cookie = True
                    # Lade HTML Seite zu erfolgreicher Anmeldung
                    html_bytes = self.getFileText("../web/html/loged_successfull.html")
                    # Wenn nicht redirect zurück auf Login (falls wiederholtes aufrufen der login Seite)
                    # → umleitung zu letzter seite ändern ( statt zu "/" )
                    if "/html/login.html" not in urllib.parse.unquote(data[data.index("ziel-link") + 1]):
                        html_bytes = html_bytes.replace(";url=/\">".encode(), (";url=" + urllib.parse.unquote(
                            data[data.index("ziel-link") + 1]) + "\">").encode())
                    log.debug("Login: {0}: Success".format(str((id_str, datetime.now()))))
                else:
                    log.debug("Login: Failed: Wrong Password")
                    html_bytes = self.getFileText("../web/html/login_failed.html")

            elif not self.checkForLoggedIn():
                html_bytes = self.getFileText("../web/html/login.html")

            elif sub_paths[2] == "log.html":
                if "deleteLog" in data:
                    html_bytes = self.deleteLogPostRequest()
                else:
                    html_status, html_bytes = self.getPageNotFound()

            elif sub_paths[2] == "settings.html":
                html_bytes = self.getFileText("../web/html/settings.html")

                if "ReloadAdvertiseListButton" in data:
                    html_bytes = self.settingsReloadAdvertiseListPostRequest(html_bytes)

                if "anzeigezeit_value" in data:
                    html_bytes = self.settingsUpdateShowTime(data, html_bytes)

                if "anzeigezeit_Hersteller_value" in data:
                    html_bytes = self.settingsUpdateProducerShowTime(data, html_bytes)

                if "changeAdvertiseTime_value" in data:
                    html_bytes = self.settingsUpdateAdvertiseToggleTime(data, html_bytes)

                if "changePasswordNewPW_value" and "changePasswordNewPW_CHECK_value" in data:
                    html_bytes = self.settingsChangePassword(data, html_bytes)

                if "changeNothingFoundTime_value" in data:
                    html_bytes = self.settingsUpdateNothingFoundTime(data, html_bytes)

                if "table_row_count_value" in data:
                    html_bytes = self.settingsUpdateTableRowCount(data, html_bytes)

                if "sql_server_port_value" in data and "sql_server_ip_value" in data:
                    html_bytes = self.settingsUpdateSQLServerAddress(data, html_bytes)

                if "sql_server_username_value" in data and "sql_server_password_value" in data:
                    html_bytes = self.settingsUpdateSQLServerLoginData(data, html_bytes)

                if "mandant_name" in data:
                    html_bytes = self.settingsUpdateMandant(data, html_bytes)

                if "update_button" in data:
                    html_bytes = self.settingsUpdate(data, html_bytes)

                if "neustarten_button" in data:
                    html_bytes = self.settings_reboot(data, html_bytes)

                if "shutdown_button" in data:
                    html_bytes = self.settings_shutdown(data, html_bytes)

                if "shutdownTime" in data:
                    html_bytes = self.settings_auto_shutdown(data, html_bytes)

                if "reconnect-mssql" in data:
                    html_bytes = self.settingsReConnectMSSQLDB(data, html_bytes)

                html_bytes = self.replaceVarsInSettingsHtml(html_bytes)

            else:
                html_status, html_bytes = self.getPageNotFound()

            if len(html_bytes) == 0:
                html_status, html_bytes = self.getPageNotFound()

            ####
            # Send Headers
            ####
            self.send_response(html_status)
            self.send_header('Content-type', content_type)

            if do_send_cookie:
                for morsel in cookie.values():
                    self.send_header("Set-Cookie", morsel.OutputString())

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
                self.loc_db_mngr.disconnect()
                return

        except Exception as exc:
            log.error("> Es ist ein Fehler im RequestHandler aufgetreten: {0}".format(exc))

            # Write Funktion in eigenem try-catch statement, um Html-Fehler senden zu können, wenn im SQL Teil
            # etwas fehlschlägt!
            self.trySendError(500, "Ein unerwartetes Problem ist aufgetreten!")

        self.loc_db_mngr.disconnect()
        return

    @staticmethod
    def getPosDataList(post_data) -> list:
        tmp_data = post_data.split("&")
        data: list = []
        for d in tmp_data:
            tmp = d.split("=")
            if len(tmp) == 0:
                continue
            if len(tmp) == 1:
                data += [tmp, ""]
            elif len(tmp) > 1:
                data += tmp[:2]
        return data

    def deleteLogPostRequest(self) -> bytes:
        log.debug("> Try to clear/rename Logfile...")
        if consts.log_file_delete_mode == "RENAME":
            shutil.copyfile(consts.log_file_path, consts.log_file_path.replace(".log", "") + "_backup_"
                            + datetime.now().strftime("%m-%d-%Y_%H-%M-%S") + ".log")
            log.info("    -> Logfile copied")

        fo = open(consts.log_file_path, "w")
        fo.truncate()
        fo.close()
        log.info("    -> (Old) Logfile deleted")
        return self.getLogPage()

    def adminPasswordIsCorrect(self, data, password_field: str):
        return password_field in data and data[data.index(password_field) + 1] == self.loc_db_mngr.getAdminPw()

    def settingsReloadAdvertiseListPostRequest(self, html: bytes) -> bytes:
        status: str = "<font color='green'>Lade Liste neu...!</font>"
        if self.loc_db_mngr.setWantReloadAdvertiseList(True) is None:
            status = "<font color='red'>Aktualisieren der Liste fehlgeschlagen!</font>"
        log.info("> Want reload Advertise List...")
        return html.replace("<!--%STATUS10%-->".encode(), status.encode())

    def settingsUpdateShowTime(self, data, html: bytes) -> bytes:
        status: str = "<font color='green'>Erfolgreich aktualisiert!</font>"
        value: str = data[data.index("anzeigezeit_value") + 1]

        if value.isdigit():
            time = int(value)
            if time != self.loc_db_mngr.getArticleShowTime():
                if self.loc_db_mngr.setArticleShowTime(time):
                    log.info("> Aktualisiere Artikel Information Anzeigezeit zu: {0} Sekunden."
                             .format(self.loc_db_mngr.getArticleShowTime()))
                else:
                    status = "<font color='red'>Ein unerwartetes Problem ist aufgetreten!</font>"
            else:
                status = ""
        else:
            status = "<font color='red'>Aktualisierung fehlgeschlagen! Nur ganzzahlige Werte!</font>"
            log.debug("Aktualisierung fehlgeschlagen! Nur ganzzahlige Werte!")

        return html.replace("<!--%STATUS1%-->".encode(), status.encode())

    def settingsUpdateProducerShowTime(self, data, html: bytes) -> bytes:
        status: str = "<font color='green'>Erfolgreich aktualisiert!</font>"
        value: str = data[data.index("anzeigezeit_Hersteller_value") + 1]

        if value.isdigit():
            time = int(value)
            if time != self.loc_db_mngr.getProducerShowTime():
                if self.loc_db_mngr.setProducerShowTime(time):
                    log.info("> Aktualisiere Hersteller Informationen Anzeigezeit zu: {0} Sekunden.".
                             format(self.loc_db_mngr.getProducerShowTime()))
                else:
                    status = "<font color='red'>Ein unerwartetes Problem ist aufgetreten!</font>"
            else:
                status = ""
        else:
            status = "<font color='red'>Aktualisierung fehlgeschlagen! Nur ganzzahlige Werte!</font>"
            log.debug("Aktualisierung fehlgeschlagen! Nur ganzzahlige Werte!")

        return html.replace("<!--%STATUS2%-->".encode(), status.encode())

    def settingsUpdateAdvertiseToggleTime(self, data, html: bytes) -> bytes:
        status: str = "<font color='green'>Erfolgreich aktualisiert!</font>"
        value: str = data[data.index("changeAdvertiseTime_value") + 1]

        if value.isdigit():
            time = int(value)
            if time != self.loc_db_mngr.getAdvertiseToggleTime():
                if self.loc_db_mngr.setAdvertiseToggleTime(time):
                    log.info("> Aktualisiere Wechselzeit zwischen Startseite und Werbung Seite zu: {0} Sekunden.".
                             format(self.loc_db_mngr.getAdvertiseToggleTime()))
                else:
                    status = "<font color='red'>Ein unerwartetes Problem ist aufgetreten!</font>"
            else:
                status = ""
        else:
            status = "<font color='red'>Aktualisierung fehlgeschlagen! Nur ganzzahlige Werte!</font>"
            log.debug("Aktualisierung fehlgeschlagen! Nur ganzzahlige Werte!")

        return html.replace("<!--%STATUS3%-->".encode(), status.encode())

    def settingsUpdateNothingFoundTime(self, data, html: bytes) -> bytes:
        status: str = "<font color='green'>Erfolgreich aktualisiert!</font>"
        value: str = data[data.index("changeNothingFoundTime_value") + 1]

        if value.isdigit():
            time = int(value)
            if time != self.loc_db_mngr.getNothingFoundPageShowTime():
                if self.loc_db_mngr.setNothingFoundPageShowTime(time):
                    log.info("> Aktualisiere NothingFoundPageShowTime zu: {0} Sekunden.".
                             format(self.loc_db_mngr.getNothingFoundPageShowTime()))
                else:
                    status = "<font color='red'>Ein unerwartetes Problem ist aufgetreten!</font>"
            else:
                status = ""
        else:
            status = "<font color='red'>Aktualisierung fehlgeschlagen! Nur ganzzahlige Werte!</font>"
            log.debug("Aktualisierung fehlgeschlagen! Nur ganzzahlige Werte!")

        return html.replace("<!--%STATUS5%-->".encode(), status.encode())

    def settingsUpdateTableRowCount(self, data, html: bytes) -> bytes:
        status: str = "<font color='green'>Erfolgreich aktualisiert!</font>"
        value: str = data[data.index("table_row_count_value") + 1]

        if value.isdigit():
            count = int(value)
            if count != self.loc_db_mngr.getItemCountOnWebTable():
                if self.loc_db_mngr.setItemCountOnWebtable(count):
                    log.info("> Aktualisiere ItemCountOnWebtable zu: {0}.".
                             format(self.loc_db_mngr.getItemCountOnWebTable()))
                else:
                    status = "<font color='red'>Ein unerwartetes Problem ist aufgetreten!</font>"
            else:
                status = ""
        else:
            status = "<font color='red'>Aktualisierung fehlgeschlagen! Nur ganzzahlige Werte!</font>"
            log.debug("Aktualisierung fehlgeschlagen! Nur ganzzahlige Werte!")

        return html.replace("<!--%STATUS6%-->".encode(), status.encode())

    def settingsUpdateSQLServerAddress(self, data, html: bytes) -> bytes:
        status: str = "<font color='green'>Erfolgreich aktualisiert!</font>"
        value_1: str = data[data.index("sql_server_ip_value") + 1]
        value_2: str = data[data.index("sql_server_port_value") + 1]

        if value_1 != "" and value_2.isdigit():
            if value_1 == self.loc_db_mngr.getMS_SQL_ServerAddr()[0] and int(value_2) == self.loc_db_mngr.getMS_SQL_ServerAddr()[1]:
                status = ""

            else:
                if self.loc_db_mngr.setMS_SQL_ServerAddr(value_1, int(value_2)):
                    log.info("> Aktualisiere settingsUpdateSQLServerAddress zu: {0}.".
                             format(self.loc_db_mngr.getMS_SQL_ServerAddr()))
                else:
                    status = "<font color='red'>Ein unerwartetes Problem ist aufgetreten!</font>"
        else:
            status = "<font color='red'>Aktualisierung fehlgeschlagen! Ungültige Eingabe!</font>"
            log.debug("Aktualisierung fehlgeschlagen! Ungültige Eingabe!")

        return html.replace("<!--%STATUS7%-->".encode(), status.encode())

    def settingsUpdateSQLServerLoginData(self, data, html: bytes) -> bytes:
        status: str = "<font color='green'>Erfolgreich aktualisiert!</font>"
        username: str = data[data.index("sql_server_username_value") + 1]
        password: str = data[data.index("sql_server_password_value") + 1]

        # use old pw if not set
        if password == "":
            password = self.loc_db_mngr.getMS_SQL_LoginData()[1]

        if username != "" and password != "":

            if username == self.loc_db_mngr.getMS_SQL_LoginData()[0] and password == self.loc_db_mngr.getMS_SQL_LoginData()[1]:
                status = ""
            else:
                if self.loc_db_mngr.setMS_SQL_LoginData(username, password):
                    log.info("> Aktualisiere MS_SQL_LoginData zu: {0}|{1}.".
                             format(self.loc_db_mngr.getMS_SQL_LoginData()[0], "*****"))
                else:
                    status = "<font color='red'>Ein unerwartetes Problem ist aufgetreten!</font>"
        else:
            status = "<font color='red'>Aktualisierung fehlgeschlagen! Ungültige Eingabe!</font>"
            log.debug("Aktualisierung fehlgeschlagen! Ungültige Eingabe!")

        return html.replace("<!--%STATUS8%-->".encode(), status.encode())

    def settingsUpdateMandant(self, data, html: bytes) -> bytes:
        status: str = "<font color='green'>Erfolgreich aktualisiert!</font>"
        value: str = data[data.index("mandant_name") + 1]

        if value != "":
            if value == self.loc_db_mngr.getMS_SQL_Mandant():
                status = ""
            else:
                if self.loc_db_mngr.setMS_SQL_Mandant(value):
                    log.info("> Aktualisiere mandant_name zu: {0}.".
                             format(self.loc_db_mngr.getMS_SQL_Mandant()))
                else:
                    status = "<font color='red'>Ein unerwartetes Problem ist aufgetreten!</font>"
        else:
            status = "<font color='red'>Aktualisierung fehlgeschlagen! Ungültige Eingabe!</font>"
            log.debug("Aktualisierung fehlgeschlagen! Ungültige Eingabe!")

        return html.replace("<!--%STATUS9%-->".encode(), status.encode())

    def settingsChangePassword(self, data, html: bytes) -> bytes:
        status: str = "<font color='green'>Erfolgreich aktualisiert!</font>"
        value: str = data[data.index("changePasswordNewPW_value") + 1]
        value2: str = data[data.index("changePasswordNewPW_CHECK_value") + 1]

        if not self.adminPasswordIsCorrect(data, "adminPW"):
            status = "<font color='red'>Aktualisierung fehlgeschlagen! Falsches Passwort</font>"
            log.debug("Aktualisierung fehlgeschlagen! Falsches Passwort")
        else:
            if value == "" or value2 == "":
                status = "<font color='red'>Aktualisierung des PWs fehlgeschlagen! Ungültige Eingabe!</font>"
                log.debug("Aktualisierung des PWs fehlgeschlagen! Ungültige Eingabe!")
            elif value != value2:
                status = "<font color='red'>Das neue Passwort stimmt nicht mit der Best&auml;tigung &uuml;berein!</font>"
            elif self.loc_db_mngr.setAdminPw(value):
                log.info("> Ändere das Admin Passwort")
            else:
                status = "<font color='red'>Ein unerwartetes Problem ist aufgetreten!</font>"

        return html.replace("<!--%STATUS4%-->".encode(), status.encode())

    @staticmethod
    def settingsUpdate(data, html: bytes) -> bytes:
        logger.glob_updater.startUpdate()
        return html

    @staticmethod
    def settings_shutdown(data, html: bytes) -> bytes:
        if os.system(consts.shutdown_command) == 0:
            status = "Fahre Computer herunter..."
            QApplication.quit()
        else:
            status = "Herunterfahren fehlgeschlagen!"
            log.debug("Herunterfahren fehlgeschlagen!")

        return html.replace("<!--%STATUS14%-->".encode(), ("<font color='red'>" + status + "</font>").encode())

    @staticmethod
    def settings_reboot(data, html: bytes) -> bytes:
        if os.system(consts.reboot_command) == 0:
            status = "Starte Computer neu..."
            QApplication.quit()
        else:
            status = "Neustarten fehlgeschlagen!"
            log.debug("Neustarten fehlgeschlagen!")

        return html.replace("<!--%STATUS13%-->".encode(), ("<font color='red'>" + status + "</font>").encode())

    def settings_auto_shutdown(self, data, html: bytes) -> bytes:
        status: str = "<font color='green'>Erfolgreich aktualisiert!</font>"
        value: [] = str(data[data.index("shutdownTime") + 1]).split("%3A")

        if str(data[data.index("shutdownTime") + 1]) == "-1"\
                or str(data[data.index("shutdownTime") + 1]) == "-1%3A-1":
            if self.loc_db_mngr.setAutoShutdownTime("-1", "-1"):
                status = "<font color='green'>Automatisches Herunterfahren deaktiviert.</font>"
                log.debug("Automatisches Herunterfahren deaktiviert.")
            else:
                status = "<font color='red'>Ein unerwartetes Problem ist aufgetreten!</font>"

        elif len(value) == 2 and value[0].isdigit() and int(value[0]) < 25 \
                and value[1].isdigit() and int(value[1]) < 60:
            if self.loc_db_mngr.setAutoShutdownTime(value[0], value[1]):
                log.info("> Aktualisiere shutdownTime zu: {0}.".
                         format(str(self.loc_db_mngr.getAutoShutdownTime())))
            else:
                status = "<font color='red'>Ein unerwartetes Problem ist aufgetreten!</font>"
        else:
            status = "<font color='red'>Aktualisierung fehlgeschlagen! Ungültige Eingabe!</font>"
            log.debug("Aktualisierung fehlgeschlagen! Ungültige Eingabe!")

        return html.replace("<!--%STATUS15%-->".encode(), status.encode())

    def settingsReConnectMSSQLDB(self, data, html: bytes) -> bytes:
        status: str = "<font color='green'>Versuche die Verbindung (neu) herzustellen...</font>"
        if self.loc_db_mngr.setWanReConnectMSSQL(True) is None:
            status = "<font color='red'>Verbindung (neu) herzustellen fehlgeschlagen!</font>"
        else:
            log.info("> Want reconnect ms sqldb...")
        return html.replace("<!--%STATUS16%-->".encode(), status.encode())

    @staticmethod
    def settingsShutDown():
        os.system('sudo shutdown now')

    @staticmethod
    def settingsReboot():
        os.system('sudo reboot')

    def replaceVarsInSettingsHtml(self, html: bytes) -> bytes:
        html = html.replace("%anzeigezeit_Hersteller_value%".encode(),
                            str(self.loc_db_mngr.getProducerShowTime()).encode())
        html = html.replace("%anzeigezeit_value%".encode(),
                            str(self.loc_db_mngr.getArticleShowTime()).encode())
        html = html.replace("%changeNothingFoundTime_value%".encode(),
                            str(self.loc_db_mngr.getNothingFoundPageShowTime()).encode())
        html = html.replace("%changeAdvertiseTime_value%".encode(),
                            str(self.loc_db_mngr.getAdvertiseToggleTime()).encode())

        html = html.replace("%table_row_count_value%".encode(),
                            str(self.loc_db_mngr.getItemCountOnWebTable()).encode())

        html = html.replace("%sql_server_ip_value%".encode(),
                            str(self.loc_db_mngr.getMS_SQL_ServerAddr()[0]).encode())
        html = html.replace("%sql_server_port_value%".encode(),
                            str(self.loc_db_mngr.getMS_SQL_ServerAddr()[1]).encode())

        html = html.replace("%sql_server_username_value%".encode(),
                            str(self.loc_db_mngr.getMS_SQL_LoginData()[0]).encode())

        html = html.replace("%programmVersion%".encode(),
                            str(logger.glob_updater.getCurrentVersion()).encode())

        html = html.replace("%mandant_name%".encode(),
                            str(self.loc_db_mngr.getMS_SQL_Mandant()).encode())
        html = html.replace("%shutdownTime%".encode(),
                            str(self.loc_db_mngr.getAutoShutdownTime()[0] + ":" +
                                self.loc_db_mngr.getAutoShutdownTime()[1]).encode())

        msg = ""
        if not logger.glob_updater.isUpdateAvailable():
            msg = "Sie verwenden die neuste Version: " + str(logger.glob_updater.getCurrentVersion())
            html = html.replace("><!--%disabled_update%-->".encode(), "hidden=\"true\">".encode())
        else:
            msg = "Es ist eine neuere Version ( " + str(logger.glob_updater.getNewestVersion()) + " ) verfügbar. " \
                                                "Derzeitige Version: " + str(logger.glob_updater.getCurrentVersion())
        if logger.glob_updater.state == logger.glob_updater.STATES.UPDATING:
            msg = "[ v" + str(logger.glob_updater.getCurrentVersion()) + " ] --> [ " + \
                  str(logger.glob_updater.getNewestVersion()) + " ]..."
            html = html.replace("><!--%disabled_update%-->".encode(), "hidden=\"true\">".encode())

        status = "<font color='orange'>" + logger.glob_updater.getStatus() + "</font>"

        html = html.replace("<!--%MSG1%-->".encode(), msg.encode())
        html = html.replace("<!--%STATUS12%-->".encode(), status.encode())
        # ms sql connection state
        html = html.replace("<!--%MSG2%-->".encode(), self.loc_db_mngr.getMSSqlConnectionState().encode())
        return html
