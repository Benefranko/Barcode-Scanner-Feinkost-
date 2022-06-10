import pyodbc


class DataBaseManager:
    cnxn = None

    def __init__(self):
        # cnxn = pyodbc.connect("DRIVER={ODBC Driver 18 for SQL Server};"
        #                      "Server=PC-MARKUS;"
        #                      "Database=PC-MARKUS;"
        #                      "Trusted_Connection=yes;"
        #                      "uid=test;pwd=altinsystems;")
        return

    def connect(self, ip="PC-MARKUS", port=None, user="test", pw="altinsystems", db="Mandant_1"):
        self.cnxn = pyodbc.connect(driver='{ODBC Driver 18 for SQL Server}', host=ip, database=db,
                                   trusted_connection="yes", user=user, password=pw, encrypt="no")
        return

    def get_ka(self):
        if self.cnxn is None:
            print("ERROR: Not Connected!")
            return

        cursor = self.cnxn.cursor()
        cursor.execute('SELECT * FROM ArtikelVerwaltung.vArtikelliste')

        for row in cursor:
            print('row = %r' % (row,))

        columns = [column[0] for column in cursor.description]

        for column in columns:
            print(column)

# kArtikel kStueckliste kVaterArtikel kArtikelForKategorieArtikel Artikelnummer Sortiernummer Artikelname Einheit EAN
# Herkunftsland UNNUmmer cHAN Gefahrennummer ISBN ASIN TaricCode UPC Hersteller Lieferstatus Breite Hoehe Laenge
# Erstelldatum
