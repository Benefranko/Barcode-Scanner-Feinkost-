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

    @staticmethod
    def roundToStr(num: float) -> str:
        ret: str = str(round(num, 2))
        splits = ret.split(".")

        if str == "":
            print("WARNING: ROUND FAILED: {0} -> {1}".format(num, ret))
            log.warning("WARNING: ROUND FAILED: {0} -> {1}".format(num, ret))
            return "0.00"
        elif len(splits) == 0 or len(splits[1]) == 0:
            return ret + ".00"
        elif len(splits[1]) == 1:
            return ret + "0"
        elif len(splits[1]) == 2:
            return ret
        else:
            return "0.00"

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

                    self.conn = pyodbc.connect(driver=s.SQL_DRIVER_USED_VERSION_MS_DRIVER, server=ip + "," + str(port),
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

    def exec_sql(self, sql, value, fetch_one: bool = True):
        try:
            cursor = self.conn.cursor()
            if value:
                cursor.execute(sql, value)
            else:
                cursor.execute(sql)
            if fetch_one:
                return cursor.fetchone()
            else:
                return cursor.fetchall()
        except Exception as exc:
            print('exec_sql failed ({0})[{1}]: {2}'.format(sql, value, exc))
            log.error('exec_sql failed ({0})[{1}]: {2}'.format(sql, value, exc))
            return None

    # AUF FEHLER NOCH CHECKEN !!
    def getSteuerSatz(self, steuerklasse) -> float:
        steuersatz = self.exec_sql('SELECT fSteuersatz FROM [Mandant_1].[dbo].[tSteuersatz]'
                                   ' WHERE fSteuersatz != 0.0 AND kSteuerklasse = ?', steuerklasse, True)
        if steuersatz:
            return float(steuersatz.fSteuersatz) / 100.0
        else:
            print('getSteuerSatz failed!')
            log.error('getSteuerSatz!')
            return -1.0

    def getDataByBarcode(self, c_barcode):
        return self.exec_sql("SELECT * FROM dbo.tArtikel WHERE cBarcode = ?", c_barcode, True)

    def getDataBykArtikel(self, k_artikel):
        return self.exec_sql("SELECT * FROM dbo.tArtikel WHERE kArtikel = ?", k_artikel, True)

    def getImageList(self):
        return self.exec_sql(" SELECT  dbo.tBild.kBild, dbo.tArtikel.kArtikel, dbo.tBild.bBild"
                             " FROM dbo.tBild, dbo.tArtikel, dbo.tArtikelbildPlattform"
                             " WHERE dbo.tArtikel.kArtikel = dbo.tArtikelbildPlattform.kArtikel "
                             " AND dbo.tArtikelbildPlattform.kPlattform = 1"
                             " AND dbo.tArtikelbildPlattform.kBild = dbo.tBild.kBild", None, False)

    def getFirstImage(self, k_article):
        img_list = self.getImageList()
        if img_list is not None:
            for img in img_list:
                if img.kArtikel == k_article:
                    return img.bBild
        return None

    def getHerstellerInfos(self, k_article):
        return self.exec_sql("SELECT [dbo].[tHersteller].cName, [dbo].[tHersteller].cHomepage, "
                             "[dbo].[tHersteller].kHersteller FROM [dbo].[tHersteller], [dbo].[tArtikel] "
                             "WHERE [dbo].[tHersteller].kHersteller = [dbo].[tArtikel].kHersteller AND [dbo].["
                             "tArtikel].kArtikel = ?", k_article)

    def getHerstellerDescription(self, k_hersteller):
        return self.exec_sql("SELECT cBeschreibung FROM [dbo].[tHerstellerSprache]"
                             " WHERE kHersteller = ?", k_hersteller)

    def getMengenPreisStr(self, k_article):
        data = self.getDataBykArtikel(k_article)
        if data is None:
            print("Error keinen Eintrag zu dem k_artikel: {0} gefunden.".format(k_article))
            log.warning("Error keinen Eintrag zu dem k_artikel: {0} gefunden.".format(k_article))
            return None

            # Get Mengeneinheit
        if data.kMassEinheit == 0:
            print("WARNUNG: kMassEinheit nicht festgelegt: k_artikel: {0}. -> Kann keinen Grundpreis erzeugen".
                  format(k_article))
            log.warning("WARNUNG: kMassEinheit nicht festgelegt: k_artikel: {0}. -> Kann keinen Grundpreis erzeugen".
                        format(k_article))
            return None
        mass_table_article = self.exec_sql("SELECT * FROM dbo.tMassEinheit WHERE kMassEinheit = ?", data.kMassEinheit)
        if mass_table_article is None:
            return None

        mass_table_einheit = self.exec_sql("SELECT * FROM dbo.tMassEinheit WHERE kMassEinheit = ?",
                                           data.kGrundPreisEinheit)
        if mass_table_einheit is None:
            # error
            return None

            # Einheiten Namen
        article_einheit = self.exec_sql("SELECT * FROM dbo.tMassEinheitSprache WHERE kMassEinheit = ?",
                                        data.kMassEinheit)
        if article_einheit is None:
            # error
            return None

        grundpreis_einheit = self.exec_sql("SELECT * FROM dbo.tMassEinheitSprache WHERE kMassEinheit = ?",
                                           data.kGrundPreisEinheit)

        steuersatz = self.getSteuerSatz(data.kSteuerklasse)
        if steuersatz == -1:
            # error
            return None

        if grundpreis_einheit is None:
            # error
            return None

        # Prevent div by 0
        if data.fMassMenge == 0:
            print("Error: data.fMassMenge == 0")
            return None

        if mass_table_article.fBezugsMassEinheitFaktor == 0:
            print("Error: mass_table_article.fBezugsMassEinheitFaktor == 0")
            return None

        # Wenn der Artikel in der Nenner Einheit gegeben ist -> In Tabelle 0 -> Zum Rechnen 1 benötigt!
        mass_bezugs_faktor = mass_table_einheit.fBezugsMassEinheitFaktor
        if mass_bezugs_faktor == 0:
            mass_bezugs_faktor = 1

        einheiten_multiplikator: float = float( mass_bezugs_faktor / mass_table_article.fBezugsMassEinheitFaktor )
        mengen_multiplikator: float = float(data.fGrundpreisMenge / data.fMassMenge)

        preis = float(data.fVKNetto)
        s_price = self.getSpecialPrice(k_article)
        if s_price is not None:
            preis = float(s_price.fNettoPreis)

        mengen_preis: float = float(preis * einheiten_multiplikator * mengen_multiplikator * (1.0 + steuersatz))

        return self.roundToStr(float(data.fMassMenge)) + " " + article_einheit.cName + " (" + \
            self.roundToStr(mengen_preis) + " € / " + self.roundToStr(float(data.fGrundpreisMenge)) + " " + \
            grundpreis_einheit.cName + ")"

    def getAdvertiseList(self, value):
        return self.exec_sql("SELECT dbo.tArtikel.kArtikel, dbo.tMerkmalWertSprache.cMetaKeywords"
                             " FROM dbo.tArtikel, dbo.tMerkmalWertSprache, dbo.tArtikelMerkmal "
                             # get tArtikelMerkmal.kMerkmal from tArtikelMerkmal from kArtikel
                             "WHERE dbo.tArtikel.kArtikel = dbo.tArtikelMerkmal.kArtikel "
                             # get tMerkmalWertSprache line with tArtikelMerkmal.kMerkmal
                             "AND dbo.tMerkmalWertSprache.kMerkmalWert = dbo.tArtikelMerkmal.kMerkmalWert "
                             # get all aktive kArtikel
                             "AND dbo.tMerkmalWertSprache.cMetaKeywords = ?", value, False)

    def getSpecialPrice(self, k_article):
        return self.exec_sql("SELECT fNettoPreis, dEnde FROM [DbeS].[vArtikelSonderpreis] as sp WHERE sp.kArtikel = ?"
                             " AND sp.cAktiv = 'Y'"
                             " AND sp.dStart < GETDATE()"
                             " AND sp.kKundenGruppe = 1", k_article)

    def getArticleDescription(self, k_article):
        return self.exec_sql("SELECT cBeschreibung ,cKurzBeschreibung, cName FROM [dbo].[tArtikelBeschreibung] WHERE"
                             " dbo.tArtikelBeschreibung.kArtikel = ?", k_article)

