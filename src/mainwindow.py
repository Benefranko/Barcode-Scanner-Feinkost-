from enum import Enum
from logging import Logger

from PySide2.QtCore import QFile, QTimerEvent, Qt, QIODevice, QRect
from PySide2.QtCore import Slot
from PySide2.QtGui import QImage, QPixmap, QFontMetrics, QFont
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel, QFrame, QWidget  # , QLayout, QLayoutItem
from PySide2.QtWidgets import QMainWindow, QApplication

from databasemanager import DataBaseManager
from localdatabasemanager import LocalDataBaseManager
import settings as s

import logging
from pathlib import Path

log: Logger = logging.getLogger(Path(__file__).name)


# Klasse steuert die Grafik und managed die Datenbanken

class MainWindow(QMainWindow):
    # Attributes
    # Sekundenspeicher für rückwärts zählenden Timer für Informationsanzeige
    showTimeTimer: int = s.SHOW_TIME
    # Sekundenspeicher für rückwärts zählenden Timer für Wechsel der Warte-Anzeige
    changeAdvertiseTimer: int = s.CHANGE_ADVERTISE_TIME
    # Haupt Sekunden-Timer ID
    timerID: int = -1
    # Auf Hauptseite: Unterseite für Werbungen: Index
    advertise_page_index: int = 0
    # counter for waitingPoints
    waiting_points_counter: int = 0

    # Objects
    # DataBaseManager für MS SQL Anbindung
    databasemanager: DataBaseManager = None
    # Hauptfenster mit ganzem Userinterface
    window: QWidget = None
    # Roter Balken für Sonderpreis
    special_price_red_line = None
    # Textlabel für Sonderpreis
    special_price_label = None
    # LocalDataBaseManager für SQL Lite Anbindung zum Speichern von Statistiken
    loc_db_mngr: LocalDataBaseManager = None

    screenSize: QRect = None

    # Liste mit Werbung → muss aktualisiert werden! Entweder mit später über Web implementierter Funktion oder über
    # täglichen Reboot!
    advertise_kArtikel_list = None

    # Enum mit Objektzuständen - Warte auf Scan - Zeige Scan an
    class STATES(Enum):
        UNKNOWN = 0
        SHOW_PRODUCT_DESCRIPTION = 1
        WAIT_FOR_SCAN = 2
        SHOW_PRODUCER_INFOS = 3

    state = STATES.SHOW_PRODUCT_DESCRIPTION

    # Stoppe Sekunden Timer im Destruktor
    def cleanUp(self):
        # Stop Timer
        self.killTimer(self.timerID)
        # Clear Layouts:
        # try:
        #    self.rec_clear_layout(self.window.page_1.layout())
        #    self.rec_clear_layout(self.window.page_2.layout())
        #    self.rec_clear_layout(self.window.page_3.layout())
        #    self.rec_clear_layout(self.window.page_4.layout())
        #    self.rec_clear_layout(self.window.page_5.layout())
        #    self.rec_clear_layout(self.window.page_6.layout())

        # self.rec_clear_layout(self.window.groupBoxAdvertise.layout())
        # except Exception as e:
        #    print("Clear Layouts failed: ", e)
        #    log.warning("Clear Layouts failed: {0}".format(e))

        self.databasemanager.disconnect()
        self.loc_db_mngr.disconnect()

    # def rec_clear_layout(self, layout: QLayout):
    #     for i in reversed(range(layout.count())):
    #         item: QLayoutItem = layout.itemAt(i)
    #         if item.layout():
    #             self.rec_clear_layout(item.layout())
    #             layout.takeAt(i)
    #
    #         elif item.widget():
    #             layout.takeAt(i).widget().setParent(None)

    def __init__(self, sql_lite_path, msql_ip, msql_port, ui_file_path, parent=None):
        # Falls Fenster ein übergeordnetes Objekt erhält, übergib dieses der Basisklasse QMainWindow
        super(MainWindow, self).__init__(parent)
        ####
        # USER INTERFACE
        ####

        ###
        # Lade Grafik aus Qt-Creator UI Datei
        if self.load_ui(ui_file_path) is None:
            raise Exception("Konnte UI nicht Laden")

        # Lege Startzustand Fest und zeige dementsprechende Seite an
        self.state = self.STATES.WAIT_FOR_SCAN
        self.window.stackedWidget.setCurrentIndex(0)
        self.window.stackedWidget_advertise.setCurrentIndex(1)

        screen = 1
        self.screenSize = QApplication.desktop().screenGeometry(screen)
        self.setGeometry(self.screenSize)

        # Vollbild:
        self.showFullScreen()

        # self.setFixedSize(800, 400)
        # self.setWindowFlags(Qt.CustomizeWindowHint | Qt.FramelessWindowHint)

        # init Sonderpreis red HLine...
        self.special_price_red_line = QFrame(self.window.widget_preis)
        self.special_price_red_line.setFrameShape(QFrame.HLine)
        # self.special_price_red_line.setFixedHeight(20)
        self.special_price_red_line.setLineWidth(6)
        self.special_price_red_line.setStyleSheet("color: rgba(255, 0, 0, 150)")
        self.special_price_red_line.hide()

        # init Sonderpreis Label
        self.special_price_label = QLabel(self.window.widget_preis)
        self.special_price_label.setStyleSheet("color: rgba(255, 0, 0, 255)")
        self.special_price_label.setFont(QFont("Segoe UI", s.SPECIAL_PRICE_FONT_SIZE, QFont.Bold))
        self.special_price_label.hide()

        # MainWindow Nach-Einstellungen
        self.setWindowTitle("Feinkost Barcode Scanner")

        ###
        # Verbinde SIGNALS und SLOTS
        ###

        # Weitere Information zum Hersteller anzeigen Button wird mit Funktion clickMoreInfosHerstellerButton verbunden
        self.window.pushButton_more_infos_hersteller.clicked.connect(self.clickMoreInfosHerstellerButton)
        # Zurück von Hersteller Anzeigen Seite zu Infos-Seite wird mit Funktion verbunden
        self.window.pushButton_back_from_hersteller_page.clicked.connect(
            self.click_pushButton_back_from_hersteller_page)

        # Lade Grafiken
        # "Kein Bild gefunden"-Grafik...
        img_path: str = "../images/no_picture_found.jpg"
        pix = QPixmap(img_path)
        if pix.isNull():
            log.error("Konnte Bild nicht laden: {0}".format(img_path))
        else:
            self.window.frame.setPixmap(pix.scaled(pix.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

        # "Barcode Scanner Bild mit Handy Beispiel"-Grafik
        img_path = "../images/sunmi_scan.png"
        pix = QPixmap(img_path)
        if pix.isNull():
            log.error("Konnte Bild nicht laden: {0}".format(img_path))
        else:
            # self.window.img1.setPixmap(pix.scaled(pix.size() / 2, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            max_width = (0.9 * (self.screenSize.width() / 2))
            max_height = (0.8 * (self.screenSize.height()))
            pix = pix.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.window.img1.setPixmap(pix)

        # InnKaufHaus-Logo-Grafik
        img_path = "../images/logo.jpg"
        pix = QPixmap(img_path)
        if pix.isNull():
            log.error("Konnte Bild nicht laden: {0}".format(img_path))
        else:
            self.window.Innkaufhauslogo.setPixmap(
                pix.scaled(pix.toImage().size() / 2, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        ####
        # DATA BASES
        ####

        # Stelle Verbindung mit MS SQL Datenbank her
        self.databasemanager = DataBaseManager()
        if self.databasemanager.connect(ip=msql_ip, port=msql_port) is None:
            raise Exception("Konnte Verbindung mit dem MS SQL Server nicht herstellen")

        # Stelle Verbindung mit lokaler SQL Lite Datenbank her
        self.loc_db_mngr = LocalDataBaseManager()
        if self.loc_db_mngr.connect(sql_lite_path) is None:
            raise Exception("Konnte Verbindung mit der SQL Lite Datenbank nicht herstellen")
        else:
            try:
                self.loc_db_mngr.create_table()
                self.loc_db_mngr.updateConstants()
            except Exception as e:
                raise Exception("Das erstellen der Tabellen in der lokalen SQL Lite Datenbank ist fehlgeschlagen: {0}"
                                .format(e))

        ####
        # Lade init Data aus dem SQL Server
        ####

        # Lade Liste mit Artikeln, zu denen die Vorschau angezeigt werden soll...
        self.advertise_kArtikel_list = self.databasemanager.getAdvertiseList(s.wawi_advertise_aktive_meta_keyword)
        if self.advertise_kArtikel_list is None or len(self.advertise_kArtikel_list) < 2:
            log.warning("Not more than 1 Advertise found !")
            self.advertise_kArtikel_list = None

        log.debug("* DEBUG: LISTE MIT WERBUNG: {0}".format(self.advertise_kArtikel_list))

        ####
        # EVENTS SIGNALS SLOTS TIMER
        ####

        # Starte Sekunden Event Timer
        self.timerID = self.startTimer(1000)

    def load_ui(self, ui_path):
        try:
            # Lade UI aus einer Datei...
            ui_file = QFile(ui_path)
            if not ui_file.open(QIODevice.ReadOnly):
                log.critical(str(f"Cannot open {ui_path}: {ui_file.errorString()}"))

                return None
            loader = QUiLoader()
            self.window = loader.load(ui_file, self)
            ui_file.close()
            if not self.window:
                print(loader.errorString())
                log.critical(loader.errorString())
                return None
            else:
                return self.window
        except Exception as exc:
            log.critical("Konnte Gui aus Ui.Datei nicht laden: {0}!".format(exc))
            return None

    def timerEvent(self, event: QTimerEvent) -> None:
        # Leite jede Sekunde Event TIMER an EventHandler weiter
        self.event_handler("TIMER")

    @Slot()
    def clickMoreInfosHerstellerButton(self):
        log.debug("Weitere Informationen zum Hersteller {0} angefragt.".format(self.window.hersteller.text()))
        self.event_handler("BUTTON_MORE_PRODUCER_INFOS_CLICKED")
        return

    @Slot()
    def click_pushButton_back_from_hersteller_page(self):
        self.event_handler("BUTTON_BACK_TO_INFOS_CLICKED")
        return

    def switchArtikelPreViewPageAndStartPage(self):
        # Wenn artikel mit Merkmal für Vorschau existieren, lade neue Anzeige und wechsle zu dieser
        try:
            if s.want_reload_advertise:
                s.want_reload_advertise = False
                self.advertise_kArtikel_list = self.databasemanager.getAdvertiseList(
                    s.wawi_advertise_aktive_meta_keyword)
                log.debug("DEBUG: LISTE MIT WERBUNG: {0}".format(self.advertise_kArtikel_list))

                if self.advertise_kArtikel_list is None or len(self.advertise_kArtikel_list) < 2:
                    print("  Not more than 1 Advertise found !")
                    log.warning("  Not more than 1 Advertise found !")
                    self.advertise_kArtikel_list = None
                    return

            if self.advertise_kArtikel_list is not None and self.window.stackedWidget_advertise.currentIndex() == 1:
                if self.new_advertise() is not None:
                    self.window.stackedWidget_advertise.setCurrentIndex(0)
            else:
                # sonst zeige weiter Startseite an
                self.window.stackedWidget_advertise.setCurrentIndex(1)

        except Exception as e:
            log.error("Failed to load new Advertise: {0}".format(e))
            self.window.stackedWidget_advertise.setCurrentIndex(1)

    def new_advertise(self):
        if self.advertise_kArtikel_list is None or len(self.advertise_kArtikel_list) < 2:
            # Advertise List is Empty
            return

        for i in range(0, 2):
            # -try all indexes but if it is the second one don't try this one => reduce range by one at the second
            # -> reduce 'i' == 1... use + 1 to check if error
            for trs in range(0, len(self.advertise_kArtikel_list) + 1 - i):
                if trs == len(self.advertise_kArtikel_list) - i:
                    log.error("Error: couldn't find a ( second ) advertise, that is not invalid -> clear list")
                    self.advertise_kArtikel_list = None

                    return None
                elif trs >= 1 and self.advertise_kArtikel_list[self.advertise_page_index] is not None:
                    log.warning("    -> Entferne ungültige Werbung: {0}".
                                format(self.advertise_kArtikel_list[self.advertise_page_index]))

                    self.advertise_kArtikel_list[self.advertise_page_index] = None
                    log.debug("  NEUE LISTE MIT WERBUNG:  {0}".format(self.advertise_kArtikel_list))

                # Wähle neue aus...
                self.advertise_page_index = (self.advertise_page_index + 1) % len(self.advertise_kArtikel_list)
                if self.advertise_kArtikel_list[self.advertise_page_index] is None:
                    continue
                k_art: int = self.advertise_kArtikel_list[self.advertise_page_index].kArtikel

                data = self.databasemanager.getDataBykArtikel(k_art)
                if data is None:
                    log.error("    Failed to load data from advertise article k_artikel={0}".format(k_art))
                    continue

                descr = self.databasemanager.getArticleDescription(k_art)
                if descr is None:
                    log.error("    Failed to load article description from advertise article k_artikel={0}"
                              .format(k_art))
                    continue

                steuersatz: float = self.databasemanager.getSteuerSatz(data.kSteuerklasse)
                if steuersatz == -1:
                    log.error("    Failed to load steuersatz kSteuerklasse={0}".format(data.kSteuerklasse))
                    continue

                inhalt = self.databasemanager.getMengenPreisStr(k_art)
                if inhalt is None:
                    log.error("    Failed to load MengenPreis from advertise article k_artikel={0}".format(k_art))
                    continue

                preis: float = float(data.fVKNetto) * (steuersatz + 1.0)
                s_preis = self.databasemanager.getSpecialPrice(k_article=k_art)

                content = self.databasemanager.getFirstImageBykArtikel(data.kArtikel)
                img: QImage = QImage()
                if content is None or content.bBild is None or img.loadFromData(content.bBild) is False:
                    if content:
                        log.error("    Failed to load Image from DB! Invalid Image! (k_artikel={0})".format(k_art))
                    else:
                        log.error("    Advertise has no Image!! -> Skipp  (k_artikel={0})".format(k_art))
                    continue
                else:
                    pix = QPixmap.fromImage(img).scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    if i == 0:
                        self.window.VorschauBild1.setPixmap(pix)
                    else:
                        self.window.vorschaubild2.setPixmap(pix)

                if i == 0:
                    self.window.textEdit_previewdescription.setHtml(descr.cKurzBeschreibung)
                    self.window.Advertise_artikel_name.setText(descr.cName)
                    self.window.textEdit_previewdescription.setFont(QFont("Arial", 14))
                    self.window.textEdit_previewdescription.setAlignment(Qt.AlignCenter)
                    self.window.inhalt_preview_1.setText("Inhalt: " + inhalt)

                    self.window.preis_preview_1.setText(self.databasemanager.roundToStr(preis) + " €")
                    if s_preis is not None:
                        p: float = float(s_preis.fNettoPreis) * (steuersatz + 1.0)
                        self.window.label_s_price_1.setText(self.databasemanager.roundToStr(p) + "€ statt")
                        self.window.preis_preview_1.font().setStrikeOut(True)
                        f = self.window.preis_preview_1.font()
                        f.setStrikeOut(True)
                        self.window.preis_preview_1.setFont(f)
                    else:
                        self.window.label_s_price_1.setText("")
                        f = self.window.preis_preview_1.font()
                        f.setStrikeOut(False)
                        self.window.preis_preview_1.setFont(f)

                else:
                    self.window.textEdit_prevdescr2.setHtml(descr.cKurzBeschreibung)
                    self.window.advertise2_articel_name.setText(descr.cName)
                    self.window.textEdit_prevdescr2.setFont(QFont("Arial", 14))
                    self.window.textEdit_prevdescr2.setAlignment(Qt.AlignCenter)
                    self.window.inhalt_preview_2.setText("Inhalt: " + inhalt)

                    self.window.preis_preview_2.setText(self.databasemanager.roundToStr(preis) + " €")
                    if s_preis is not None:
                        p: float = float(s_preis.fNettoPreis) * (steuersatz + 1.0)
                        self.window.label_s_price_2.setText(self.databasemanager.roundToStr(p) + "€ statt")
                        f = self.window.preis_preview_2.font()
                        f.setStrikeOut(True)
                        self.window.preis_preview_2.setFont(f)

                    else:
                        self.window.label_s_price_2.setText("")
                        f = self.window.preis_preview_2.font()
                        f.setStrikeOut(False)
                        self.window.preis_preview_2.setFont(f)
                # skip try find 1 fitting img:
                # print("    -> use: [", k_art, "]")
                # log.debug("    -> use: [", k_art, "]" {0}".format( {0}".format()))
                break

        return "OK"

    def loadHerstellerPage(self, k_artikel: str):
        h_infos = self.databasemanager.getHerstellerInfos(k_artikel)
        if h_infos is None:
            log.warning("        Keine Hersteller Informationen für Artikel (kArtikel={0}) vorhanden".format(k_artikel))
            return None

        h_descr = self.databasemanager.getHerstellerDescription(h_infos.kHersteller)
        if h_descr is None:
            log.warning("        Failed to load HerstellerBeschreibung (kArtikel={0})".format(k_artikel))
            return None

        self.window.label_herstellername.setText(h_infos.cName)
        self.window.textEdit_hersteller_description.setHtml(h_descr.cBeschreibung)
        if h_infos.cHomepage != "":
            self.window.label_link.setText(h_infos.cHomepage)
            self.window.label_link.setStyleSheet("QLabel { color : blue; }")
            self.window.label_link.show()
            self.window.label_link_text.show()

        else:
            self.window.label_link.hide()
            self.window.label_link_text.hide()

        content = self.databasemanager.getFirstImageBykHersteller(h_infos.kHersteller)
        img = QImage()
        if content is None or content.bBild is None or img.loadFromData(content.bBild) is False:
            if content:
                log.warning("    Failed to load img from db: Invalid Img: .kHersteller={0}".format(h_infos.kHersteller))
            else:
                log.debug("    No Img for Hersteller: .kHersteller={0}".format(h_infos.kHersteller))
            self.window.hersteller_img.hide()
        else:
            # update sizes:
            self.window.stackedWidget.setCurrentIndex(0)
            self.window.stackedWidget.setCurrentIndex(1)
            self.window.stackedWidget.setCurrentIndex(0)
            self.window.stackedWidget.setCurrentIndex(3)

            p = QPixmap.fromImage(img).scaled(self.window.hersteller_img.size() / 1.3,
                                              Qt.KeepAspectRatio,
                                              Qt.SmoothTransformation)
            self.window.hersteller_img.setPixmap(p)
            self.window.hersteller_img.show()

        return h_infos.cName

    def newScanHandling(self, scan_article_ean: str):
        # Barcodescanner hat neues Scan registriert...
        # Setzte Anzeige Timer zurück und ändere Objektzustand
        self.showTimeTimer = s.SHOW_TIME
        self.state = self.STATES.SHOW_PRODUCT_DESCRIPTION

        # Versuche Informationen vom MS SQL Server zu dem Artikel abzufragen
        try:
            data = self.databasemanager.getDataByBarcode(int(scan_article_ean))
        except Exception as exc:
            log.warning("    Ungültiger Scan: Can't cast to int: {0}: {1}".format(scan_article_ean, exc))
            self.event_handler("LOAD_ARTICLE_FAILED", scan_article_ean)
            return

        if data is None:
            # Wenn keine Informationen zu dem Artikel gefunden werden kann, welche zu "nichts-gefunden"-Seite
            self.window.stackedWidget.setCurrentIndex(2)
            self.showTimeTimer = s.SHOW_TIME_NOTHING_FOUND
            return

        descript = self.databasemanager.getArticleDescription(data.kArtikel)
        if descript is None:
            log.warning("    Keine Artikelbeschreibung vorhanden! k_artikel={0}".format(data.kArtikel))
            self.event_handler("LOAD_ARTICLE_FAILED", scan_article_ean)
            return

        steuersatz: float = self.databasemanager.getSteuerSatz(data.kSteuerklasse)
        if steuersatz == -1:
            log.error("    Failed to get steuersatz kSteuerklasse={0}".format(data.kSteuerklasse))
            self.event_handler("LOAD_ARTICLE_FAILED", scan_article_ean)
            return

        # Wechsle aktuelle Seite zur Startseite, um das Layout zu aktualisieren, damit auch die Positionen der
        # Labels aktualisiert werden, um dann auch die richtige Position des Preis-Labels zu erhalten,
        # um den Sonderpreis richtig Positionieren zu können

        self.window.stackedWidget.setCurrentIndex(0)
        self.window.stackedWidget.setCurrentIndex(1)
        self.window.stackedWidget.setCurrentIndex(0)

        # Aktualisiere die Labels im User Interface mit den Werten aus der Datenbank...

        # Artikel Namen
        if descript.cName != "":
            self.window.p_name.setText(descript.cName)
            # Passe Font Size so an, dass ganzer Name angezeigt wird
            font: QFont = QFont("Areal")
            font.setPixelSize(s.PRODUCT_MAX_FONT_SIZE)
            font.setBold(True)
            font.setUnderline(True)
            while QFontMetrics(font).boundingRect(self.window.p_name.text()).width() > self.window.p_name.width():
                font.setPixelSize(font.pixelSize() - 1)
            self.window.p_name.setFont(font)
        else:
            self.event_handler("LOAD_ARTICLE_FAILED", scan_article_ean)
            log.info("    LOAD_ARTICLE_FAILED: {0} -> data.Artikelname == \"\" ".format(scan_article_ean))
            return

        # Artikel Preis
        self.window.preis.setText(
            str(self.databasemanager.roundToStr(float(data.fVKNetto) * (steuersatz + 1.0))) + " €")

        # Artikel Inhalt
        # self.window.inhalt.setText("value")

        # Artikel Hersteller
        hersteller = None
        if data.kHersteller == 0:
            log.warning("    Kein Hersteller für den Artikel k_artikel={0} vorhanden!".format(data.kArtikel))
        else:
            hersteller = self.databasemanager.getHerstellerInfos(k_article=data.kArtikel)

        if hersteller is None or hersteller.cName == "":
            self.window.hersteller.hide()
            self.window.hersteller_label.hide()

            self.window.pushButton_more_infos_hersteller.hide()
        else:
            self.window.hersteller.setText(hersteller.cName)
            self.window.hersteller.show()
            self.window.hersteller_label.show()
            # Lade Hersteller seite
            if self.loadHerstellerPage(data.kArtikel) is not None:
                self.window.pushButton_more_infos_hersteller.show()
            else:
                self.window.pushButton_more_infos_hersteller.hide()

        # Artikel Beschreibung - diese muss aus extra Datenbank geladen werden
        if descript is None or descript.cBeschreibung == "" \
                or descript.cKurzBeschreibung is None or descript.cKurzBeschreibung == "":
            self.window.groupBox_beschreibung.setTitle("")
            self.window.description.setHtml("")
        else:
            self.window.description.setHtml(descript.cBeschreibung)
            if len(descript.cKurzBeschreibung) > s.MAX_SHORT_DESCRIPTION_LENGTH:
                self.window.groupBox_beschreibung.setTitle("Produktinformationen:")
            else:
                self.window.groupBox_beschreibung.setTitle("Produktinformationen: \"{0}\""
                                                           .format(descript.cKurzBeschreibung))

        self.window.stackedWidget.setCurrentIndex(1)
        self.window.stackedWidget.setCurrentIndex(0)

        # Lade Grafik aus MS SQL Datenbank zu dem Artikel
        # Verwende dazu das erste vorhandene Bild, das es gibt
        content = self.databasemanager.getFirstImageBykArtikel(data.kArtikel)
        img = QImage()

        if content is None or content.bBild is None or img.loadFromData(content.bBild) is False:
            if content:
                log.warning("    Failed to load img from db: Invalid Img: k=artikel={0}".format(data.kArtikel))
            # self.window.img.setPixmap(
            #     QPixmap("../images/kein-bild-vorhanden.webp").scaled(self.window.img.size() / 1.5, Qt.KeepAspectRatio,
            #                                                          Qt.SmoothTransformation))
            self.window.img.hide()
        else:
            p = QPixmap.fromImage(img).scaled(self.window.img.size() / 1.3, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.window.img.setPixmap(p)
            self.window.img.show()

        # Erneuter Seitenwechsel, um Layout-update zu erzwingen
        self.window.stackedWidget.setCurrentIndex(1)

        # Überprüfe, ob ein Sonderangebot im Moment vorliegt
        special_price = self.databasemanager.getSpecialPrice(data.kArtikel)
        # wenn ja:
        if special_price is not None:
            # Mach Sonderangebots-Label sichtbar:
            self.special_price_label.show()
            self.special_price_red_line.show()

            # Aktualisiere Sonderpreis-Label mit auf 2-Stellen gerundetem Sonderpreis in €
            self.special_price_label.setText(self.databasemanager.roundToStr(float(special_price.fNettoPreis)
                                                                             * (steuersatz + 1.0)) + " €")

            # Berechne Position der "Streich Linie":
            # Breite des Normal-Preis-Textes (Abhängig von Schriftart und Größe)
            br_price = QFontMetrics(self.window.preis.font()).boundingRect(self.window.preis.text())
            # Breite des Sonder-Preis-Text-Labels
            br_special_price = QFontMetrics(self.special_price_label.font()). \
                boundingRect(self.special_price_label.text())

            # Lege Position der roten Streichlinie fest: x = normal_preis.x
            #                                            y = normal_preis.y + ( 0.5 * normal_preis.höhe )
            #                                       breite = sonder_preis.breite
            #                                       höhe   = KONSTANT: SPECIAL_PRICE_RED_LINE_HEIGHT
            self.special_price_red_line.setGeometry(self.window.preis.x() - 5,
                                                    self.window.preis.y() + 0.5 * self.window.preis.height(),
                                                    br_price.width() + 10,
                                                    s.SPECIAL_PRICE_RED_LINE_HEIGHT)
            # Lege Position des Streichpreises fest:    x = normal_preis.x + normal_preis.breite + KONSTANT: Abstand
            #                                      y = normal_preis.y - ( sonder_preis.höhe - 0.5 * normal_preis.höhe )
            #                                      breite = sonder_preis.breite + 2
            #                                      höhe   = sonder_preis.höhe
            self.special_price_label.setGeometry(self.window.preis.x() + br_price.width()
                                                 + s.SPACE_BETWEEN_PRICE_AND_SPECIAL_PRICE,
                                                 self.window.preis.y() - int((float(br_special_price.height()) * 0.5
                                                                              - 0.5 * float(br_price.height()))),
                                                 br_special_price.width() + 2,
                                                 br_special_price.height())

        # Wenn kein Sonderpreis vorliegt:
        else:
            # Verstecke Sonderpreis Label und Linie
            self.special_price_label.hide()
            self.special_price_red_line.hide()

        mengen_preis_line = self.databasemanager.getMengenPreisStr(k_article=data.kArtikel)
        if mengen_preis_line is not None:
            self.window.inhalt.setText(mengen_preis_line)
            self.window.inhalt.show()
            self.window.label_inhalt.show()
        else:
            # self.window.inhalt.hide()
            # self.window.label_inhalt.hide()
            self.event_handler("LOAD_ARTICLE_FAILED", scan_article_ean)
            return None

        lagerbestand = self.databasemanager.getLagerBestand(data.kArtikel)
        if lagerbestand == -1:
            self.window.label_lagerbstand_value.hide()
            self.window.label_lagerbstand_text.hide()
        else:
            if lagerbestand == 0:
                self.window.label_lagerbstand_value.setText("Ausverkauft. Bald wieder verfügbar!")
            else:
                self.window.label_lagerbstand_value.setText(str(lagerbestand) + " Stück")
            self.window.label_lagerbstand_text.show()
            self.window.label_lagerbstand_value.show()

        # Füge den Scan der lokalen Statistiken-Datenbank hinzu:
        try:
            self.loc_db_mngr.add_new_scan(data.kArtikel, scan_article_ean)
        except Exception as e:
            log.error("    Error: Das speichern des Scans für Statistiken ist fehlgeschlagen: {0}".format(e))
        return

    # Eventhandler: Je nach Objektzustand führe die übergebenen Aktionen aus
    def event_handler(self, action, value=None):
        try:

            # Speichere, falls Aktion nicht ausgeführt wurde (für Debug Nachrichten)
            # für Aktionen, die mehrere If-Statements "erreichen" können, wo kein return am Ende vorliegt.
            # Wenn diese Funktion in keinem If-Statement an ein return gelangt, wird Warnung ausgegeben
            handled: bool = False

            # Zustands unabhängige Aktionen:

            if self.state != self.STATES.UNKNOWN:
                # Es wurde ein Barcode gescannt-> Ermittle Informationen und zeige diese an
                if action == "NEW_SCAN":
                    self.newScanHandling(value)
                    handled = True
                elif action == "TIMER":
                    self.waiting_points_counter = (self.waiting_points_counter + 1) % 4
                    self.window.label_waiting_for_scan.setText("Warten auf Scan" + self.waiting_points_counter * ".")

            # Zustands spezifische Aktionen:
            # Zustand: Warte für Barcode Scan:
            if self.state == self.STATES.WAIT_FOR_SCAN:

                # Timer wurde erreicht-> Wechsle die Warte-Auf-Eingabe Seite, bzw zeige neue Werbung an
                if action == "CHANGE_ADVERTISE":
                    self.switchArtikelPreViewPageAndStartPage()
                    return
                # (jede Sekunde) Sekunden-Timer-Event
                elif action == "TIMER":
                    # wenn Timer_MAX erreicht wurde, führe Aktion CHANGE_ADVERTISE aus, sonst timer--
                    if self.changeAdvertiseTimer > 1:
                        self.changeAdvertiseTimer -= 1
                    else:
                        self.changeAdvertiseTimer = s.CHANGE_ADVERTISE_TIME
                        self.event_handler("CHANGE_ADVERTISE")
                    return

            # Zustand: Zeige Produktinformationen:
            elif self.state == self.STATES.SHOW_PRODUCT_DESCRIPTION:
                if action == "EXIT_SHOW_DESCRIPTION":
                    self.window.stackedWidget.setCurrentIndex(0)
                    self.state = self.STATES.WAIT_FOR_SCAN
                    return

                elif action == "LOAD_ARTICLE_FAILED":
                    self.window.stackedWidget.setCurrentIndex(2)
                    self.showTimeTimer = s.SHOW_TIME_NOTHING_FOUND
                    return
                elif action == "BUTTON_MORE_PRODUCER_INFOS_CLICKED":
                    # Setzte Zeit auf Maximalwert zurück: auf SHOW_PRODUCER_INFOS_TIME Anzeigezeit
                    self.showTimeTimer = s.SHOW_PRODUCER_INFOS_TIME
                    self.state = self.STATES.SHOW_PRODUCER_INFOS
                    self.window.stackedWidget.setCurrentIndex(3)
                    return

                # (jede Sekunde) Sekunden-Timer-Event
                elif action == "TIMER":
                    # Wenn Anzeige-Zeit erreicht wurde, wechsle wieder auf Startseite / Objektzustand-"Warte auf Scan"
                    if self.showTimeTimer > 1:
                        self.showTimeTimer -= 1
                    else:
                        self.showTimeTimer = s.SHOW_TIME
                        self.event_handler("EXIT_SHOW_DESCRIPTION")
                    return
                # Wenn während Informationsanzeige ein neues Produkt gescannt wird,
                # aktualisiere die Anzeige und resette den Timer

            # Wenn gerade Information zu einem Hersteller angezeigt werden
            elif self.state == self.STATES.SHOW_PRODUCER_INFOS:
                # Wenn die Anzeige Zeit ausläuft und action exit aufgerufen wird
                if action == "EXIT_SHOW_DESCRIPTION":
                    self.window.stackedWidget.setCurrentIndex(0)
                    self.state = self.STATES.WAIT_FOR_SCAN
                    return

                # Wenn der zurück Button gedrückt wird
                elif action == "BUTTON_BACK_TO_INFOS_CLICKED":
                    self.showTimeTimer = s.SHOW_TIME
                    self.state = self.STATES.SHOW_PRODUCT_DESCRIPTION
                    self.window.stackedWidget.setCurrentIndex(1)
                    return

                # (jede Sekunde) Sekunden-Timer-Event
                elif action == "TIMER":
                    # Wenn Anzeige-Zeit erreicht wurde, wechsle wieder auf Startseite / Objektzustand-"Warte auf Scan"
                    if self.showTimeTimer > 1:
                        self.showTimeTimer -= 1
                    else:
                        self.showTimeTimer = s.SHOW_TIME
                        self.event_handler("EXIT_SHOW_DESCRIPTION")
                    return

            # Wenn ein Unbekannter Objektzustand vorliegt, wirf Exception
            else:
                raise Exception("Unbekannter Objektzustand: ")

            if not handled:
                log.warning("Die Aktion {0} wurde nicht bearbeitet!".format(action))

        except Exception as e:
            log.error("Handle Event ({0})[{1}] failed: [{2}]".format(action, value, e))

    # Funktion (Slot), die mit dem Signal aus MApplication verbunden ist, und bei einem Scan aufgerufen wird
    @Slot(str)
    def new_scan(self, value):
        # Gib den Scan dem Event-Handler weiter...
        log.debug("Neuen Barcode Scan erhalten: {0}".format(value))
        self.event_handler("NEW_SCAN", value)


