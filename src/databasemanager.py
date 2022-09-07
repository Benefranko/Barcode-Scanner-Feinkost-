# Open Source Bibliothek für MS SQL
import pyodbc
import constants as consts
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
                    log.debug("Verwende Driver: ODBC Driver 18 for SQL Server...")

                    self.conn = pyodbc.connect(driver=consts.SQL_DRIVER_USED_VERSION_MS_DRIVER,
                                               server=ip + "," + str(port),
                                               database=db,
                                               user=usr,
                                               password=pw,
                                               encrypt="no")
                    log.info("  -> Erfolgreich mit MS SQL Server verbunden über ODBC Driver 18")

                    break

                elif "FreeTDS" in driver_names:
                    log.debug("Verwende Driver: FreeTDS {0} ...".format(consts.SQL_DRIVER_USED_VERSION_FreeTDS_VERSION))

                    self.conn = pyodbc.connect('DRIVER={0}; SERVER={1}; PORT={2}; DATABASE={3}; UID={4}; PWD={5}; '
                                               'TDS_Version={6};'.format(consts.SQL_DRIVER_USED_VERSION_FreeTDS,
                                                                         ip, port, db, usr, pw,
                                                                         consts.SQL_DRIVER_USED_VERSION_FreeTDS_VERSION)
                                               )
                    log.info("Erfolgreich mit MS SQL Server verbunden über FreeTDS Driver {0} ".format(
                        consts.SQL_DRIVER_USED_VERSION_FreeTDS_VERSION))
                    break
                else:
                    log.critical('Error: No suitable driver found. Cannot connect.')
                    log.debug("All installed driver: {0}".format(pyodbc.drivers()))
                    self.conn = None
                    break
            except Exception as exc:
                log.warning('Connect to Database failed. ( Try: {0}/10 ) Error: {1} - Warte 1 Sekunde...'
                            .format(i + 1, exc))

                time.sleep(1)
                self.conn = None

        return self.conn

    def exec_sql(self, sql, value, fetch_one: bool = True):
        # log.debug("        exec_sql MS SQL DATABASE: {0} ARGS: {1} FETCHONE: {2}".format(sql, value, fetch_one))
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
            log.error('        exec_sql failed ({0})[{1}]: {2}'.format(sql, value, exc))
            return None

    # AUF FEHLER NOCH CHECKEN !!
    def getSteuerSatz(self, steuerklasse) -> float:
        steuersatz = self.exec_sql('SELECT fSteuersatz FROM [Mandant_1].[dbo].[tSteuersatz]'
                                   ' WHERE fSteuersatz != 0.0 AND kSteuerklasse = ?', steuerklasse, True)
        if steuersatz:
            return float(steuersatz.fSteuersatz) / 100.0
        else:
            log.error('        getSteuerSatz failed!')
            return -1.0

    def getDataByBarcode(self, c_barcode):
        return self.exec_sql("SELECT * FROM dbo.tArtikel WHERE cBarcode = ?", c_barcode, True)

    def getDataBykArtikel(self, k_artikel):
        return self.exec_sql("SELECT * FROM dbo.tArtikel WHERE kArtikel = ?", k_artikel, True)

    def getFirstImageBykArtikel(self, k_article):
        return self.exec_sql(" SELECT dbo.tBild.bBild"
                             " FROM dbo.tBild, dbo.tArtikelbildPlattform"
                             " WHERE dbo.tArtikelbildPlattform.kBild = dbo.tBild.kBild"
                             " AND dbo.tArtikelbildPlattform.kPlattform = 1"
                             " AND dbo.tArtikelbildPlattform.kArtikel = ?", k_article, True)

    def getFirstImageBykHersteller(self, k_hersteller):
        return self.exec_sql(" SELECT dbo.tBild.bBild"
                             " FROM dbo.tBild, dbo.[tHerstellerBildPlattform]"
                             " WHERE dbo.tHerstellerBildPlattform.kBild = dbo.tBild.kBild"
                             " AND dbo.tHerstellerBildPlattform.kPlattform = 1"
                             " AND dbo.tHerstellerBildPlattform.kHersteller = ?", k_hersteller, True)

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
            log.warning("        Kein Eintrag zu dem k_artikel: {0} gefunden.".format(k_article))
            return None

            # Get Mengeneinheit
        if data.kMassEinheit == 0:
            log.warning("        (!) kMassEinheit nicht festgelegt: k_artikel: {0}. -> Kann keinen Grundpreis erzeugen".
                        format(k_article))
            return None
        mass_table_article = self.exec_sql("SELECT * FROM dbo.tMassEinheit WHERE kMassEinheit = ?", data.kMassEinheit)
        if mass_table_article is None:
            log.warning("        (!) dbo.tMassEinheit für .kMassEinheit bei k_artikel: {0} nicht gefunden. "
                        "-> Kann keinen Grundpreis erzeugen".
                        format(k_article))
            return None

        mass_table_einheit = self.exec_sql("SELECT * FROM dbo.tMassEinheit WHERE kMassEinheit = ?",
                                           data.kGrundPreisEinheit)
        if mass_table_einheit is None:
            log.warning("        (!) dbo.tMassEinheit für .kGrundPreisEinheit bei k_artikel: {0} nicht gefunden. "
                        "-> Kann keinen Grundpreis erzeugen".
                        format(k_article))
            return None

            # Einheiten Namen
        article_einheit = self.exec_sql("SELECT * FROM dbo.tMassEinheitSprache WHERE kMassEinheit = ?",
                                        data.kMassEinheit)
        if article_einheit is None:
            log.warning("        (!) dbo.tMassEinheitSprache für .kMassEinheit bei k_artikel: {0} nicht gefunden. "
                        "-> Kann keinen Grundpreis erzeugen".
                        format(k_article))
            return None

        steuersatz = self.getSteuerSatz(data.kSteuerklasse)
        if steuersatz == -1:
            log.warning("        (!) getSteuerSatz() ist fehlgeschlagen für: k_artikel: {0}. "
                        "-> Kann keinen Grundpreis erzeugen".
                        format(k_article))
            return None

        grundpreis_einheit = self.exec_sql("SELECT * FROM dbo.tMassEinheitSprache WHERE kMassEinheit = ?",
                                           data.kGrundPreisEinheit)
        if grundpreis_einheit is None:
            log.warning("        (!) dbo.tMassEinheitSprache für data.kGrundPreisEinheit bei: k_artikel: {0}"
                        " nicht gefunden. -> Kann keinen Grundpreis erzeugen".
                        format(k_article))
            return None

        # Prevent div by 0
        if data.fMassMenge == 0:
            log.warning("        (!) Error: data.fMassMenge == 0 bei: k_artikel: {0}. "
                        "-> Kann keinen Grundpreis erzeugen".
                        format(k_article))
            return None
        if data.fGrundpreisMenge == 0:
            log.warning("        (!) Error: data.fGrundpreisMenge == 0 bei: k_artikel: {0}. "
                        "-> Kann keinen Grundpreis erzeugen".
                        format(k_article))
            return None

        # Wenn der Artikel in der Nenner Einheit gegeben ist → In Tabelle 0 → Zum Rechnen 1 benötigt!
        mass_bezugs_faktor = mass_table_einheit.fBezugsMassEinheitFaktor
        if mass_bezugs_faktor == 0:
            mass_bezugs_faktor = 1

        article_bezugs_faktor = mass_table_article.fBezugsMassEinheitFaktor
        if article_bezugs_faktor == 0:
            article_bezugs_faktor = 1

        einheiten_multiplikator: float = float(mass_bezugs_faktor / article_bezugs_faktor)
        mengen_multiplikator: float = float(data.fGrundpreisMenge / data.fMassMenge)

        preis = float(data.fVKNetto)
        s_price = self.getSpecialPrice(k_article)
        if s_price is not None:
            preis = float(s_price.fNettoPreis)

        mengen_preis: float = float(preis * einheiten_multiplikator * mengen_multiplikator * (1.0 + steuersatz))

        return self.roundToStr(float(data.fMassMenge)) + " " + article_einheit.cName + " (" + \
                                                         self.roundToStr(mengen_preis) + " € / " +\
                                                         self.roundToStr(float(data.fGrundpreisMenge)) + " " + \
                                                         grundpreis_einheit.cName + ")"

    def getAdvertiseList(self, value):
        return self.exec_sql("SELECT dbo.tArtikel.kArtikel"
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

    def getLagerBestand(self, k_article) -> int:
        bestand = self.exec_sql("SELECT fLagerbestand FROM [dbo].[tlagerbestand] WHERE kArtikel = ?", k_article)
        if bestand is None:
            return -1
        else:
            return int(bestand.fLagerbestand)

    def getKategorieByKArtikel(self, k_article):
        return self.exec_sql("SELECT [tKategorieSprache].cName"
                             " FROM [Mandant_1].[dbo].[tkategorieartikel], [Mandant_1].[dbo].[tKategorieSprache]"
                             " WHERE [tkategorieartikel].kArtikel = ?"
                             " AND [tkategorieartikel].kKategorie = [tKategorieSprache].kKategorie", k_article)
