import datetime
import sqlite3
from sqlite3 import Error
import contextlib

import settings

import logging
from pathlib import Path

log = logging.getLogger(Path(__file__).name)


class LocalDataBaseManager:
    connection = None
    sql_create_table = """CREATE TABLE IF NOT EXISTS "scans" ( 
                                            "id" INTEGER, 
                                            "date" date NOT NULL, 
                                            "time" time NOT NULL, 
                                            "kArticle" integer NOT NULL, 
                                            "ean" integer NOT NULL, 
                                            "hersteller" TEXT, 
                                            PRIMARY KEY("id") 
                                        );"""

    sql_create_table2 = """CREATE TABLE IF NOT EXISTS times (
                                        name TEXT PRIMARY KEY,
                                        value integer NOT NULL
                                    );"""
    sql_create_table3 = """CREATE TABLE IF NOT EXISTS passwords (
                                            name TEXT PRIMARY KEY,
                                            value TEXT NOT NULL
                                        );"""

    def create_table(self):
        with contextlib.closing(self.connection.cursor()) as c:
            c.execute(self.sql_create_table)
            c.execute(self.sql_create_table2)
            c.execute(self.sql_create_table3)
            log.info("Erfolgreich mit lokaler SQL Lite Datenbank verbunden und Tables erstellt!")

    def updateConstants(self):
        d_time = self.getDelayTime("ARTIKEL")
        if d_time and d_time[0] > 1:
            settings.SHOW_TIME = d_time[0]
        d_time = self.getDelayTime("HERSTELLER")
        if d_time and d_time[0] > 1:
            settings.SHOW_PRODUCER_INFOS_TIME = d_time[0]
        d_time = self.getDelayTime("CHANGE_ADVERTISE")
        if d_time and d_time[0] > 1:
            settings.CHANGE_ADVERTISE_TIME = d_time[0]
        pw = self.getPassword("ADMIN")
        if pw:
            settings.clear_log_file_pw = pw[0]

    def disconnect(self):
        self.connection.close()
        self.connection = None

    def connect(self, file_path):
        try:
            if self.connection is not None:
                log.warning("WARNING: Try to connect, but already Connected!")
                return self.connection
            else:
                self.connection = sqlite3.connect(file_path)
        except Error as exc:
            log.critical("Konnte keine Verbindung zur lokalen SQL Lite Datenbank herstellen!")
            self.connection = None
            return None
        return self.connection

    def getDelayTime(self, name: str):
        with contextlib.closing(self.connection.cursor()) as cur:
            cur.execute("SELECT value FROM times WHERE name = ?", (name,))
            return cur.fetchone()

    def setDelayTime(self, name, value):
        with contextlib.closing(self.connection.cursor()) as cur:
            cur.execute("INSERT INTO times(name,value) VALUES(?,?) ON CONFLICT(name) DO UPDATE SET value = ?;",
                        (name, value, value))
            self.connection.commit()
            id_ = cur.lastrowid
        return id_

    def getPassword(self, name: str):
        with contextlib.closing(self.connection.cursor()) as cur:
            cur.execute("SELECT value FROM passwords WHERE name = ?", (name,))
            return cur.fetchone()

    def setPassword(self, name, value):
        with contextlib.closing(self.connection.cursor()) as cur:
            cur.execute("INSERT INTO passwords(name,value) VALUES(?,?) ON CONFLICT(name) DO UPDATE SET value = ?;",
                        (name, value, value))
            self.connection.commit()
            id_ = cur.lastrowid
        return id_

    def getTime(self, k_article, ean):
        with contextlib.closing(self.connection.cursor()) as cur:
            cur.execute(''' INSERT INTO scans(date,time,kArticle,ean)
                      VALUES(date('now','localtime'), time('now','localtime'),?,?) ''', (k_article, ean))
            self.connection.commit()
            id_ = cur.lastrowid
        return id_

    def get_all_scans(self):
        with contextlib.closing(self.connection.cursor()) as cur:
            cur.execute("SELECT * FROM scans")
            return cur.fetchall()

    def getRange(self, begin, count):
        with contextlib.closing(self.connection.cursor()) as cur:
            cur.execute("SELECT * FROM scans LIMIT ?, ?;", [begin, count])
            return cur.fetchall()

    def getItemCount(self):
        with contextlib.closing(self.connection.cursor()) as cur:
            cur.execute("SELECT COUNT(0) FROM scans")
            count = cur.fetchone()[0]
            if count is None:
                return 0
            else:
                return int(count)

    def count_scans_at_date(self, date: datetime.date):
        with contextlib.closing(self.connection.cursor()) as cur:
            cur.execute("SELECT COUNT(1) FROM scans WHERE date = ?", [date.isoformat()])
            return cur.fetchall()

    def count_scans_at_date_where_hersteller_is(self, date: datetime.date, hersteller: str):
        if hersteller == "Unbekannt":
            with contextlib.closing(self.connection.cursor()) as cur:
                cur.execute("SELECT COUNT(1) FROM scans WHERE date = ? AND hersteller is NULL",
                            (date.isoformat(),))
                return cur.fetchall()
        else:
            with contextlib.closing(self.connection.cursor()) as cur:
                cur.execute("SELECT COUNT(1) FROM scans WHERE date = ? AND hersteller = ?",
                            (date.isoformat(), hersteller))
                return cur.fetchall()

    def getHerstellerList(self):
        with contextlib.closing(self.connection.cursor()) as cur:
            cur.execute("SELECT DISTINCT hersteller FROM scans")
            return cur.fetchall()

    def add_new_scan(self, k_article, ean, hersteller):
        with contextlib.closing(self.connection.cursor()) as cur:
            if hersteller is not None and hersteller.cName != "":
                cur.execute(''' INSERT INTO scans(date,time,kArticle,ean,hersteller)
                            VALUES(date('now','localtime'), time('now','localtime'),?,?,?) ''',
                            (k_article, ean, hersteller.cName))
            else:
                cur.execute(''' INSERT INTO scans(date,time,kArticle,ean)
                        VALUES(date('now','localtime'), time('now','localtime'),?,?) ''', (k_article, ean))
            self.connection.commit()
            id_ = cur.lastrowid
        return id_

    def get_rating_by_k_article(self, k_article):
        with contextlib.closing(self.connection.cursor()) as cur:
            cur.execute("SELECT AVG(rating) FROM scans WHERE kArticle = ?", [k_article])
            return cur.fetchone()
