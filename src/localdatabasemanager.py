import datetime
import sqlite3
import contextlib

import constants as consts

import updater

import logging
from pathlib import Path

log = logging.getLogger(Path(__file__).name)

###################################
# ### EINSTELLUNG-S-VARIABLEN ### #
###################################

# Login settings
admin_pw: str = consts.web_admin_init_pw
ms_sql_server_login_data: () = ("test", "altinsystems")
ms_sql_database_mandant: str = "Mandant_1"

# Time settings
# Dauer der Zeit zwischen einem Wechsel der Warte-Anzeige in Sekunden
advertise_toggle_time: int = 30

# Dauer der Zeit, wie lange die Information zu einem Produkt angezeigt werden, in Sekunden
show_article_infos_time: int = 30

# Dauer der Zeit, wie lange die Information zum Hersteller angezeigt werden, in Sekunden
show_producer_infos_time: int = 20

# Dauer der Zeit, wie lange "Keine Informationen zu diesem Produkt gefunden" angezeigt wird, in Sekunden
show_nothing_found_time: int = 8

# IDK
item_count_on_web_server_list: int = 150
ms_sql_server_addr: () = ("home.obermui.de", 18769)
# auto shutdown time
auto_shutdown_time: (str, str) = ("-1", "-1")


#   SERVER NOTIFY UI -> GETS EDITED!!!!
want_reload_advertise_var: bool = False

want_reconnect_mssql: bool = False

sql_connection_state: (str, str) = "-1"


# Der LocalDataBaseManager läd und speichert u.a. sämtliche Einstellungen.
# Falls man zum Beispiel den Webserver von der GUI trennen möchte, kann man alle globalen Variablen zu lokalen ändern.
# Jedoch müssen dann in jeder GET und POST Methode alle Einstellungen neu geladen werden, was zu längeren Ladezeiten der
# Internetseiten führen kann.


