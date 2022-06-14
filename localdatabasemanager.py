import datetime
import sqlite3
from sqlite3 import Error
import contextlib

class LocalDataBaseManager:
    connection = None
    sql_create_table = """CREATE TABLE IF NOT EXISTS scans (
                                    id integer PRIMARY KEY ,
                                    date date NOT NULL,
                                    time time NOT NULL,
                                    kArticle integer NOT NULL,
                                    ean integer NOT NULL
                                    
                                );"""

    def create_table(self):
        try:
            with contextlib.closing(self.connection.cursor()) as c:
                c.execute(self.sql_create_table)
        except Error as e:
            self.connection = None
            print(e)

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()
        self.connection = None

    def connect(self, file_path):
        if self.connection is not None:
            print("Already Connected")
            return False
        try:
            self.connection = sqlite3.connect(file_path)
            return True
        except Error as e:
            print(e)
            self.connection = None
            return False

    def get_all_scans(self):
        if self.connection is None:
            print("Not Connected")
            return
        else:
            with contextlib.closing(self.connection.cursor()) as cur:
                cur.execute("SELECT * FROM scans")
                return cur.fetchall()

    def count_scans_at_date(self, date:datetime.date):
        if self.connection is None:
            print("Not Connected")
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
            print("Not Connected")
            return

        if self.connection:
            sql = ''' INSERT INTO scans(date,time,kArticle,ean)
                          VALUES(date('now','localtime'), time('now','localtime'),?,?) '''
            with contextlib.closing(self.connection.cursor()) as cur:
                cur.execute(sql, (k_article, ean))
                self.connection.commit()
                id_ = cur.lastrowid
            return id_



