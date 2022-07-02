# Open Source Bibliothek für MS SQL
import pyodbc
import main

# Klasse, die sich um den Datenaustausch mit dem MS SQL Server kümmert,
# um die Informationen zu einem Artikel über die EAN zu bekommen
class DataBaseManager:
    conn = None

    def __init__(self):
        return

    def connect(self, ip: str = "PC-MARKUS", port: int = 1433, pw: str = "altinsystems",
                usr: str = "test", db: str = "Mandant_1"):
        try:
            ###
            # trusted_connection="yes", :
            #
            # Specifies whether a user connects through a user account by using either Kerberos [RFC4120] or
            # another platform-specific authentication as specified by the fIntSecurity field
            # The valid values are "Yes", "1", or empty string, which are equivalent, or "No".
            # If the value "No" is not specified, the value "Yes" is used.
            # If the value is "No", the UID and PWD keys have to be used to establish a connection with the data source.
            ###

            # Verbinde mit MS SQl server unter verwendung des extern installierten ODBC Driver 18
            driver_names = pyodbc.drivers()
            if "ODBC Driver 18 for SQL Server" in driver_names:
                self.conn = pyodbc.connect(driver=main.SQL_DRIVER_USED_VERSION_MS_DRIVER, server=ip + "," + str(port),
                                           database=db,
                                           user=usr,
                                           password=pw,
                                           encrypt="no")
            elif "FreeTDS" in driver_names:
                self.conn = pyodbc.connect('DRIVER={0}; SERVER={1}; PORT={2}; DATABASE={3}; UID={4}; PWD={5}; '
                                           'TDS_Version={6};'.format(main.SQL_DRIVER_USED_VERSION_FreeTDS,
                                                                     ip, port, db,usr, pw,
                                                                     main.SQL_DRIVER_USED_VERSION_FreeTDS_VERSION))
                ###
                # DRIVER = {FreeTDS};
                #             SERVER = server.com;
                #             PORT = 1433;
                #             DATABASE = dbname;
                #             UID = user;
                #             PWD = password;
                #             TDS_Version = 7.3;
                ###
            else:
                print('Error: No suitable driver found. Cannot connect.')
                print("All installed driver: ", pyodbc.drivers())
                self.conn = None
        except Exception as exc:
            print('critical error occurred: {0}. Please save your data and restart application'.format(exc))
            self.conn = None

        return self.conn

    def get_header_list(self):
        if self.conn is None:
            print("ERROR: Not Connected!")
            return None

        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM ArtikelVerwaltung.vArtikelliste')

            columns = [column[0] for column in cursor.description]
            return columns
        except Exception as exc:
            print('critical error occurred: {0}. Please save your data and restart application'.format(exc))
            return None

    def get_data_by_ean(self, ean):
        if self.conn is None:
            print("ERROR: Not Connected!")
            return None

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM ArtikelVerwaltung.vArtikelliste WHERE vArtikelliste.EAN = ?", ean)
            row = cursor.fetchone()
            count = len(cursor.fetchall())
            if row is not None:
                count += 1
            if count != 1:
                print("WARNUNG: Keinen oder mehrere Einträge gefunden:", count)
            return row

        except Exception as exc:
            print('critical error occurred: {0}. Please save your data and restart application'.format(exc))
            return None

    def p_all(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM ArtikelVerwaltung.vArtikelliste')
        columns = [column[0] for column in cursor.description]
        for column in columns:
            print(column)
        for row in cursor:
            print('row = %r' % (row,))

    def get_image_list(self):
        if self.conn is None:
            print("ERROR: Not Connected!")
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                " SELECT  dbo.tBild.kBild , dbo.tArtikel.kArtikel, dbo.tBild.bBild   FROM dbo.tBild, dbo.tArtikel,"
                " dbo.tArtikelbildPlattform"
                " WHERE dbo.tArtikel.kArtikel =  dbo.tArtikelbildPlattform.kArtikel "
                " AND  dbo.tArtikelbildPlattform.kPlattform = 1"
                " AND dbo.tArtikelbildPlattform.kBild = dbo.tBild.kBild")
            return cursor.fetchall()

        except Exception as exc:
            print('critical error occurred: {0}. Please save your data and restart application'.format(exc))
            return None

    def get_first_image(self, k_article):
        img_list = self.get_image_list()
        for img in img_list:
            if img.kArtikel == k_article:
                return img.bBild
        return None

    def get_special_price(self, k_article):
        if self.conn is None:
            print("ERROR: Not Connected!")
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT fNettoPreis, dEnde FROM [DbeS].[vArtikelSonderpreis] as sp WHERE sp.kArtikel = ?"
                           " AND sp.cAktiv = 'Y'"
                           " AND sp.dStart < GETDATE()"
                           " AND sp.kKundenGruppe = 1", k_article)
            # check if there are more than one special price?!
            # if cursor.fetchall() is not None...
            return cursor.fetchone()

        except Exception as exc:
            print('critical error occurred: {0}. Please save your data and restart application'.format(exc))
            return None

    def get_article_description(self, k_article):
        if self.conn is None:
            print("ERROR: Not Connected!")
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT cBeschreibung ,cKurzBeschreibung ,cUrlPfad FROM [dbo].[tArtikelBeschreibung] WHERE"
                           " dbo.tArtikelBeschreibung.kArtikel = ?", k_article)
            # check if there are more than one special price?!
            # if cursor.fetchall() is not None...
            return cursor.fetchone()

        except Exception as exc:
            print('critical error occurred: {0}. Please save your data and restart application'.format(exc))
            return None
