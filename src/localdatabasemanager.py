import datetime
import sqlite3
from sqlite3 import Error
import contextlib

import logging
from pathlib import Path
log = logging.getLogger(Path(__file__).name)


class LocalDataBaseManager:
    connection = None
    sql_create_table = """CREATE TABLE IF NOT EXISTS scans (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    date date NOT NULL,
                                    time time NOT NULL,
                                    kArticle integer NOT NULL,
                                    ean integer NOT NULL
                                    
                                );"""

    def create_table(self):
        with contextlib.closing(self.connection.cursor()) as c:
            c.execute(self.sql_create_table)
            log.info("Erfolgreich mit lokaler SQL Lite Datenbank verbunden und Tables erstellt!")

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

    def add_new_scan(self, k_article, ean):
        with contextlib.closing(self.connection.cursor()) as cur:
            cur.execute(''' INSERT INTO scans(date,time,kArticle,ean)
                      VALUES(date('now','localtime'), time('now','localtime'),?,?) ''', (k_article, ean))
            self.connection.commit()
            id_ = cur.lastrowid
        return id_

    def get_rating_by_k_article(self, k_article):
        with contextlib.closing(self.connection.cursor()) as cur:
            cur.execute("SELECT AVG(rating) FROM scans WHERE kArticle = ?", [k_article])
            return cur.fetchone()
