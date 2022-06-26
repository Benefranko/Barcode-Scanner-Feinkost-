import datetime
import sqlite3
from sqlite3 import Error
import contextlib


#

class LocalDataBaseManager:
    connection = None
    sql_create_table = """CREATE TABLE IF NOT EXISTS scans (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    date date NOT NULL,
                                    time time NOT NULL,
                                    kArticle integer NOT NULL,
                                    ean integer NOT NULL
                                    
                                );"""
    sql_create_table2 = """CREATE TABLE IF NOT EXISTS ratings (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        date date NOT NULL,
                                        time time NOT NULL,
                                        kArticle integer NOT NULL,
                                        ean integer NOT NULL,
                                        rating float NOT NULL,
                                        comment string
                                    );"""

    def create_table(self):
        try:
            with contextlib.closing(self.connection.cursor()) as c:
                c.execute(self.sql_create_table)
            with contextlib.closing(self.connection.cursor()) as c:
                c.execute(self.sql_create_table2)
        except Error as e:
            self.connection = None
            print(e)

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()
        self.connection = None

    def connect(self, file_path):
        try:
            if self.connection is not None:
                print("WARNING: Already Connected")
            else:
                self.connection = sqlite3.connect(file_path)
            return self.connection
        except Error as exc:
            print('critical error occurred: {0}. Please save your data and restart application'.format(exc))
            self.connection = None
            return None

    def get_all_scans(self):
        if self.connection is None:
            print("ERROR: Nicht mit lokaler Datenbank verbunden!")
            return
        else:
            with contextlib.closing(self.connection.cursor()) as cur:
                cur.execute("SELECT * FROM scans")
                return cur.fetchall()

    def getRange(self, begin, count):
        if self.connection is None:
            print("ERROR: Nicht mit lokaler Datenbank verbunden!")
            return
        else:
            with contextlib.closing(self.connection.cursor()) as cur:
                cur.execute("SELECT * FROM scans LIMIT ?, ?;", [begin, count])
                return cur.fetchall()

    def count_scans_at_date(self, date: datetime.date):
        if self.connection is None:
            print("ERROR: Nicht mit lokaler Datenbank verbunden!")
            return
        else:
            with contextlib.closing(self.connection.cursor()) as cur:
                cur.execute("SELECT COUNT(1) FROM scans WHERE date = ?", [date.isoformat()])
                return cur.fetchall()

    def add_new_scan(self, k_article, ean):
        """
           Create a new scan into the scans table
           :param k_article:
           :param ean:
           :return: scan id
        """
        if self.connection is None:
            print("ERROR: Nicht mit lokaler Datenbank verbunden!")
            return

        if self.connection:
            sql = ''' INSERT INTO scans(date,time,kArticle,ean)
                          VALUES(date('now','localtime'), time('now','localtime'),?,?) '''
            with contextlib.closing(self.connection.cursor()) as cur:
                cur.execute(sql, (k_article, ean))
                self.connection.commit()
                id_ = cur.lastrowid
            return id_

    def add_rating(self, k_article, ean, rating, msg):
        if self.connection is None:
            print("ERROR: Nicht mit lokaler Datenbank verbunden!")
            return

        if self.connection:
            sql = ''' INSERT INTO ratings(date,time,kArticle,ean,rating,comment)
                          VALUES(date('now','localtime'), time('now','localtime'),?,?,?,?) '''
            with contextlib.closing(self.connection.cursor()) as cur:
                cur.execute(sql, (k_article, ean, rating, msg))
                self.connection.commit()
                id_ = cur.lastrowid
            return id_

    def get_rating_by_k_article(self, k_article):
        if self.connection is None:
            print("ERROR: Nicht mit lokaler Datenbank verbunden!")
            return
        else:
            with contextlib.closing(self.connection.cursor()) as cur:
                cur.execute("SELECT AVG(rating) FROM scans WHERE kArticle = ?", [k_article])
                return cur.fetchone()
