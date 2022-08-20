import calendar
import shutil
import random


from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta

import constants as consts
import localdatabasemanager

import logging
from pathlib import Path

log = logging.getLogger(Path(__file__).name)


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
                    html_bytes = self.getFileText(consts.log_file_path)

                else:
                    html_status, html_bytes = self.getPageNotFound()

            ####
            # Internetseiten
            ####
            elif sub_paths[1] == "html":

                if self.checkPathIsNotValid(sub_paths, 2):
                    html_status, html_bytes = self.getPageNotFound()

                elif sub_paths[2] == "wochenstatus.html":
                    html_bytes = self.getWochenStatusPage([["Alle Artikel"]], None)

                elif sub_paths[2] == "wochenstatus-kategorie.html":
                    html_bytes = self.getWochenStatusPage(self.loc_db_mngr.getKategorieList(), "kategorie")

                elif sub_paths[2] == "wochenstatus-hersteller.html":
                    html_bytes = self.getWochenStatusPage(self.loc_db_mngr.getHerstellerList(), "hersteller")

                elif sub_paths[2] == "monatsstatus.html":
                    html_bytes = self.getMonatsStatusPage([["Alle Artikel"]], None)

                elif sub_paths[2] == "monatsstatus-hersteller.html":
                    html_bytes = self.getMonatsStatusPage(self.loc_db_mngr.getKategorieList(), "kategorie")

                elif sub_paths[2] == "monatsstatus-kategorie.html":
                    html_bytes = self.getMonatsStatusPage(self.loc_db_mngr.getHerstellerList(), "hersteller")

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
        log.debug("> WARNUNG: (POST) Seite nicht gefunden: {0}".format(self.path))
        return 404, open("../web/html/404.html", "r").read().encode()

    @staticmethod
    def getRandomColor(i) -> str:
        x = random.randint(0, 255)
        y = random.randint(0, 255)
        z = random.randint(0, 255)
        if x+y+z > 600:
            x = 0
        return str(x) + ", " + str(y) + ", " + str(z)

    def getWochenStatusPage(self, group_list, name) -> bytes:
        html_bytes: bytes = self.getFileText("../web/html/wochenstatus-template.html")
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
            color = self.getRandomColor(i)

            replace_str += "{\r\n" \
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
        html_bytes: bytes = self.getFileText("../web/html/monatsstatus-template.html")
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
            color = self.getRandomColor(i)

            replace_str += "{\r\n" \
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
        html_bytes: bytes = self.getFileText("../web/html/jahresstatus-template.html")
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
            color = self.getRandomColor(i)
            replace_str += "{\r\n" \
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
        html_bytes: bytes
        content_type: str = "text/html"
        sub_paths = self.path.split("/")
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
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

            elif sub_paths[2] == "log.html":
                if "deleteLog" in data and "password" in data:
                    html_bytes = self.deleteLogPostRequest(data)
                else:
                    html_status, html_bytes = self.getPageNotFound()

            elif sub_paths[2] == "settings.html":
                html = self.getFileText("../web/html/settings.html")

                if "ReloadAdvertiseListButton" in data:
                    html_bytes = self.settingsReloadAdvertiseListPostRequest()

                elif "anzeigezeit_value" in data:
                    html_bytes = self.settingsUpdateShowTime(data, html)

                elif "anzeigezeit_Hersteller_value" in data:
                    html_bytes = self.settingsUpdateProducerShowTime(data, html)

                elif"changeAdvertiseTime_value" in data:
                    html_bytes = self.settingsUpdateAdvertiseToggleTime(data, html)

                elif "changePasswordNewPW_value" in data:
                    html_bytes = self.settingsChangePassword(data, html)

                else:
                    html_status, html_bytes = self.getPageNotFound()

            else:
                html_status, html_bytes = self.getPageNotFound()

            if len(html_bytes) == 0:
                html_status, html_bytes = self.getPageNotFound()

            ####
            # Send Headers
            ####
            self.send_response(html_status)
            self.send_header('Content-type', content_type)
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

    def deleteLogPostRequest(self, data) -> bytes:
        log.debug("> Try to clear/rename Logfile...")
        # Check if Password is correct
        if self.adminPasswordIsCorrect(data, "password"):
            if consts.log_file_delete_mode == "RENAME":
                shutil.copyfile(consts.log_file_path, consts.log_file_path.replace(".log", "") + "_backup_"
                                + datetime.now().strftime("%m-%d-%Y_%H-%M-%S") + ".log")
                log.info("    -> Logfile copied")

            fo = open(consts.log_file_path, "w")
            fo.truncate()
            fo.close()
            log.info("    -> (Old) Logfile deleted")
            return self.getLogPage()
        else:
            log.warning("   -> Clear/Delete Logfile failed: Wrong password: ".format(str(data)))
            return self.getFileText("../web/html/tabelle-falsches-pw.html")

    def adminPasswordIsCorrect(self, data, password_field: str):
        return password_field in data and data[data.index(password_field) + 1] == self.loc_db_mngr.getAdminPw()

    def settingsReloadAdvertiseListPostRequest(self) -> bytes:
        localdatabasemanager.want_reload_advertise = True
        log.info("> Want reload Advertise List...")
        return self.getSettingsPage()

    def settingsUpdateShowTime(self, data, html: bytes) -> bytes:
        status: str = "<font color='green'>Erfolgreich aktualisiert!</font>"
        value: str = data[data.index("anzeigezeit_value") + 1]

        if not self.adminPasswordIsCorrect(data, "adminPW"):
            status = "<font color='red'>Aktualisierung fehlgeschlagen! Falsches Passwort</font>"
            log.debug("Aktualisierung fehlgeschlagen! Falsches Passwort")

        elif value.isdigit():
            time = int(value)
            if self.loc_db_mngr.setArticleShowTime(time):
                log.info("> Aktualisiere Artikel Information Anzeigezeit zu: {0} Sekunden."
                         .format(self.loc_db_mngr.getArticleShowTime()))
            # else:
                # Error
        else:
            status = "<font color='red'>Aktualisierung fehlgeschlagen! Nur ganzzahlige Werte!</font>"
            log.debug("Aktualisierung fehlgeschlagen! Nur ganzzahlige Werte!")

        return self.replaceVarsInSettingsHtml(html.replace("<!--%STATUS1%-->".encode(), status.encode()))

    def settingsUpdateProducerShowTime(self, data, html: bytes) -> bytes:
        status: str = "<font color='green'>Erfolgreich aktualisiert!</font>"
        value: str = data[data.index("anzeigezeit_Hersteller_value") + 1]

        if not self.adminPasswordIsCorrect(data, "adminPW"):
            status = "<font color='red'>Aktualisierung fehlgeschlagen! Falsches Passwort</font>"
            log.debug("Aktualisierung fehlgeschlagen! Falsches Passwort")

        elif value.isdigit():
            time = int(value)
            if self.loc_db_mngr.setProducerShowTime(time):
                log.info("> Aktualisiere Hersteller Informationen Anzeigezeit zu: {0} Sekunden.".
                        format(self.loc_db_mngr.getProducerShowTime()))
            # else:
                # Error
        else:
            status = "<font color='red'>Aktualisierung fehlgeschlagen! Nur ganzzahlige Werte!</font>"
            log.debug("Aktualisierung fehlgeschlagen! Nur ganzzahlige Werte!")

        return self.replaceVarsInSettingsHtml(html.replace("<!--%STATUS2%-->".encode(), status.encode()))

    def settingsUpdateAdvertiseToggleTime(self, data, html: bytes) -> bytes:
        status: str = "<font color='green'>Erfolgreich aktualisiert!</font>"
        value: str = data[data.index("changeAdvertiseTime_value") + 1]

        if not self.adminPasswordIsCorrect(data, "adminPW"):
            status = "<font color='red'>Aktualisierung fehlgeschlagen! Falsches Passwort</font>"
            log.debug("Aktualisierung fehlgeschlagen! Falsches Passwort")

        elif value.isdigit():
            time = int(value)
            if self.loc_db_mngr.setAdvertiseToggleTime(time):
                log.info("> Aktualisiere Wechselzeit zwischen Startseite und Werbung Seite zu: {0} Sekunden.".
                        format(self.loc_db_mngr.getAdvertiseToggleTime()))
            # else:
                # Error
        else:
            status = "<font color='red'>Aktualisierung fehlgeschlagen! Nur ganzzahlige Werte!</font>"
            log.debug("Aktualisierung fehlgeschlagen! Nur ganzzahlige Werte!")

        return self.replaceVarsInSettingsHtml(html.replace("<!--%STATUS3%-->".encode(), status.encode()))

    def settingsChangePassword(self, data, html: bytes) -> bytes:
        status: str = "<font color='green'>Erfolgreich aktualisiert!</font>"
        value: str = data[data.index("changePasswordNewPW_value") + 1]

        if not self.adminPasswordIsCorrect(data, "adminPW"):
            status = "<font color='red'>Aktualisierung fehlgeschlagen! Falsches Passwort</font>"
            log.debug("Aktualisierung fehlgeschlagen! Falsches Passwort")
        else:
            if self.loc_db_mngr.setAdminPw(value):
                log.info("> Ändere das Admin Passwort")
            # else:
                # Error
        return self.replaceVarsInSettingsHtml(html.replace("<!--%STATUS4%-->".encode(), status.encode()))

    def replaceVarsInSettingsHtml(self, html: bytes) -> bytes:
        html = html.replace("%anzeigezeit_Hersteller_value%".encode(),
                            str(self.loc_db_mngr.getProducerShowTime()).encode())
        html = html.replace("%anzeigezeit_value%".encode(),
                            str(self.loc_db_mngr.getArticleShowTime()).encode())
        return html.replace("%changeAdvertiseTime_value%".encode(),
                            str(self.loc_db_mngr.getAdvertiseToggleTime()).encode())