class LocalDataBaseManager:
    connection: sqlite3.Connection = None
    isConnected: bool = False

    #############################################
    # ### SQL3 DB ANBINDUNG UND EINRICHTUNG ### #
    #############################################

    scans_table = """CREATE TABLE IF NOT EXISTS "scans" ( 
                                            "id" INTEGER, 
                                            "date" date NOT NULL, 
                                            "time" time NOT NULL, 
                                            "kArticle" integer NOT NULL, 
                                            "ean" integer NOT NULL, 
                                            "hersteller" TEXT, 
                                            "kategorie" TEXT, 
                                            PRIMARY KEY("id") 
                                        );"""

    times_table = """CREATE TABLE IF NOT EXISTS "numbers" (
                                        name TEXT PRIMARY KEY,
                                        value integer NOT NULL
                                    );"""

    passwords_table = """CREATE TABLE IF NOT EXISTS "logins" (
                                        "name" TEXT,
                                        "user" TEXT,
                                        "password" TEXT,
                                        PRIMARY KEY("name")
                                   );"""

    def create_table_ne(self):
        try:
            if self.isConnected:
                with contextlib.closing(self.connection.cursor()) as c:
                    c.execute(self.scans_table)
                    c.execute(self.times_table)
                    c.execute(self.passwords_table)
                    log.info("Erfolgreich mit lokaler SQL Lite Datenbank verbunden und Tables erstellt!")
        except Exception as e:
            log.critical("Das erstellen der Tabellen in der lokalen SQL Lite Datenbank ist fehlgeschlagen: {0}"
                         .format(e))
            return None
        return "SUCCESS"

    def disconnect(self):
        self.connection.close()
        self.isConnected = False

    def connect(self, file_path):
        try:
            if self.connection is not None:
                log.warning("WARNING: Try to connect, but already Connected!")
                return self.connection
            else:
                self.connection = sqlite3.connect(file_path)

        except sqlite3.Error as exc:
            log.critical("Die Verbindung mit der lokalen DB ist fehlgeschlagen: {0}".format(exc))
            return None

        self.isConnected = True
        return self.connection

    def exec_sql(self, sql, values=None, fetch_one: bool = True, commit: bool = False):
        # log.debug("exec_sql {0} [{1}] {2} {3}".format(sql, values, fetch_one, commit))
        if not self.isConnected:
            log.error('        localdb sql3 exec_sql failed ({0})[{1}]: {2}'.format(sql, values, "Not connected!"))
            return
        try:
            with contextlib.closing(self.connection.cursor()) as cur:
                if values:
                    cur.execute(sql, values)
                else:
                    cur.execute(sql)
                if commit:
                    self.connection.commit()
                    return "SUCCESS"
                else:
                    if fetch_one:
                        return cur.fetchone()
                    else:
                        return cur.fetchall()
        except Exception as exc:
            log.error('        localdb sql3 exec_sql failed ({0})[{1}]: {2}'.format(sql, values, exc))
            return None

    ###############################
    # ### Handle Scan Tabelle ### #
    ###############################

    def get_all_scans(self):
        return self.exec_sql("SELECT * FROM scans", None, False)

    def getRange(self, begin, count):
        return self.exec_sql("SELECT * FROM scans LIMIT ?, ?;", [begin, count], False)

    def getItemCount(self):
        count = self.exec_sql("SELECT COUNT(0) FROM scans")[0]
        if count:
            return int(count)
        return 0

    def count_scans_at_date_where(self, date: datetime.date, cond_table_name: str, cond_value: str) -> int:
        condition: str = ""
        # Wenn Gruppierung, füge extra Bedingung hinzu
        if cond_table_name is not None:
            if cond_value == "Unbekannt":
                condition = "AND {0} is NULL".format(cond_table_name)
            else:
                condition = "AND {0} = '{1}'".format(cond_table_name, cond_value)
        count = self.exec_sql("SELECT COUNT(1) FROM scans WHERE date = ? {0}".format(condition), (date.isoformat(),))
        if count is None:
            return 0
        else:
            return int(count[0])

    def getHerstellerList(self):
        return self.exec_sql("SELECT DISTINCT hersteller FROM scans", None, False)

    def getKategorieList(self):
        return self.exec_sql("SELECT DISTINCT kategorie FROM scans", None, False)

    def add_new_scan(self, k_article, ean, hersteller, kategorie):
        if hersteller is not None and hersteller.cName != "":
            return self.exec_sql(''' INSERT INTO scans(date,time,kArticle,ean,hersteller,kategorie)
                        VALUES(date('now','localtime'), time('now','localtime'),?,?,?,?) ''',
                                 (k_article, ean, hersteller.cName, kategorie), True, True)
        else:
            return self.exec_sql(''' INSERT INTO scans(date,time,kArticle,ean,kategorie)
                        VALUES(date('now','localtime'), time('now','localtime'),?,?,?) ''',
                                 (k_article, ean, kategorie), True, True)

    ####################
    # ### Settings ### #
    ####################

    def storeLogin(self, name: str, user: str, pw: str):
        return self.exec_sql("INSERT INTO logins(name, user, password) VALUES(?, ?, ?) ON CONFLICT(name)"
                             " DO UPDATE SET user = ?, password = ?;", (name, user, pw, user, pw), True, True)

    def storeNumber(self, name: str, value: int):
        return self.exec_sql("INSERT INTO numbers(name,value) VALUES(?,?) ON CONFLICT(name) DO UPDATE SET value = ?;",
                             (name, value, value), True, True)

    def rowExists(self, table, column, value):
        ret = self.exec_sql("SELECT EXISTS(SELECT 1 FROM {0} WHERE {1}=? LIMIT 1);".format(table, column), (value,))
        return bool(ret and int(ret[0]) > 0)

    def loadNumber(self, name: str, min_t: int, fallback: int):
        sql = "SELECT value FROM numbers WHERE name = ?"
        time = self.exec_sql(sql, (name,))
        if time and int(time[0]) > min_t:
            return int(time[0])
        if not self.rowExists("numbers", "name", name):
            if self.storeNumber(name, fallback):
                time = self.exec_sql(sql, (name,))
                if time and int(time[0]) > min_t:
                    log.debug("    Init Database ( Table numbers ) Number: {0}".format(name))
                    return int(time[0])
        log.warning("    load Number from local Db failed! Fallback to old value: {0}".format(fallback))
        return fallback

    def loadLogin(self, name: str, fallback: ()) -> ():
        sql = "SELECT user,password FROM logins WHERE name = ?"
        ret = self.exec_sql(sql, (name,))
        if ret:
            return ret
        if not self.rowExists("logins", "name", name):
            if self.storeLogin(name, fallback[0], fallback[1]):
                ret = self.exec_sql(sql, (name,))
                if ret:
                    log.debug("    Init Database ( logins ) Login_data: {0}".format(name))
                    return ret

        log.warning("    load Login Data from local Db failed! Fallback to old value: {0}".format(fallback))
        return fallback

    def loadAllSettings(self):
        # Login settings
        # Important: Make Tuple of size 2 from str as fallback and also convert result to one str
        global admin_pw
        global ms_sql_server_login_data
        global ms_sql_database_mandant
        global advertise_toggle_time
        global show_article_infos_time
        global show_producer_infos_time
        global show_nothing_found_time
        global item_count_on_web_server_list
        global ms_sql_server_addr
        global want_reload_advertise_var
        global auto_shutdown_time

        global want_reconnect_mssql
        global sql_connection_state

        admin_pw = self.loadLogin("ADMIN", ("", admin_pw))[1]
        ms_sql_server_login_data = self.loadLogin("MS-SQL-SERVER-LOGIN", ms_sql_server_login_data)
        ms_sql_database_mandant = self.loadLogin("MANDANT", (ms_sql_database_mandant, ""))[0]

        # Time settings
        advertise_toggle_time = self.loadNumber("CHANGE_ADVERTISE",  1, advertise_toggle_time)
        show_article_infos_time = self.loadNumber("ARTIKEL",       1, show_article_infos_time)
        show_producer_infos_time = self.loadNumber("HERSTELLER",  1, show_producer_infos_time)
        show_nothing_found_time = self.loadNumber("NOTHING-FOUND", 1, show_nothing_found_time)

        # Else
        item_count_on_web_server_list = self.loadNumber("WEB-TABLE-LENGTH", 1, item_count_on_web_server_list)
        ms_sql_server_addr = self.loadLogin("SERVER-ADDRESS", ms_sql_server_addr)
        want_reload_advertise_var = bool(self.loadNumber("WANT-RELOAD-ADVERTISE-LIST", -1,
                                                         int(want_reload_advertise_var)))
        auto_shutdown_time = self.loadLogin("AUTO_SHUTDOWN_TIME", auto_shutdown_time)

        sql_connection_state = self.loadLogin("MS_SQL_CONNECTION_STATE", sql_connection_state)
        want_reconnect_mssql = self.loadNumber("WANT-RECONNECT-MSSQL", -1, int(want_reconnect_mssql))

    def setAdminPw(self, new_value):
        global admin_pw
        if self.storeLogin("ADMIN", "", new_value):
            admin_pw = new_value
            return "SUCCESS"
        return None

    def setMS_SQL_LoginData(self, user, pw):
        global ms_sql_server_login_data
        if self.storeLogin("MS-SQL-SERVER-LOGIN", user, pw):
            ms_sql_server_login_data = (user, pw)
            return "SUCCESS"
        return None

    def setMS_SQL_Mandant(self, new_value):
        global ms_sql_database_mandant
        if self.storeLogin("MANDANT", new_value, ""):
            ms_sql_database_mandant = new_value
            return "SUCCESS"
        return None

    def setAdvertiseToggleTime(self, new_value):
        global advertise_toggle_time
        if self.storeNumber("CHANGE_ADVERTISE", new_value):
            advertise_toggle_time = new_value
            return "SUCCESS"
        return None

    def setArticleShowTime(self, new_value):
        global show_article_infos_time
        if self.storeNumber("ARTIKEL", new_value):
            show_article_infos_time = new_value
            return "SUCCESS"
        return None

    def setProducerShowTime(self, new_value):
        global show_producer_infos_time
        if self.storeNumber("HERSTELLER", new_value):
            show_producer_infos_time = new_value
            return "SUCCESS"
        return None

    def setNothingFoundPageShowTime(self, new_value):
        global show_nothing_found_time
        if self.storeNumber("NOTHING-FOUND", new_value):
            show_nothing_found_time = new_value
            return "SUCCESS"
        return None

    def setItemCountOnWebtable(self, new_value):
        global item_count_on_web_server_list
        if self.storeNumber("WEB-TABLE-LENGTH", new_value):
            item_count_on_web_server_list = new_value
            return "SUCCESS"
        return None

    def setMS_SQL_ServerAddr(self, ip: str, port: int):
        global ms_sql_server_addr
        if self.storeLogin("SERVER-ADDRESS", ip, str(port)):
            ms_sql_server_addr = (ip, port)
            return "SUCCESS"
        return None

    def setWantReloadAdvertiseList(self, value: bool):
        global want_reload_advertise_var
        if self.storeNumber("WANT-RELOAD-ADVERTISE-LIST", int(value)):
            want_reload_advertise_var = value
            return "SUCCESS"
        return None

    def setAutoShutdownTime(self, hour: str, minutes: str):
        global auto_shutdown_time
        if len(hour) == 1:
            hour = "0" + hour
        if len(minutes) == 1:
            minutes = "0" + minutes
        if self.storeLogin("AUTO_SHUTDOWN_TIME", hour, minutes):
            auto_shutdown_time = (hour, minutes)
            return "SUCCESS"
        return None

    def setWanReConnectMSSQL(self, value: bool):
        global want_reconnect_mssql
        if self.storeNumber("WANT-RECONNECT-MSSQL", int(value)):
            want_reconnect_mssql = value
            return "SUCCESS"
        return None

    def setMSSQLConnectionState(self, new_value):
        global sql_connection_state
        if self.storeLogin("MS_SQL_CONNECTION_STATE", new_value, ""):
            sql_connection_state = new_value
            return "SUCCESS"
        return None
    ####
    # Getter
    ####

    @staticmethod
    def getAdminPw():
        return admin_pw

    @staticmethod
    def getMS_SQL_LoginData():
        return ms_sql_server_login_data

    @staticmethod
    def getMS_SQL_Mandant():
        return ms_sql_database_mandant

    @staticmethod
    def getAdvertiseToggleTime():
        return advertise_toggle_time

    @staticmethod
    def getArticleShowTime():
        return show_article_infos_time

    @staticmethod
    def getProducerShowTime():
        return show_producer_infos_time

    @staticmethod
    def getNothingFoundPageShowTime():
        return show_nothing_found_time

    @staticmethod
    def getItemCountOnWebTable():
        return item_count_on_web_server_list

    @staticmethod
    def getMS_SQL_ServerAddr():
        return ms_sql_server_addr

    @staticmethod
    def checkWantReloadAdvertiseList() -> bool:
        return want_reload_advertise_var

    @staticmethod
    def getAutoShutdownTime() -> (str, str):
        return auto_shutdown_time

    @staticmethod
    def checkWanReConnectMSSQL():
        return want_reconnect_mssql

    @staticmethod
    def getMSSqlConnectionState():
        return sql_connection_state
