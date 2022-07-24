# Open Source Bibliothek für MS SQL
import pyodbc
import settings as s
import time

import logging
from pathlib import Path

log = logging.getLogger(Path(__file__).name)


# Klasse, die sich um den Datenaustausch mit dem MS SQL Server kümmert,
# um die Informationen zu einem Artikel über die EAN zu bekommen
class DataBaseManager:
    conn = None

    def __init__(self):
        return

    def disconnect(self):
        if self.conn:
            self.conn.close()

    def connect(self, ip: str = "PC-MARKUS", port: int = 1433, pw: str = "altinsystems",
                usr: str = "test", db: str = "Mandant_1"):
        for i in range(0, 10):
            try:
                ###
                # trusted_connection="yes", :
                #
                # Specifies whether a user connects through a user account by using either Kerberos [RFC4120] or
                # another platform-specific authentication as specified by the fIntSecurity field
                # The valid values are "Yes", "1", or empty string, which are equivalent, or "No".
                # If the value "No" is not specified, the value "Yes" is used.
                # If the value is "No", the UID and PWD keys have to be used to establish a connection with the
                # data source.
                ###

                # Verbinde mit MS SQl server unter verwendung des extern installierten ODBC Driver 18
                driver_names = pyodbc.drivers()
                if "ODBC Driver 18 for SQL Server" in driver_names:
                    print("Verwende Driver: ODBC Driver 18 for SQL Server...")
                    log.debug("Verwende Driver: ODBC Driver 18 for SQL Server...")

                    self.conn = pyodbc.connect(driver=s.SQL_DRIVER_USED_VERSION_MS_DRIVER, server=ip + "," +
                                                                                                  str(port),
                                               database=db,
                                               user=usr,
                                               password=pw,
                                               encrypt="no")
                    print("Erfolgreich mit MS SQL Server verbunden über ODBC Driver 18")
                    log.info("Erfolgreich mit MS SQL Server verbunden über ODBC Driver 18")

                    break

                elif "FreeTDS" in driver_names:
                    print("Verwende Driver: FreeTDS ", s.SQL_DRIVER_USED_VERSION_FreeTDS_VERSION, "...")
                    log.debug("Verwende Driver: FreeTDS {0} ...".format(s.SQL_DRIVER_USED_VERSION_FreeTDS_VERSION))

                    self.conn = pyodbc.connect('DRIVER={0}; SERVER={1}; PORT={2}; DATABASE={3}; UID={4}; PWD={5}; '
                                               'TDS_Version={6};'.format(s.SQL_DRIVER_USED_VERSION_FreeTDS,
                                                                         ip, port, db, usr, pw,
                                                                         s.SQL_DRIVER_USED_VERSION_FreeTDS_VERSION))
                    print("Erfolgreich mit MS SQL Server verbunden über FreeTDS Driver "
                          + s.SQL_DRIVER_USED_VERSION_FreeTDS_VERSION)
                    log.info("Erfolgreich mit MS SQL Server verbunden über FreeTDS Driver {0} ".format(
                        s.SQL_DRIVER_USED_VERSION_FreeTDS_VERSION))
                    break
                else:
                    print('Error: No suitable driver found. Cannot connect.')
                    log.critical('Error: No suitable driver found. Cannot connect.')
                    print("All installed driver: ", pyodbc.drivers())
                    log.debug("All installed driver: {0}".format(pyodbc.drivers()))
                    self.conn = None
                    break
            except Exception as exc:
                print('Connect to Database failed. ( Try: {0}/10 )'.format(i + 1), " Error: ", exc,
                      " Warte 1 Sekunde...")
                log.warning('Connect to Database failed. ( Try: {0}/10 ) Error: {1} - Warte 1 Sekunde...'
                            .format(i + 1, exc))

                time.sleep(1)
                self.conn = None

        return self.conn

    def get_header_list(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM ArtikelVerwaltung.vArtikelliste')

            columns = [column[0] for column in cursor.description]
            return columns
        except Exception as exc:
            print('get_header_list failed: {0}'.format(exc))
            log.error('get_header_list failed: {0}'.format(exc))
            return None

    def get_data_by_ean(self, ean):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM ArtikelVerwaltung.vArtikelliste WHERE vArtikelliste.EAN = ?", ean)
            row = cursor.fetchone()
            count = len(cursor.fetchall())
            if row is not None:
                count += 1
            if count != 1:
                print("WARNUNG: Keinen oder mehrere Einträge gefunden:", count)
                log.warning("WARNUNG: Keinen oder mehrere Einträge gefunden: {0} für Artikel EAN={1}"
                            .format(count, ean))
            return row

        except Exception as exc:
            print('get_data_by_ean: {0}'.format(exc))
            log.error('get_data_by_ean: {0}'.format(exc))
            return None

    def get_image_list(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                " SELECT  dbo.tBild.kBild, dbo.tArtikel.kArtikel, dbo.tBild.bBild FROM dbo.tBild, dbo.tArtikel,"
                " dbo.tArtikelbildPlattform"
                " WHERE dbo.tArtikel.kArtikel =  dbo.tArtikelbildPlattform.kArtikel "
                " AND dbo.tArtikelbildPlattform.kPlattform = 1"
                " AND dbo.tArtikelbildPlattform.kBild = dbo.tBild.kBild")
            return cursor.fetchall()

        except Exception as exc:
            print('get_image_list: {0}'.format(exc))
            log.error('get_image_list: {0}'.format(exc))
            return None

    def get_first_image(self, k_article):
        img_list = self.get_image_list()
        if img_list is not None:
            for img in img_list:
                if img.kArtikel == k_article:
                    return img.bBild
        return None

    def get_hersteller_infos(self, k_article):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT [dbo].[tHersteller].cName, [dbo].[tHersteller].cHomepage, "
                           "[dbo].[tHersteller].kHersteller FROM [dbo].[tHersteller], "
                           "[dbo].[tArtikel] "
                           "WHERE [dbo].[tHersteller].kHersteller = [dbo].[tArtikel].kHersteller AND [dbo].["
                           "tArtikel].kArtikel = ?", k_article)
            hersteller = cursor.fetchone()
            if hersteller is None:
                print("WARNUNG: Kein hersteller gefunden!")
                log.warning("WARNUNG: Kein hersteller gefunden: {0} ".format(k_article))
                return None
        except Exception as exc:
            print('get_hersteller_infos: {0}'.format(exc))
            log.error('get_hersteller_infos: {0}'.format(exc))
            return None
        return hersteller

    def get_hersteller_description(self, k_hersteller):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT cBeschreibung FROM [dbo].[tHerstellerSprache]"
                           " WHERE kHersteller = ?", k_hersteller)
            hersteller_desk = cursor.fetchone()
            if hersteller_desk is None:
                print("WARNUNG: Kein herstellerDescription gefunden!")
                log.warning("WARNUNG: Kein herstellerDescription gefunden: {0} ".format(k_hersteller))
                return None
        except Exception as exc:
            print('get_hersteller_description: {0}'.format(exc))
            log.error('get_hersteller_description: {0}'.format(exc))
            return None
        return hersteller_desk

    def get_mengen_preis(self, k_article):
        try:
            # Get: kArtikel, kMassEinheit, fMassMenge, kGrundPreisEinheit, fGrundpreisMenge
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT kArtikel,fVKNetto, kMassEinheit, fMassMenge, kGrundPreisEinheit, fGrundpreisMenge FROM "
                "dbo.tArtikel WHERE kArtikel = ?", k_article)
            article_data = cursor.fetchall()
            if len(article_data) != 1:
                print("Error keinen oder mehrere Einträge zu dem k_artikel: {0} gefunden: {1} Stück."
                      .format(k_article, len(article_data)))
                log.error("Error keinen oder mehrere Einträge zu dem k_artikel: {0} gefunden: {1} Stück."
                          .format(k_article, len(article_data)))
                return None

            # Get Mengeneinheit
            cursor.execute("SELECT * FROM dbo.tMassEinheit WHERE kMassEinheit = ?", article_data[0].kMassEinheit)
            mass_table_article = cursor.fetchone()
            if mass_table_article is None:
                return None

            cursor.execute("SELECT * FROM dbo.tMassEinheit WHERE kMassEinheit = ?", article_data[0].kGrundPreisEinheit)
            mass_table_einheit = cursor.fetchone()
            if mass_table_einheit is None:
                return None

            # Einheiten Namen
            cursor.execute("SELECT * FROM dbo.tMassEinheitSprache WHERE kMassEinheit = ?", article_data[0].kMassEinheit)
            article_einheit = cursor.fetchone()
            if article_einheit is None:
                return None

            cursor.execute("SELECT * FROM dbo.tMassEinheitSprache WHERE kMassEinheit = ?",
                           article_data[0].kGrundPreisEinheit)
            grundpreis_einheit = cursor.fetchone()
            if grundpreis_einheit is None:
                return None

            # Prevent div by 0
            if article_data[0].fGrundpreisMenge == 0:
                print("Error: article_data[0].fGrundpreisMenge == 0")
                return None

            # Wenn der Artikel in der Nenner Einheit gegeben ist -> In Tabelle 0 -> Zum Rechnen 1 benötigt!
            if mass_table_einheit.fBezugsMassEinheitFaktor == 0:
                mass_table_einheit.fBezugsMassEinheitFaktor = 1

            einheiten_multiplikator: float = float(mass_table_einheit.fBezugsMassEinheitFaktor
                                                   / mass_table_article.fBezugsMassEinheitFaktor)
            mengen_multiplikator: float = float(article_data[0].fGrundpreisMenge / article_data[0].fMassMenge)

            preis = float(article_data[0].fVKNetto)
            s_price = self.get_special_price(k_article)
            if s_price is not None:
                preis = float(s_price.fNettoPreis)

            mengen_preis: float = float(int(float(preis * einheiten_multiplikator
                                              * mengen_multiplikator * (1.0 + s.STEUERSATZ)) * 100) / 100)

            ret_val = str( float(int(float(article_data[0].fMassMenge) * 100)) / 100)  + " " + article_einheit.cName + " (" + \
                str( float( int(mengen_preis * 100)) / 100) + " € / " + str(
                float(int(article_data[0].fGrundpreisMenge * 100)) / 100) + " " + grundpreis_einheit.cName + ")"

        except Exception as exc:
            print('get_mengen_preis: {0}'.format(exc))
            log.error('get_mengen_preis: {0}'.format(exc))
            return None
        return ret_val

    def get_advertise_list(self, value):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT dbo.tArtikel.kArtikel, dbo.tMerkmalWertSprache.cMetaKeywords  FROM dbo.tArtikel, "
                           "dbo.tMerkmalWertSprache, dbo.tArtikelMerkmal "
                           # get tArtikelMerkmal.kMerkmal from tArtikelMerkmal from kArtikel
                           "WHERE dbo.tArtikel.kArtikel = dbo.tArtikelMerkmal.kArtikel "
                           # get tMerkmalWertSprache line with tArtikelMerkmal.kMerkmal
                           "AND dbo.tMerkmalWertSprache.kMerkmalWert = dbo.tArtikelMerkmal.kMerkmalWert "
                           # get all aktive kArtikel
                           "AND dbo.tMerkmalWertSprache.cMetaKeywords = ?", value)
            article_list = cursor.fetchall()
            if article_list is None:
                print("WARNUNG: Keine Werbung gefunden!")
                log.warning("WARNUNG: Keine Werbung gefunden!")
                return None
        except Exception as exc:
            print('get_advertise_list: {0}'.format(exc))
            log.error('get_advertise_list: {0}'.format(exc))
            return None
        return article_list

    def get_special_price(self, k_article):
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
            print('get_special_price: {0}'.format(exc))
            log.error('get_special_price: {0}'.format(exc))
            return None

    def getDataBykArtikel(self, kArtikel):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM dbo.tArtikel WHERE kArtikel = ?", kArtikel)
            # check if there are more than one special price?!
            # if cursor.fetchall() is not None...
            return cursor.fetchone()

        except Exception as exc:
            print('getDataBykArtikel: {0}'.format(exc))
            log.error('getDataBykArtikel: {0}'.format(exc))
            return None

    def get_article_description(self, k_article):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT cBeschreibung ,cKurzBeschreibung, cName FROM [dbo].[tArtikelBeschreibung] WHERE"
                           " dbo.tArtikelBeschreibung.kArtikel = ?", k_article)
            # check if there are more than one special price?!
            # if cursor.fetchall() is not None...
            return cursor.fetchone()

        except Exception as exc:
            print('get_article_description: {0}'.format(exc))
            log.error('get_article_description: {0}'.format(exc))
            return None
